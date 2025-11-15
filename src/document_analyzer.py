"""Document analysis utilities for determining OCR requirements."""

import os
import logging
from pathlib import Path
from typing import Literal, Optional

from src.pdf_image_ocr import is_pdf_searchable_pypdf


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module name.

    Args:
        name: Logger name (e.g., 'EmailReader.DocumentAnalyzer')

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


logger = get_logger('EmailReader.DocumentAnalyzer')

# Document type constants
DocumentType = Literal[
    'pdf_searchable',      # PDF with extractable text
    'pdf_scanned',         # PDF without extractable text (image-based)
    'image',               # Image files (.jpg, .png, .tiff, etc.)
    'word_document',       # Word documents (.docx, .doc)
    'text_document',       # Text files (.txt, .rtf)
    'unknown'              # Unsupported or unrecognized format
]


def requires_ocr(file_path: str) -> bool:
    """
    Determine if a document requires OCR processing.

    This function checks if a document needs OCR based on:
    - File type (images always need OCR)
    - PDF content (scanned PDFs need OCR, searchable PDFs don't)
    - Document format (Word docs never need OCR)

    Args:
        file_path: Absolute path to the document file

    Returns:
        True if document requires OCR, False otherwise

    Raises:
        FileNotFoundError: If file doesn't exist

    Examples:
        >>> requires_ocr('document.pdf')  # Searchable PDF
        False
        >>> requires_ocr('scan.pdf')  # Scanned PDF
        True
        >>> requires_ocr('photo.jpg')
        True
        >>> requires_ocr('report.docx')
        False
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    doc_type = get_document_type(file_path)

    ocr_required = doc_type in ('pdf_scanned', 'image')
    logger.debug(f"OCR required for {file_path}: {ocr_required} (type: {doc_type})")

    return ocr_required


def get_document_type(file_path: str) -> DocumentType:
    """
    Classify document type based on file extension and content.

    Args:
        file_path: Path to the document

    Returns:
        DocumentType classification

    Examples:
        >>> get_document_type('scan.pdf')
        'pdf_scanned'
        >>> get_document_type('image.jpg')
        'image'
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found for type detection: {file_path}")
        return 'unknown'

    ext = Path(file_path).suffix.lower()

    # PDF files require content analysis
    if ext == '.pdf':
        return get_pdf_type(file_path)

    # Image files always need OCR
    if ext in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp'}:
        logger.debug(f"Detected image file: {file_path}")
        return 'image'

    # Word documents don't need OCR
    if ext in {'.docx', '.doc'}:
        logger.debug(f"Detected Word document: {file_path}")
        return 'word_document'

    # Text documents don't need OCR
    if ext in {'.txt', '.rtf'}:
        logger.debug(f"Detected text document: {file_path}")
        return 'text_document'

    logger.warning(f"Unknown document type: {file_path} (ext: {ext})")
    return 'unknown'


def get_pdf_type(pdf_path: str) -> Literal['pdf_searchable', 'pdf_scanned']:
    """
    Determine if PDF is searchable or scanned.

    Uses the existing is_pdf_searchable_pypdf() function to detect
    if the PDF contains extractable text.

    Args:
        pdf_path: Path to PDF file

    Returns:
        'pdf_searchable' if text can be extracted,
        'pdf_scanned' if PDF is image-based

    Examples:
        >>> get_pdf_type('text.pdf')
        'pdf_searchable'
        >>> get_pdf_type('scan.pdf')
        'pdf_scanned'
    """
    try:
        is_searchable = is_pdf_searchable_pypdf(pdf_path)
        pdf_type = 'pdf_searchable' if is_searchable else 'pdf_scanned'
        logger.debug(f"PDF type for {pdf_path}: {pdf_type}")
        return pdf_type
    except Exception as e:
        logger.error(f"Error detecting PDF type for {pdf_path}: {e}")
        # Default to scanned if we can't determine
        # (safer to run OCR than skip it)
        logger.warning(f"Defaulting to 'pdf_scanned' for safety")
        return 'pdf_scanned'


def is_image_based_pdf(pdf_path: str) -> bool:
    """
    Check if PDF is image-based (scanned document).

    This is a convenience function that wraps get_pdf_type().

    Args:
        pdf_path: Path to PDF file

    Returns:
        True if PDF is image-based/scanned, False if searchable

    Examples:
        >>> is_image_based_pdf('scan.pdf')
        True
        >>> is_image_based_pdf('text.pdf')
        False
    """
    return get_pdf_type(pdf_path) == 'pdf_scanned'


def get_supported_extensions() -> dict[str, list[str]]:
    """
    Get dictionary of supported file extensions by category.

    Returns:
        Dictionary mapping categories to extension lists

    Example:
        >>> ext = get_supported_extensions()
        >>> ext['images']
        ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp']
    """
    return {
        'pdf': ['.pdf'],
        'images': ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp'],
        'word': ['.docx', '.doc'],
        'text': ['.txt', '.rtf']
    }


def is_supported_format(file_path: str) -> bool:
    """
    Check if file format is supported for processing.

    Args:
        file_path: Path to file

    Returns:
        True if file format is supported, False otherwise

    Examples:
        >>> is_supported_format('document.pdf')
        True
        >>> is_supported_format('video.mp4')
        False
    """
    ext = Path(file_path).suffix.lower()
    all_extensions = []

    for ext_list in get_supported_extensions().values():
        all_extensions.extend(ext_list)

    is_supported = ext in all_extensions
    logger.debug(f"Format support check for {file_path}: {is_supported}")

    return is_supported


# Example usage and testing
if __name__ == '__main__':
    # Example: Test with actual files
    test_files = [
        'test_docs/file-sample-pdf.pdf',           # Searchable PDF
        'test_docs/PDF-scanned-rus-words.pdf',    # Scanned PDF
        'test_docs/file-sample-img.pdf',          # Image-based PDF
        'test_docs/file-sample-doc.doc',          # Word document
        'test_docs/file-sample-txt.txt',          # Text file
        'test_docs/file-sample-rtf.rtf',          # RTF file
    ]

    print("Document Analysis Test:")
    print("=" * 80)

    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                doc_type = get_document_type(file_path)
                needs_ocr = requires_ocr(file_path)
                is_supported = is_supported_format(file_path)

                print(f"{Path(file_path).name:35} | Type: {doc_type:15} | OCR: {str(needs_ocr):5} | Supported: {is_supported}")
            except Exception as e:
                print(f"{Path(file_path).name:35} | Error: {str(e)}")
        else:
            print(f"{Path(file_path).name:35} | File not found")

    print("=" * 80)
    print("\nSupported Extensions:")
    print("-" * 80)
    for category, extensions in get_supported_extensions().items():
        print(f"{category:10} : {', '.join(extensions)}")
    print("=" * 80)
