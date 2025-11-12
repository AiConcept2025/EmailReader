"""
Process images pdf files
"""
import os
import logging
import tempfile
from sys import platform

import pytesseract
from pdf2image import convert_from_path  # type: ignore
from pdf2image.exceptions import (PDFInfoNotInstalledError, PDFPageCountError,
                                  PDFSyntaxError)
from pypdf import PdfReader

from src.convert_to_docx import convert_txt_to_docx

# Get logger for this module
logger = logging.getLogger('EmailReader.OCR')


def get_platform() -> str:
    """
    Returns operation system
    """
    logger.debug("Entering get_platform()")
    logger.debug("Platform detected: %s", platform)

    app_platform: str
    if platform == "linux" or platform == "linux2":
        app_platform = 'linux'
    elif platform == "darwin":
        app_platform = 'OS X'
    elif platform == "win32":
        app_platform = 'Windows'
    else:
        app_platform = 'Unknown'

    logger.info('EmailReader runs on: %s', app_platform)
    return app_platform


def validate_pdf_file(pdf_path: str) -> bool:
    """
    Validates that a file is actually a PDF by checking magic bytes.

    Args:
        pdf_path (str): Path to the PDF file

    Returns:
        bool: True if valid PDF, False otherwise

    Raises:
        ValueError: If file is not a valid PDF
    """
    logger.debug("Validating PDF file: %s", pdf_path)

    if not os.path.exists(pdf_path):
        logger.error("File does not exist: %s", pdf_path)
        raise FileNotFoundError(f"File not found: {pdf_path}")

    # Check file size
    file_size = os.path.getsize(pdf_path)
    logger.debug("File size: %d bytes", file_size)

    if file_size < 100:  # PDFs are typically > 100 bytes
        logger.error("File too small to be valid PDF: %d bytes (minimum ~100 bytes)", file_size)
        raise ValueError(f"Invalid PDF: file too small ({file_size} bytes)")

    # Check magic bytes (PDF header: %PDF-)
    try:
        with open(pdf_path, 'rb') as f:
            header = f.read(5)
            if not header.startswith(b'%PDF-'):
                logger.error(
                    "Invalid PDF header: %s (expected b'%%PDF-')",
                    header
                )
                raise ValueError(
                    f"Invalid PDF file: wrong magic bytes. "
                    f"Expected b'%PDF-', got {header!r}. "
                    f"This file may not be a real PDF document."
                )
        logger.debug("PDF validation passed")
        return True
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error("Error validating PDF: %s", e)
        raise ValueError(f"Failed to validate PDF file: {e}")


def is_pdf_searchable_pypdf(pdf_path: str) -> bool:
    """
    Checks if a PDF is searchable using pypdf (by attempting to extract text).
    Args:
        pdf_path (str): Path to the PDF document.
    Returns:
        bool: True if text can be extracted, False otherwise.
        exception: If an error occurs during processing.
    Raises:
        ValueError: If file is not a valid PDF
        Exception: If there is an error reading the PDF.
    """
    logger.debug("Entering is_pdf_searchable_pypdf() for: %s", pdf_path)

    # Validate PDF format first
    validate_pdf_file(pdf_path)

    try:
        if not os.path.exists(pdf_path):
            logger.error("PDF file not found: %s", pdf_path)
            return False

        file_size = os.path.getsize(pdf_path) / 1024  # Size in KB
        logger.debug("PDF file size: %.2f KB", file_size)

        logger.debug("Opening PDF with PdfReader")
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        logger.debug("PDF has %d pages", num_pages)

        total_text_length = 0
        for page_num, page in enumerate(reader.pages, 1):
            logger.debug("Extracting text from page %d/%d", page_num, num_pages)
            text = page.extract_text()
            if text:
                text_length = len(text.strip())
                total_text_length += text_length
                logger.debug("Page %d has %d characters", page_num, text_length)
                if text_length > 0:
                    logger.info("PDF is searchable - found text on page %d", page_num)
                    logger.debug("Total text extracted: %d characters", total_text_length)
                    return True  # Found text, so it's searchable

        logger.info("PDF is not searchable - no text found in %d pages", num_pages)
        return False  # No text found

    except (ValueError, FileNotFoundError):
        # Re-raise validation errors - these are fatal
        raise
    except Exception as e:
        logger.error('Error checking if PDF is searchable: %s', e, exc_info=True)
        # Don't assume it's image-based - raise error to avoid false processing
        raise RuntimeError(f"Failed to read PDF file: {e}")


def ocr_pdf_image_to_doc(ocr_file: str, out_doc_file_path: str) -> None:
    """
    Perform OCR on a PDF file and save the result as a DOCX file.
    """
    logger.info('Starting OCR process for PDF image: %s', os.path.basename(ocr_file))
    logger.debug("Input file: %s", ocr_file)
    logger.debug("Output DOCX: %s", out_doc_file_path)

    if not os.path.exists(ocr_file):
        logger.error("OCR input file not found: %s", ocr_file)
        raise FileNotFoundError(f"File not found: {ocr_file}")

    ocr_str: str = ''
    temp_dir = None

    try:
        logger.debug("Creating temporary directory for image extraction")
        temp_dir = tempfile.mkdtemp()
        logger.debug("Temporary directory: %s", temp_dir)

        logger.info("Converting PDF pages to images (DPI=300, format=PNG)")
        images_from_path = convert_from_path(
            pdf_path=ocr_file,
            output_folder=temp_dir,
            dpi=300,
            fmt='png',)

        num_images = len(images_from_path)
        logger.info("Extracted %d images from PDF", num_images)

        for idx, image in enumerate(images_from_path, 1):
            image_path = os.path.join(temp_dir, image.filename)
            logger.debug("Processing image %d/%d: %s", idx, num_images, image.filename)

            logger.debug("Running Tesseract OCR on image %d", idx)
            text: str = pytesseract.image_to_string(
                image_path,
                config='-c preserve_interword_spaces=1',
                lang="eng+rus+aze+uzb+deu")

            text_length = len(text)
            logger.debug("OCR extracted %d characters from image %d", text_length, idx)
            ocr_str += text

        total_chars = len(ocr_str)
        logger.info("Total OCR text extracted: %d characters", total_chars)

        if total_chars == 0:
            logger.warning("No text extracted from PDF images - OCR may have failed")

        logger.info("Converting OCR text to DOCX: %s", out_doc_file_path)
        convert_txt_to_docx(ocr_str, out_doc_file_path)
        logger.info("OCR process completed successfully")

    except PDFInfoNotInstalledError as e:
        logger.error('PDFInfoNotInstalledError: Poppler utilities not installed')
        logger.error('Install with: sudo apt-get install -y poppler-utils')
        logger.error('Error details: %s', e, exc_info=True)
        raise

    except PDFPageCountError as e:
        logger.error('PDFPageCountError: Could not determine page count')
        logger.error('Error details: %s', e, exc_info=True)
        raise

    except PDFSyntaxError as e:
        logger.error('PDFSyntaxError: Invalid PDF syntax')
        logger.error('Error details: %s', e, exc_info=True)
        raise

    except Exception as e:
        logger.error('Unexpected error during OCR process: %s', e, exc_info=True)
        raise

    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            logger.debug("Cleaning up temporary directory: %s", temp_dir)
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.debug("Temporary directory cleaned up")
            except Exception as e:
                logger.warning("Failed to clean up temp directory: %s", e)


if __name__ == '__main__':
    # Example usage
    ocr_pdf_image_to_doc('test_docs/PDF-scanned-rus-words.pdf',
                         'data/documents/file-pdf-image-to-doc.doc')
