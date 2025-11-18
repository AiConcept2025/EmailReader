"""
Translation Module

Provides unified interface for document translation using different providers.
"""

from src.translation.base_translator import BaseTranslator
from src.translation.translator_factory import TranslatorFactory

__all__ = ['BaseTranslator', 'TranslatorFactory']
