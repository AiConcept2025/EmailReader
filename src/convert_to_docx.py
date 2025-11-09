"""
Convert docs to docx
"""
import os
import logging
import pdfplumber
from docx import Document

# Get logger for this module
logger = logging.getLogger('EmailReader.DocConverter')


def convert_txt_to_docx(paragraph: str, docx_file_path: str) -> None:
    """
    Converts a plain text file to a Word document. test

    Args:
        paragraph: text.
        docx_file_path: Path to save the output Word document.
    """
    logger.debug("Entering convert_txt_to_docx()")
    logger.debug("Output path: %s", docx_file_path)

    try:
        text_length = len(paragraph)
        logger.debug("Text length: %d characters", text_length)

        if text_length == 0:
            logger.warning("Empty text provided for conversion")

        logger.debug("Creating new Word document")
        document = Document()
        document.add_paragraph(paragraph)

        logger.debug("Saving document to: %s", docx_file_path)
        document.save(docx_file_path)

        if os.path.exists(docx_file_path):
            file_size = os.path.getsize(docx_file_path) / 1024  # KB
            logger.info('Text converted to Word successfully: %s (%.2f KB)',
                       os.path.basename(docx_file_path), file_size)
        else:
            logger.error("Document save failed - file not found: %s", docx_file_path)

    except Exception as e:
        logger.error("Error converting text to DOCX: %s", e, exc_info=True)
        raise


def convert_txt_file_to_docx(txt_file_path: str, docx_file_path: str) -> None:
    """
    Converts a plain text file to a Word document.

    Args:
        paragraph: text.
        docx_file_path: Path to save the output Word document.
    """
    logger.debug("Entering convert_txt_file_to_docx()")
    logger.debug("Input TXT: %s", txt_file_path)
    logger.debug("Output DOCX: %s", docx_file_path)

    try:
        if not os.path.exists(txt_file_path):
            logger.error("Text file not found: %s", txt_file_path)
            raise FileNotFoundError(f"File not found: {txt_file_path}")

        input_size = os.path.getsize(txt_file_path) / 1024  # KB
        logger.debug("Input file size: %.2f KB", input_size)

        logger.debug("Reading text file")
        with open(txt_file_path, 'r', encoding='utf-8') as file:
            paragraph = file.read()

        text_length = len(paragraph)
        logger.debug("Read %d characters from file", text_length)

        logger.debug("Creating Word document")
        document = Document()
        document.add_paragraph(paragraph)

        logger.debug("Saving document to: %s", docx_file_path)
        document.save(docx_file_path)

        if os.path.exists(docx_file_path):
            output_size = os.path.getsize(docx_file_path) / 1024  # KB
            logger.info('TXT file converted to Word: %s (%.2f KB)',
                       os.path.basename(docx_file_path), output_size)
        else:
            logger.error("Document save failed - file not found: %s", docx_file_path)

    except Exception as e:
        logger.error("Error converting TXT file to DOCX: %s", e, exc_info=True)
        raise


def convert_pdf_to_docx(pdf_path: str, docx_path: str):
    """
    Converts a PDF file to a DOCX file, preserving text formatting.
    """
    logger.debug("Entering convert_pdf_to_docx()")
    logger.debug("Input PDF: %s", pdf_path)
    logger.debug("Output DOCX: %s", docx_path)

    try:
        if not os.path.exists(pdf_path):
            logger.error("PDF file not found: %s", pdf_path)
            raise FileNotFoundError(f"File not found: {pdf_path}")

        input_size = os.path.getsize(pdf_path) / 1024  # KB
        logger.debug("Input PDF size: %.2f KB", input_size)

        logger.debug("Opening PDF with pdfplumber")
        document = Document()
        total_text_length = 0

        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            logger.info("PDF has %d pages", num_pages)

            for page_num, page in enumerate(pdf.pages, 1):
                logger.debug("Processing page %d/%d", page_num, num_pages)
                text = page.extract_text()

                if text:
                    text_length = len(text)
                    total_text_length += text_length
                    logger.debug("Page %d: extracted %d characters", page_num, text_length)
                    document.add_paragraph(text)
                else:
                    logger.debug("Page %d: no text extracted", page_num)

            logger.info("Total text extracted: %d characters from %d pages",
                       total_text_length, num_pages)

            logger.debug("Saving DOCX file")
            document.save(docx_path)

        if os.path.exists(docx_path):
            output_size = os.path.getsize(docx_path) / 1024  # KB
            logger.info('PDF converted to Word: %s (%.2f KB)',
                       os.path.basename(docx_path), output_size)
        else:
            logger.error("Document save failed - file not found: %s", docx_path)

    except Exception as e:
        logger.error("Error converting PDF to DOCX: %s", e, exc_info=True)
        raise
