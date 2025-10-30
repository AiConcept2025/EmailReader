"""
Convert docs to docx
"""
import os
import pdfplumber
from docx import Document
from src.logger import logger


def convert_txt_to_docx(paragraph: str, docx_file_path: str) -> None:
    """
    Converts a plain text file to a Word document. test

    Args:
        paragraph: text.
        docx_file_path: Path to save the output Word document.
    """
    logger.info('Convert txt to word %s', os.path.basename(docx_file_path))
    document = Document()
    document.add_paragraph(paragraph)
    document.save(docx_file_path)


def convert_txt_file_to_docx(txt_file_path: str, docx_file_path: str) -> None:
    """
    Converts a plain text file to a Word document.

    Args:
        paragraph: text.
        docx_file_path: Path to save the output Word document.
    """
    logger.info('Convert txt to word %s', os.path.basename(docx_file_path))
    with open(txt_file_path, 'r', encoding='utf-8') as file:
        paragraph = file.read()
    document = Document()
    document.add_paragraph(paragraph)
    document.save(docx_file_path)


def convert_pdf_to_docx(pdf_path: str, docx_path: str):
    """
    Converts a PDF file to a DOCX file, preserving text formatting.
    """
    document = Document()
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:  # Avoid adding empty paragraphs
                document.add_paragraph(text)
        document.save(docx_path)
