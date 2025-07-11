"""
Process original documents.
Process txt, pdf, rtf, images, foreign language documents documents
to word document
"""
import os
from docx import Document
from striprtf.striprtf import rtf_to_text
from langdetect import detect
from src.pdf_image_ocr import is_pdf_searchable_pypdf2, ocr_pdf_image_to_doc
from src.convert_to_docx import convert_pdf_to_docx
from src.logger import logger
from src.utils import (
    delete_file,
    translate_document_to_english,
    read_word_doc_to_text,
    read_pdf_doc_to_text,
)
from src.utils import rename_file


class DocProcessor:
    """
    Class to process all type of docs and create
    collection of documents for processing by ChatGPT
    """

    def __init__(self, doc_path: str):
        """
        Initialise word document list
        and list for original documents
        """
        # Word documents
        self.documents: str = []
        # Original document
        self.original_documents: str = []
        # document folder path
        self.docs_path: str = doc_path

    # Process PDF documents
    def convert_pdf_payload_to_word(self, client: str, doc_name: str, payload: str) -> None:
        """
        Process PDF image or searchable doc and generate
        Word document
        Args:
        client:  client email
        doc_name: doc name '<email>+<doc name>'
        payload: content of the file
        """
        logger.info('Process PDF document %s', doc_name)
        file_name_no_ext, file_ext = os.path.splitext(doc_name)
        file_name = f'{client}+{file_name_no_ext}+original+original{file_ext}'
        file_path = os.path.join(self.docs_path, file_name)
        # Save original file in doc directory
        with open(file_path, "wb") as f:
            f.write(payload)

    def convert_pdf_file_to_word(self, pdf_file_path: str) -> None:
        """
        Convert PDF file (image or text) to word document
        Args:
        pdf_file_path: path for PDF file
        """
        logger.info(
            'Convert %s PDF file(image or text) to word document.', pdf_file_path)
        file_name_no_ext, _ = os.path.splitext(pdf_file_path)
        file_name_chunks = file_name_no_ext.split('+')
        file_path_name = f'{file_name_chunks[0]}+{file_name_chunks[1]}'
        # Check if file is image
        if is_pdf_searchable_pypdf2(pdf_file_path):
            text = read_pdf_doc_to_text(pdf_file_path)
            docx_file_path = f'{file_path_name}+original+english.docx'
            convert_pdf_to_docx(pdf_file_path, docx_file_path)
            if detect(text) != 'en':
                translated_file_path = f'{file_path_name}+original+translated.docx'
                translate_document_to_english(
                    docx_file_path, translated_file_path)
                delete_file(docx_file_path)
        else:
            ocr_file_path = f'{file_path_name}+ocr+english.docx'
            ocr_pdf_image_to_doc(pdf_file_path, ocr_file_path)
            text = read_word_doc_to_text(ocr_file_path)
            if detect(text) != 'en':
                translated_file_path = f'{file_path_name}+ocr+translated.docx'
                translate_document_to_english(
                    ocr_file_path, translated_file_path)
                delete_file(docx_file_path)

    # Process TIF document
    def convert_rtf_text_to_world(self, client: str, rtf_file_name: str, payload: str) -> None:
        """
        Converts a RTF text to a Word document.
        Args:
            client: client email
            txt_file_name: file name from attachment
            payload: payload from attachment
        """
        logger.info('Client %s convert TIF %s to Word document',
                    client, rtf_file_name)
        file_name_no_ext, _ = os.path.splitext(rtf_file_name)
        plain_text = rtf_to_text(payload)

        rtf_file_path = os.path.join(
            self.docs_path, f'{client}+{file_name_no_ext}+original+original.tft')
        with open(rtf_file_path, 'w', encoding='utf-8') as fl:
            fl.write(payload)

        doc_file_path = os.path.join(
            self.docs_path, f'{client}+{file_name_no_ext}+original+original.doc')
        with open(doc_file_path, 'w', encoding='utf-8') as fl:
            fl.write(plain_text)

        # Check if foreign language
        if detect(plain_text) != 'en':
            translated_file_path = os.path.join(
                self.docs_path, f'{client}+{file_name_no_ext}+original+translated.doc')
            translate_document_to_english(doc_file_path, translated_file_path)

    def convert_rtf_file_to_world(self, client: str, rtf_file_name: str) -> None:
        """
            Converts a RTF file to a Word document.
            Args:
                client: client email
                txt_file_name: file name from google drive
        """
        logger.info('Client %s convert TIF %s to Word document',
                    client, rtf_file_name)
        with open(rtf_file_name, 'r', encoding='utf-8') as fl:
            rtf_text = fl.read()

        file_name_no_ext, _ = os.path.splitext(rtf_file_name)
        plain_text = rtf_to_text(rtf_text)

        rtf_file_path = os.path.join(
            self.docs_path, f'{client}+{file_name_no_ext}+original+original.tft')
        with open(rtf_file_path, 'w', encoding='utf-8') as fl:
            fl.write(rtf_text)

        doc_file_path = os.path.join(
            self.docs_path, f'{client}+{file_name_no_ext}+original+original.doc')
        with open(doc_file_path, 'w', encoding='utf-8') as fl:
            fl.write(plain_text)

        # Check if foreign language
        if detect(plain_text) != 'en':
            translated_file_path = os.path.join(
                self.docs_path, f'{client}+{file_name_no_ext}+original+translated.doc')
            translate_document_to_english(doc_file_path, translated_file_path)

    # Process plain text
    def convert_plain_text_to_word(self, client: str, txt_file_name: str, payload: str) -> None:
        """
        Converts a plain text to a Word document.
        Args:
            client: client email
            txt_file_name: file name from attachment
            payload: payload from attachment
        """
        logger.info('Convert txt to word %s', txt_file_name)
        file_name_no_ext, _ = os.path.splitext(txt_file_name)
        file_path = os.path.join(
            self.docs_path, f'{client}+{file_name_no_ext}+original+original.txt')
        doc_file_path = os.path.join(
            self.docs_path, f'{client}+{file_name_no_ext}+original+original.doc')
        with open(file_path, 'w', encoding='utf-8') as fl:
            fl.write(payload)
        document = Document()
        document.add_paragraph(payload)
        document.save(doc_file_path)

        # Check if foreign language
        if detect(payload) != 'en':
            translated_file_path = os.path.join(
                self.docs_path, f'{client}+{file_name_no_ext}+original+translated.doc')
            translate_document_to_english(doc_file_path, translated_file_path)

    def convert_plain_text_file_to_word(
            self,
            client: str,
            txt_file_name: str
    ) -> None:
        """
        Converts a plain text file to a Word document.
        Args:
            client: client email
            txt_file_name: file name from attachment
            payload: payload from attachment
        """
        logger.info('Convert txt file to word %s', txt_file_name)
        file_name_no_ext, _ = os.path.splitext(txt_file_name)
        file_path = os.path.join(
            self.docs_path, f'{client}+{file_name_no_ext}+original+original.txt')
        with open(file_path, 'r', encoding='utf-8') as fl:
            plain_text = fl.read()
        doc_file_path = os.path.join(
            self.docs_path, f'{client}+{file_name_no_ext}+original+original.doc')
        document = Document()
        document.add_paragraph(plain_text)
        document.save(doc_file_path)

        # Check if foreign language
        if detect(plain_text) != 'en':
            translated_file_path = os.path.join(
                self.docs_path, f'{client}+{file_name_no_ext}+original+translated.doc')
            translate_document_to_english(doc_file_path, translated_file_path)

    # Process Word document
    def process_word_load(self, client: str, word_file_name: str, payload: str) -> None:
        """
        Process Word document text to Word file
        Args:
            client: client email
            txt_file_name: file name from attachment
            payload: payload from attachment
        """
        logger.info('Process Word doc text to file %s', word_file_name)
        if detect(payload) == 'en':
            word_file_name = f'{client}+{word_file_name}+original+english.docx'
            word_file_path = os.path.join(self.docs_path, word_file_name)
            with open(word_file_path, 'w', encoding='utf-8') as fl:
                fl.write(payload)
        else:
            word_file_name = f'{client}+{word_file_name}+original+foreign.docx'
            word_file_path = os.path.join(self.docs_path, word_file_name)
            with open(word_file_path, 'w', encoding='utf-8') as fl:
                fl.write(payload)
            translated_file_name = f'{client}+{word_file_name}+original+translated.docx'
            translated_file_path = os.path.join(
                self.docs_path, translated_file_name)
            translate_document_to_english(word_file_path, translated_file_path)

    def process_word_file(
            self,
            client: str,
            file_name: str,
            document_folder: str
    ) -> tuple[str, str, str, str]:
        """
        Process Word document text to Word file and translate it if needed.
        Args:
            client: client email
            word_file_name: file name with +original+original
        """
        logger.info('Process Word doc text to file %s', file_name)
        file_path = os.path.join(document_folder, file_name)
        file_name_no_ext, file_ext = os.path.splitext(file_name)
        document = Document(file_path)
        # Check if document language is English
        full_text: list[str] = []
        for paragraph in document.paragraphs:
            full_text.append(paragraph.text)
        text = '/n'.join(full_text)
        # If English, rename file with +english
        if detect(text) == 'en':
            new_file_name = f'{client}+{file_name_no_ext}+english{file_ext}'
            new_file_path = os.path.join(document_folder, new_file_name)
            rename_file(file_path, new_file_path)
            original_file_name = new_file_name
            original_file_path = new_file_path
        else:
            # If not English, translate it and rename file with +translated
            # Rename original file with +original
            original_file_name = f'{client}+{file_name_no_ext}+original{file_ext}'
            original_file_path = os.path.join(
                document_folder, original_file_name)
            rename_file(file_path, original_file_path)
            # Translate document to English
            new_file_name = f'{client}+{file_name_no_ext}+translated{file_ext}'
            new_file_path = os.path.join(document_folder, new_file_name)
            translate_document_to_english(original_file_path, new_file_path)
        return (new_file_path, new_file_name, original_file_name, original_file_path)
