"""
Base Translator Interface

Defines the abstract interface that all translation providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
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
        source_lang: str | None = None,
        target_lang: str = 'en'
    ) -> None:
        """
        Translate a document and save the result.

        Args:
            input_path: Path to input document (DOCX)
            output_path: Path to save translated document (DOCX)
            source_lang: Source language code (e.g., 'ru', 'es') or None for auto-detect
            target_lang: Target language code (e.g., 'en', 'fr', 'es')

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If translation fails
        """
        pass

    @abstractmethod
    def translate_document_paragraphs(
        self,
        input_path: str,
        output_path: str,
        source_lang: str = None,
        target_lang: str = 'en'
    ) -> str:
        """
        Translate document using paragraph-based approach.

        This method provides better quality control by:
        1. Extracting paragraphs from the document
        2. Translating each paragraph individually or in batches
        3. Reconstructing the document with translated paragraphs

        Args:
            input_path: Path to input document (DOCX)
            output_path: Path to save translated document (DOCX)
            source_lang: Source language code (e.g., 'ru', 'es') or None for auto-detect
            target_lang: Target language code (default: 'en')

        Returns:
            Path to output file

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If translation fails
        """
        pass

    @abstractmethod
    def translate_paragraphs(
        self,
        paragraphs: List[str],
        target_lang: str,
        source_lang: str | None = None,
        batch_size: int = 15,
        preserve_formatting: bool = True
    ) -> List[str]:
        """
        Translate a list of paragraphs in batches.

        Args:
            paragraphs: List of paragraph text strings to translate
            target_lang: Target language code (e.g., 'en', 'es', 'fr')
            source_lang: Source language code or None for auto-detect
            batch_size: Number of paragraphs to process per API call
            preserve_formatting: Maintain paragraph boundaries

        Returns:
            List of translated paragraph strings in the same order as input

        Raises:
            ValueError: If paragraphs is empty or target_lang is invalid
            RuntimeError: If translation fails
        """
        pass
