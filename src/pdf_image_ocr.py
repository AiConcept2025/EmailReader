"""
Process images pdf files
"""
import os
import tempfile
from sys import platform
from pypdf import PdfReader
import pytesseract
from pdf2image import convert_from_path
from pdf2image.exceptions import (PDFInfoNotInstalledError, PDFPageCountError,
                                  PDFSyntaxError)

from src.convert_to_docx import convert_txt_to_docx
from src.logger import logger


def get_platform() -> str:
    """
    Returns operation system
    """
    app_platform: str
    if platform == "linux" or platform == "linux2":
        app_platform = 'linux'
    elif platform == "darwin":
        app_platform = 'OS X'
    elif platform == "win32":
        app_platform = 'Windows'
    logger.info('EmailReader runs on %s', app_platform)
    return app_platform


def is_pdf_searchable_pypdf2(pdf_path: str) -> bool:
    """
    Checks if a PDF is searchable using pypdf (by attempting to extract text).

    Args:
        pdf_path (str): Path to the PDF document.

    Returns:
        bool: True if text can be extracted, False otherwise.
    """
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text and len(text.strip()) > 0:
                return True  # Found text, so it's searchable
        return False  # No text found
    except Exception as e:
        logger.error('Error processing PDF: %s', e)
        return False


def ocr_pdf_image_to_doc(ocr_file: str, out_doc_file_path: str) -> None:
    """
    Perform OCR on a PDF file and save the result as a DOCX file.
    """
    logger.info('Set ')
#    pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract'
    ocr_str: str = ''
    try:
        with tempfile.TemporaryDirectory(delete=False) as temp_file:
            images_from_path = convert_from_path(
                pdf_path=ocr_file,
                output_folder=temp_file,
                dpi=300,
                fmt='png',)
            for image in images_from_path:
                image_path = os.path.join(temp_file, image.filename)
                text = pytesseract.image_to_string(
                    image_path, config='-c preserve_interword_spaces=1', lang="rus")
                ocr_str += text
    except PDFInfoNotInstalledError as e:
        # sudo apt-get update
        # sudo apt-get install -y poppler-utils
        # which pdfinfo # /usr/bin/pdfinfo.
        logger.error('PDFInfoNotInstalledError %s', e)
    except PDFPageCountError as e:
        logger.error('PDFPageCountError %s', e)
    except PDFSyntaxError as e:
        logger.error('PDFSyntaxError %s', e)
    finally:
        print("OCR process completed.")
    convert_txt_to_docx(ocr_str, out_doc_file_path)


if __name__ == '__main__':
    # Example usage
    ocr_pdf_image_to_doc('test_docs/file-sample-img.pdf',
                         'data/documents/file-pdf-image-to-doc.doc')
