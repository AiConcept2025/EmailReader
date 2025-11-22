"""
OCR Provider Factory

Factory class for creating OCR provider instances based on configuration.
"""

from typing import Dict, Any
import logging

from src.ocr.base_provider import BaseOCRProvider

logger = logging.getLogger('EmailReader.OCR')


class OCRProviderFactory:
    """
    Factory for creating OCR provider instances.

    Supports multiple OCR providers: Azure Document Intelligence,
    LandingAI, and default (Tesseract).
    """

    VALID_PROVIDERS = {'azure', 'landing_ai', 'default'}

    @staticmethod
    def get_provider(config: Dict[str, Any]) -> BaseOCRProvider:
        """
        Create an OCR provider instance based on configuration.

        Args:
            config: Application configuration dictionary

        Returns:
            BaseOCRProvider instance

        Raises:
            ValueError: If provider type is invalid or not configured
        """
        ocr_config = config.get('ocr', {})
        provider_type = ocr_config.get('provider', 'default')

        logger.info("Creating OCR provider: %s", provider_type)

        if provider_type not in OCRProviderFactory.VALID_PROVIDERS:
            raise ValueError(
                f"Invalid OCR provider: {provider_type}. "
                f"Valid providers: {OCRProviderFactory.VALID_PROVIDERS}"
            )

        if provider_type == 'azure':
            azure_config = ocr_config.get('azure', {})
            if not azure_config.get('endpoint') or not azure_config.get('api_key'):
                raise ValueError(
                    "Azure OCR provider requires 'endpoint' and 'api_key' in configuration"
                )
            from src.ocr.azure_provider import AzureOCRProvider
            # Pass full config to provider so it can access preprocessing settings
            azure_config['preprocessing'] = config.get('preprocessing', {})
            return AzureOCRProvider(azure_config)

        elif provider_type == 'landing_ai':
            landing_ai_config = ocr_config.get('landing_ai', {})
            if not landing_ai_config.get('api_key'):
                raise ValueError(
                    "LandingAI OCR provider requires 'api_key' in configuration"
                )
            from src.ocr.landing_ai_provider import LandingAIOCRProvider
            return LandingAIOCRProvider(landing_ai_config)

        else:  # default
            default_config = ocr_config.get('default', {})
            from src.ocr.default_provider import DefaultOCRProvider
            return DefaultOCRProvider(default_config)
