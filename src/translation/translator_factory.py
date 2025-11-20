"""
Translator Factory

Factory class for creating translator instances based on configuration.
"""

from typing import Dict, Any
import logging

from src.translation.base_translator import BaseTranslator

logger = logging.getLogger('EmailReader.Translation')


class TranslatorFactory:
    """
    Factory for creating translator instances.

    Supports Google Cloud Translation API v3 (google_doc provider).
    """

    VALID_PROVIDERS = {'google_doc'}

    @staticmethod
    def get_translator(config: Dict[str, Any]) -> BaseTranslator:
        """
        Create a translator instance based on configuration.

        Args:
            config: Application configuration dictionary

        Returns:
            BaseTranslator instance

        Raises:
            ValueError: If provider type is invalid or not configured
        """
        translation_config = config.get('translation', {})
        provider_type = translation_config.get('provider', 'google_doc')

        logger.info("Creating translator: %s", provider_type)

        if provider_type not in TranslatorFactory.VALID_PROVIDERS:
            raise ValueError(
                f"Invalid translation provider: {provider_type}. "
                f"Valid providers: {TranslatorFactory.VALID_PROVIDERS}"
            )

        if provider_type == 'google_doc':
            # Google Cloud Translation API v3
            google_doc_config = translation_config.get('google_doc', {})
            if not google_doc_config.get('project_id'):
                raise ValueError(
                    "Google Document Translation requires 'project_id' in configuration"
                )

            # Pass service account credentials from google_drive section
            service_account = config.get('google_drive', {}).get('service_account')
            if service_account:
                google_doc_config['service_account'] = service_account
                logger.debug("Added service account credentials to translation config")

            from src.translation.google_doc_translator import GoogleDocTranslator
            return GoogleDocTranslator(google_doc_config)

        raise ValueError(f"Unknown translation provider: {provider_type}")
