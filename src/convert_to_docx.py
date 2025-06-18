"""
Convert docs to docx
"""
import os
import tempfile

import pdfplumber
import pymupdf
import pytesseract
from docx import Document
from pdf2image import convert_from_bytes, convert_from_path
from pdf2image.exceptions import (PDFInfoNotInstalledError, PDFPageCountError,
                                  PDFSyntaxError)
from rtf_converter import rtf_to_txt


def convert_txt_to_docx(paragraph: str, docx_file_path: str):
    """
    Converts a plain text file to a Word document.

    Args:
        paragraph: text.
        docx_file_path: Path to save the output Word document.
    """
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


def convert_rtf_to_txt(rtf_filepath, txt_file):
    with open(rtf_filepath, 'r', encoding='utf-8') as file:
        rtf_content = file.read()
    # Convert RTF content to plain text
    plain_text = rtf_to_txt(rtf_content)
    # Save plain text to a new file
    with open(txt_file, 'w', encoding='utf-8') as file:
        file.write(plain_text)


def check_if_image(pdf_file):
    doc = pymupdf.open(pdf_file)
    doc_len = 0
    for page in doc:  # iterate the document pages
        doc_len += len(page.get_text())  # get plain text encoded as UTF-8
    return doc_len > 0


def ocr(ocr_file):
    """
    Perform OCR on a PDF file and save the result as a DOCX file.
    """
    pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract'
    cwd = os.getcwd()
    poopler_folder = 'poppler-windows/poppler-24.08.0/Library/bin'
    poppler_path = os.path.join(cwd,  poopler_folder)

    str = ''
    try:
        with tempfile.TemporaryDirectory(delete=False) as temp_file:
            images_from_path = convert_from_path(
                pdf_path=ocr_file,
                output_folder=temp_file,
                poppler_path=poppler_path,
                dpi=300,
                fmt='png',)
            for image in images_from_path:
                image_path = os.path.join(temp_file, image.filename)
                text = pytesseract.image_to_string(image_path)
                str += text
    finally:
        print("OCR process completed.")
    convert_txt_to_docx(str, 'test.docx')


if __name__ == "__main__":
    # Example usage

    ocr("test_docs/file-sample-img.pdf")
