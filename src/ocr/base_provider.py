"""
Abstract Base Class for OCR Providers

This module defines the interface that all OCR providers must implement.
It ensures consistent behavior across different OCR engines.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseOCRProvider(ABC):
    """
    Abstract base class for OCR providers.

    All OCR provider implementations must inherit from this class and implement
    the required abstract methods. This ensures a consistent interface for OCR
    operations regardless of the underlying OCR engine.

    Attributes:
        config (dict): Provider-specific configuration dictionary
    """

    @abstractmethod
    def process_document(self, ocr_file: str, out_doc_file_path: str) -> None:
        """
        Process a document with OCR and save as DOCX.

        This method performs OCR on the input file (PDF or image) and saves
        the extracted text as a formatted DOCX document.

        Args:
            ocr_file: Path to input file (PDF or image format)
            out_doc_file_path: Path where DOCX output should be saved

        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If file format is invalid or unsupported
            RuntimeError: If OCR processing fails for any reason

        Example:
            >>> provider = OCRProviderFactory.get_provider(config)
            >>> provider.process_document('scanned.pdf', 'output.docx')
        """
        pass

    @abstractmethod
    def is_pdf_searchable(self, pdf_path: str) -> bool:
        """
        Check if PDF contains searchable text.

        Determines whether a PDF document contains extractable text (searchable)
        or is image-based and requires OCR processing.

        Args:
            pdf_path: Path to PDF file to check

        Returns:
            True if PDF has extractable text content, False if image-based

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If file is not a valid PDF format
            RuntimeError: If PDF cannot be read or processed

        Example:
            >>> provider = OCRProviderFactory.get_provider(config)
            >>> if not provider.is_pdf_searchable('document.pdf'):
            ...     provider.process_document('document.pdf', 'output.docx')
        """
        pass
