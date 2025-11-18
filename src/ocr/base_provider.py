"""
Base OCR Provider Interface

Defines the abstract interface that all OCR providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger('EmailReader.OCR')


class BaseOCRProvider(ABC):
    """
    Abstract base class for OCR providers.

    All OCR providers must implement these methods to ensure
    consistent behavior across different services.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OCR provider with configuration.

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        logger.debug("Initialized %s with config keys: %s",
                    self.__class__.__name__, list(config.keys()))

    @abstractmethod
    def process_document(self, input_path: str, output_path: str) -> None:
        """
        Process a document with OCR and save the result.

        Args:
            input_path: Path to input file (PDF or image)
            output_path: Path to save output DOCX file

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If OCR processing fails
        """
        pass

    @abstractmethod
    def is_pdf_searchable(self, pdf_path: str) -> bool:
        """
        Check if a PDF contains searchable text.

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF has extractable text, False otherwise
        """
        pass
