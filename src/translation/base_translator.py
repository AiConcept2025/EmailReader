"""
Base Translator Interface

Defines the abstract interface that all translation providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger('EmailReader.Translation')


class BaseTranslator(ABC):
    """
    Abstract base class for translation providers.

    All translation providers must implement these methods to ensure
    consistent behavior across different services.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the translator with configuration.

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        logger.debug("Initialized %s with config keys: %s",
                    self.__class__.__name__, list(config.keys()))

    @abstractmethod
    def translate_document(
        self,
        input_path: str,
        output_path: str,
        target_lang: str = 'en'
    ) -> None:
        """
        Translate a document and save the result.

        Args:
            input_path: Path to input document (DOCX)
            output_path: Path to save translated document (DOCX)
            target_lang: Target language code (e.g., 'en', 'fr', 'es')

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If translation fails
        """
        pass
