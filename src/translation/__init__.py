"""
Translation Module

Provides unified interface for document translation using different providers.
"""

from typing import Dict, Any
from src.translation.base_translator import BaseTranslator
from src.translation.translator_factory import TranslatorFactory


def get_translator(config: Dict[str, Any]) -> BaseTranslator:
    """
    Get a translator instance based on configuration.

    Args:
        config: Configuration dictionary containing translation settings

    Returns:
        Translator instance (GoogleDocTranslator or GoogleTextTranslator)
    """
    factory = TranslatorFactory()
    return factory.get_translator(config)


__all__ = ['BaseTranslator', 'TranslatorFactory', 'get_translator']
