"""
Default OCR Provider using Tesseract

This provider wraps the existing Tesseract OCR functionality from pdf_image_ocr.py
and provides it through the standard OCR provider interface.
"""

import logging
from typing import Dict, Any

from .base_provider import BaseOCRProvider
from src.pdf_image_ocr import ocr_pdf_image_to_doc, is_pdf_searchable_pypdf

# Get logger for this module
logger = logging.getLogger('EmailReader.OCR.Default')


class DefaultOCRProvider(BaseOCRProvider):
    """
    Default OCR provider using Tesseract.

    This provider uses the open-source Tesseract OCR engine to extract text
    from images and scanned PDF documents. It supports multiple languages
    (English, Russian, Azerbaijani, Uzbek, German) and provides high-quality
    text extraction for most document types.

    Features:
        - Multi-language support (eng+rus+aze+uzb+deu)
        - PDF to image conversion at 300 DPI
        - Automatic text extraction from searchable PDFs
        - Configurable OCR parameters

    Requirements:
        - Tesseract OCR installed on the system
        - Poppler utilities for PDF processing
        - Language data files for required languages

    Attributes:
        config (dict): OCR configuration dictionary (reserved for future use)
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize default Tesseract OCR provider.

        Args:
            config: OCR configuration dictionary. Currently reserved for
                   future configuration options such as DPI, languages,
                   or OCR engine parameters.

        Example:
            >>> config = {'dpi': 300, 'languages': 'eng+rus'}
            >>> provider = DefaultOCRProvider(config)
        """
        self.config = config
        logger.info("Initialized DefaultOCRProvider (Tesseract)")
        logger.debug("Configuration: %s", config)

    def process_document(self, ocr_file: str, out_doc_file_path: str) -> None:
        """
        Process document using Tesseract OCR.

        Performs OCR on the input PDF or image file using Tesseract engine
        and saves the extracted text as a formatted DOCX document.

        Process flow:
            1. Convert PDF pages to images (300 DPI, PNG format)
            2. Run Tesseract OCR on each image
            3. Combine extracted text from all pages
            4. Convert to DOCX format
            5. Clean up temporary files

        Args:
            ocr_file: Path to input file (PDF or image)
            out_doc_file_path: Path where DOCX output should be saved

        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If file format is invalid
            RuntimeError: If OCR processing fails
            PDFInfoNotInstalledError: If Poppler is not installed

        Example:
            >>> provider = DefaultOCRProvider({})
            >>> provider.process_document('scanned.pdf', 'output.docx')
        """
        logger.debug(f"Processing document with Tesseract: {ocr_file}")
        logger.info("Starting OCR process using Tesseract engine")

        try:
            ocr_pdf_image_to_doc(ocr_file, out_doc_file_path)
            logger.info(f"Tesseract OCR completed successfully: {out_doc_file_path}")
        except FileNotFoundError as e:
            logger.error(f"Input file not found: {ocr_file}")
            raise
        except ValueError as e:
            logger.error(f"Invalid file format: {e}")
            raise
        except Exception as e:
            logger.error(f"OCR processing failed: {e}", exc_info=True)
            raise RuntimeError(f"Tesseract OCR failed: {e}") from e

    def is_pdf_searchable(self, pdf_path: str) -> bool:
        """
        Check if PDF is searchable using existing implementation.

        Uses PyPDF to attempt text extraction from the PDF. If text can be
        extracted, the PDF is considered searchable and doesn't require OCR.

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF contains extractable text, False if image-based

        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If file is not a valid PDF
            RuntimeError: If PDF cannot be read

        Example:
            >>> provider = DefaultOCRProvider({})
            >>> if not provider.is_pdf_searchable('document.pdf'):
            ...     print("PDF requires OCR processing")
        """
        logger.debug(f"Checking if PDF is searchable: {pdf_path}")

        try:
            result = is_pdf_searchable_pypdf(pdf_path)
            logger.debug(f"PDF searchable check for {pdf_path}: {result}")

            if result:
                logger.info(f"PDF is searchable (contains extractable text): {pdf_path}")
            else:
                logger.info(f"PDF is image-based (requires OCR): {pdf_path}")

            return result
        except FileNotFoundError as e:
            logger.error(f"PDF file not found: {pdf_path}")
            raise
        except ValueError as e:
            logger.error(f"Invalid PDF file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error checking PDF searchability: {e}", exc_info=True)
            raise RuntimeError(f"Failed to check PDF searchability: {e}") from e
