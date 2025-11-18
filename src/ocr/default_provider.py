"""
Default OCR Provider (Tesseract)

Wraps existing Tesseract OCR logic from pdf_image_ocr.py
"""

import os
import logging
from typing import Dict, Any

from src.ocr.base_provider import BaseOCRProvider
from src.pdf_image_ocr import is_pdf_searchable_pypdf, ocr_pdf_image_to_doc
from src.convert_to_docx import convert_pdf_to_docx

logger = logging.getLogger('EmailReader.OCR.Default')


class DefaultOCRProvider(BaseOCRProvider):
    """
    Default OCR provider using Tesseract.

    Wraps the existing Tesseract-based OCR functionality
    from pdf_image_ocr.py module.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the default OCR provider.

        Args:
            config: Configuration dictionary (currently unused for Tesseract)
        """
        super().__init__(config)
        logger.info("Initialized DefaultOCRProvider (Tesseract)")

    def process_document(self, input_path: str, output_path: str) -> None:
        """
        Process a document with OCR and save the result.

        Uses Tesseract OCR for scanned PDFs, or direct text extraction
        for searchable PDFs.

        Args:
            input_path: Path to input file (PDF or image)
            output_path: Path to save output DOCX file

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If OCR processing fails
        """
        logger.info("Processing document with Tesseract: %s", os.path.basename(input_path))
        logger.debug("Input: %s", input_path)
        logger.debug("Output: %s", output_path)

        if not os.path.exists(input_path):
            logger.error("Input file not found: %s", input_path)
            raise FileNotFoundError(f"File not found: {input_path}")

        try:
            # Check if PDF is searchable
            logger.debug("Checking if PDF is searchable")
            is_searchable = self.is_pdf_searchable(input_path)

            if is_searchable:
                logger.info("PDF is searchable - using text extraction")
                convert_pdf_to_docx(input_path, output_path)
            else:
                logger.info("PDF is not searchable - using OCR")
                ocr_pdf_image_to_doc(input_path, output_path)

            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / 1024  # KB
                logger.info("Document processed successfully: %s (%.2f KB)",
                           os.path.basename(output_path), file_size)
            else:
                logger.error("Processing failed - output file not created")
                raise RuntimeError("OCR processing failed to create output file")

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error("Error processing document: %s", e, exc_info=True)
            raise RuntimeError(f"OCR processing failed: {e}")

    def is_pdf_searchable(self, pdf_path: str) -> bool:
        """
        Check if a PDF contains searchable text.

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF has extractable text, False otherwise
        """
        logger.debug("Checking if PDF is searchable: %s", os.path.basename(pdf_path))

        try:
            result = is_pdf_searchable_pypdf(pdf_path)
            logger.debug("PDF searchable check result: %s", result)
            return result
        except Exception as e:
            logger.error("Error checking PDF searchability: %s", e)
            raise
