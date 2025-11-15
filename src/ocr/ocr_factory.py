"""
OCR Provider Factory

This module provides a factory for creating OCR provider instances based on
configuration. It handles provider selection, validation, and fallback logic.
"""

import logging
from typing import Dict, Any

from .base_provider import BaseOCRProvider
from .default_provider import DefaultOCRProvider
from .landing_ai_provider import LandingAIOCRProvider

# Get logger for this module
logger = logging.getLogger('EmailReader.OCR.Factory')


class OCRProviderFactory:
    """
    Factory for creating OCR provider instances.

    This factory handles the creation of OCR providers based on application
    configuration. It supports multiple provider types and implements intelligent
    fallback behavior when required configuration is missing.

    Supported Providers:
        - 'default': DefaultOCRProvider (Tesseract OCR)
        - 'landing_ai': LandingAIOCRProvider (LandingAI Vision API)

    Configuration Format:
        {
            'ocr': {
                'provider': 'default',  # or 'landing_ai'
                'landing_ai': {
                    'api_key': 'your-api-key',
                    'base_url': 'https://api.va.landing.ai/v1',
                    'model': 'dpt-2-latest'
                }
            }
        }
    """

    # Valid provider types
    VALID_PROVIDERS = {'default', 'landing_ai'}

    @staticmethod
    def get_provider(config: Dict[str, Any]) -> BaseOCRProvider:
        """
        Get OCR provider based on configuration.

        Creates and returns an OCR provider instance based on the 'ocr.provider'
        configuration value. If LandingAI is requested but the API key is missing,
        automatically falls back to the default Tesseract provider.

        Args:
            config: Full application configuration dictionary. Should contain
                   an 'ocr' key with provider configuration. Structure:
                   {
                       'ocr': {
                           'provider': 'default' | 'landing_ai',
                           'landing_ai': {
                               'api_key': str,
                               'base_url': str (optional),
                               'model': str (optional)
                           }
                       }
                   }

        Returns:
            OCR provider instance implementing BaseOCRProvider interface

        Raises:
            ValueError: If provider type is invalid (not in VALID_PROVIDERS)

        Examples:
            >>> # Using default Tesseract provider
            >>> config = {'ocr': {'provider': 'default'}}
            >>> provider = OCRProviderFactory.get_provider(config)
            >>> isinstance(provider, DefaultOCRProvider)
            True

            >>> # Using LandingAI provider
            >>> config = {
            ...     'ocr': {
            ...         'provider': 'landing_ai',
            ...         'landing_ai': {'api_key': 'land_sk_...'}
            ...     }
            ... }
            >>> provider = OCRProviderFactory.get_provider(config)
            >>> isinstance(provider, LandingAIOCRProvider)
            True

            >>> # Invalid provider
            >>> config = {'ocr': {'provider': 'invalid'}}
            >>> OCRProviderFactory.get_provider(config)
            ValueError: Unknown OCR provider: invalid
        """
        # Extract OCR configuration
        ocr_config = config.get('ocr', {})
        provider_type = ocr_config.get('provider', 'default').lower()

        logger.info(f"Creating OCR provider: {provider_type}")
        logger.debug(f"OCR configuration: {ocr_config}")

        # Validate provider type
        if provider_type not in OCRProviderFactory.VALID_PROVIDERS:
            error_msg = (
                f"Unknown OCR provider: {provider_type}. "
                f"Valid options: {', '.join(sorted(OCRProviderFactory.VALID_PROVIDERS))}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Create provider based on type
        if provider_type == 'landing_ai':
            landing_ai_config = ocr_config.get('landing_ai', {})

            # Check if API key is configured
            if not landing_ai_config.get('api_key'):
                logger.warning(
                    "LandingAI provider requested but API key not found in config. "
                    "Falling back to default Tesseract provider."
                )
                logger.info("To use LandingAI, add 'ocr.landing_ai.api_key' to configuration")
                return DefaultOCRProvider(ocr_config)

            logger.info("Creating LandingAI OCR provider")
            logger.debug(f"LandingAI config: base_url={landing_ai_config.get('base_url')}, "
                        f"model={landing_ai_config.get('model', 'dpt-2-latest')}")
            return LandingAIOCRProvider(landing_ai_config)

        elif provider_type == 'default':
            logger.info("Creating default Tesseract OCR provider")
            return DefaultOCRProvider(ocr_config)

        # This should never be reached due to earlier validation
        else:
            # Defensive programming - should be caught by validation above
            logger.error(f"Unexpected provider type after validation: {provider_type}")
            raise ValueError(f"Provider type validation failed: {provider_type}")

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """
        Validate OCR configuration structure.

        Checks if the provided configuration has the correct structure and
        required fields for the specified provider type.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if configuration is valid, False otherwise

        Note:
            This is a utility method for configuration validation before
            attempting to create a provider.

        Example:
            >>> config = {'ocr': {'provider': 'default'}}
            >>> OCRProviderFactory.validate_config(config)
            True

            >>> config = {'ocr': {'provider': 'invalid'}}
            >>> OCRProviderFactory.validate_config(config)
            False
        """
        try:
            # Check if ocr section exists
            if 'ocr' not in config:
                logger.warning("OCR configuration section missing")
                return False

            ocr_config = config['ocr']
            provider_type = ocr_config.get('provider', 'default').lower()

            # Check if provider type is valid
            if provider_type not in OCRProviderFactory.VALID_PROVIDERS:
                logger.warning(f"Invalid provider type: {provider_type}")
                return False

            # Additional validation for LandingAI
            if provider_type == 'landing_ai':
                landing_ai_config = ocr_config.get('landing_ai', {})
                if not landing_ai_config.get('api_key'):
                    logger.warning("LandingAI provider missing API key")
                    return False

            logger.debug(f"Configuration validated successfully for provider: {provider_type}")
            return True

        except Exception as e:
            logger.error(f"Error validating configuration: {e}", exc_info=True)
            return False
