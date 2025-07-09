"""
Convert docs to docx
"""
import os
import pdfplumber
import pymupdf
from docx import Document
from src.logger import logger


def convert_txt_to_docx(paragraph: str, docx_file_path: str):
    """
    Converts a plain text file to a Word document.

    Args:
        paragraph: text.
        docx_file_path: Path to save the output Word document.
    """
    logger.info('Convert txt to word %s', os.path.basename(docx_file_path))
    document = Document()
    document.add_paragraph(paragraph)
    document.save(docx_file_path)


def convert_txt1_to_docx(txt_file_path: str, docx_file_path: str):
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


def convert_pdf_to_docx(pdf_path, docx_path):
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


def convert_rtf_to_docs(rtf_filepath, dox_file):
    """
    Convert a rtf document to a DOCX file
    """
    # with open(rtf_filepath, 'r', encoding='utf-8') as file:
    #     rtf_content = file.read()
    # # Convert RTF content to plain text
    # plain_text = rtf_to_txt(rtf_content)
    # # Save plain text to a new file
    # with open(txt_file, 'w', encoding='utf-8') as file:
    #     file.write(plain_text)

    # with open(rtf_filepath, 'r', encoding='utf-8') as file:
    #     paragraph = file.read()
    # document = Document()
    # document.add_paragraph(paragraph)
    # document.save(txt_file)
    # Create a Document object
    # document = Document()
    # # Load the RTF file
    # document.LoadFromFile(rtf_filepath)
    # # Save the document as DOCX
    # # or FileFormat.Docx2019, etc.
    # document.SaveToFile(dox_file, FileFormat.Docx2013)
    # # Close the document
    # document.Close()


def check_if_image(pdf_file):
    doc = pymupdf.open(pdf_file)
    doc_len = 0
    for page in doc:  # iterate the document pages
        doc_len += len(page.get_text())  # get plain text encoded as UTF-8
    return doc_len > 0
