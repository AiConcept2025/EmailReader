"""
Utilities
"""

import json
import os
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
import shutil
from pypdf import PdfReader
from docx import Document
from striprtf.striprtf import rtf_to_text  # type: ignore

# Get logger for this module
logger = logging.getLogger('EmailReader.Utils')


def read_json_secret_file(
        file_path: str
) -> (Dict[str, Dict[str, str]] | None):
    """
    Reads a JSON Secrets file and returns its content as a
    Python dictionary.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: A dictionary representing the JSON data,
        or None if an error occurs.
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not a valid JSON.
        OSError: If an OS error occurs while reading the file.
        exception: For any other exceptions that may occur.
    """
    logger.debug("Entering read_json_secret_file() for: %s", file_path)

    try:
        if not os.path.exists(file_path):
            logger.error('File not found at %s', file_path)
            return None

        file_size = os.path.getsize(file_path)
        logger.debug("Reading JSON file, size: %d bytes", file_size)

        with open(file_path, encoding='utf-8', mode='r') as file:
            data = json.load(file)
            logger.debug("JSON file parsed successfully, keys: %s", list(
                data.keys()) if isinstance(data, dict) else "not a dict")
            return data

    except FileNotFoundError:
        logger.error('Error: File not found at %s', file_path)
        return None
    except json.JSONDecodeError as e:
        logger.error('Error: Invalid JSON format in %s: %s', file_path, e)
        return None
    except OSError as e:
        logger.error('An OS error occurred while reading %s: %s', file_path, e)
        return None
    except Exception as e:
        logger.error('Unexpected error reading JSON file %s: %s',
                     file_path, e, exc_info=True)
        return None


def list_all_dir_files() -> List[str]:
    """
    List all files in specify folder
    Args:
        folder: folder name
    """
    from src.config import load_config

    cwd = os.getcwd()
    config = load_config()
    if config is None or config.get('storage') is None:
        logger.error('Documents folder not specified in configuration')
        return []
    if not isinstance(config.get('storage'), dict):
        logger.error('Documents folder not specified in configuration')
        return []
    documents_folder: str = config.get('storage').get('documents_folder')
    attachments_path = Path(os.path.join(cwd, documents_folder))
    attachments_dir_list = os.listdir(attachments_path)
    return attachments_dir_list


def list_files_in_directory(folder_path: str) -> List[str]:
    """
    Lists all files in the specified directory.

    Args:
      folder_path: The path to the directory.

    Returns:
      A list of file names in the directory.
    """
    try:
        file_list = os.listdir(folder_path)
        return file_list
    except FileNotFoundError:
        print(f"Error: Directory not found: {folder_path}")
        return []
    except NotADirectoryError:
        print(f"Error: Not a directory: {folder_path}")
        return []


def get_uuid() -> str:
    """
    Generate a unique identifier (UUID).

    Returns:
        str: A string representation of the UUID.
    """
    return str(uuid.uuid4())


def read_pdf_doc_to_text(pdf_file_path: str) -> str:
    """
    Read PDF file to text
    Args:
    pdf_file_path: path for PDF file
    """
    reader = PdfReader(pdf_file_path)
    num_pages = len(reader.pages)
    full_text: list[str] = []
    for page_num in range(num_pages):
        page = reader.pages[page_num]
        text_on_page = page.extract_text()
        full_text.append(text_on_page)
    extract_text = '\n'.join(full_text)
    reader.close()
    return extract_text


def read_word_doc_to_text(word_doc_path: str) -> str:
    """
    Read Word dov to text
    Args:
    word_doc_path: path do word document
    """
    document = Document(word_doc_path)
    full_text: list[str] = []
    for paragraph in document.paragraphs:
        full_text.append(paragraph.text)
    extracted_text = '\n'.join(full_text)
    return extracted_text


def translate_document_to_english(
        original_path: str,
        translated_path: str,
        source_lang: str | None = None,
        target_lang: str | None = None
) -> None:
    """
    Translates word document to English (or a specified target language)
    using Google Cloud Document Translation API which preserves formatting.

    Args:
        original_path: foreign language word document Word format
        translated_path: output english Word document Word format
        source_lang: optional source language code (e.g., 'ru', 'es') or None for auto-detect
        target_lang: optional language code to translate to (e.g., 'en', 'fr')
    """
    logger.debug("Entering translate_document_to_english()")
    logger.debug("Original: %s", original_path)
    logger.debug("Translated: %s", translated_path)
    logger.debug("Source language: %s", source_lang or 'auto-detect')
    logger.debug("Target language: %s", target_lang or 'en (default)')

    if not os.path.exists(original_path):
        logger.error("Original file not found: %s", original_path)
        raise FileNotFoundError(f"File not found: {original_path}")

    try:
        # Use paragraph-based translation for better quality control
        from src.translation import get_translator
        from src.config import load_config

        logger.info("Initializing document translator (paragraph-based mode)")
        config = load_config()
        translator = get_translator(config)

        # Set target language (default to 'en' if not specified)
        target = target_lang if target_lang else 'en'

        logger.info("Translating document using paragraph-based approach")
        translator.translate_document_paragraphs(
            input_path=original_path,
            output_path=translated_path,
            source_lang=source_lang,
            target_lang=target
        )

        if os.path.exists(translated_path):
            file_size = os.path.getsize(translated_path) / 1024  # KB
            logger.info("Translation completed successfully: %s (%.2f KB)",
                       os.path.basename(translated_path), file_size)
        else:
            logger.error("Translation completed but output file not found: %s",
                        translated_path)
            raise FileNotFoundError(f"Translated file not created: {translated_path}")

    except Exception as e:
        logger.error('Error during document translation: %s', e, exc_info=True)
        raise


def copy_file(source_file: str, destination_file: str) -> bool:
    """
    Copies file
    source_file: source file
    destination_file: destination file
    """
    try:
        logger.info("COPY file: %s -> %s", source_file, destination_file)
        shutil.copy(source_file, destination_file)
        logger.info("COPY OK: %s", destination_file)
        return True
    except FileNotFoundError:
        logger.error('Error: Source file %s not found.', source_file)
        return False
    except Exception as e:
        logger.error('An error occurred: %s', e)
        return False


def delete_file(file_path: str) -> None:
    """
    Delete file by path
    """
    if os.path.exists(file_path):
        try:
            logger.info("DELETE file: %s", file_path)
            os.remove(file_path)
            logger.info("DELETE OK: %s", file_path)
        except OSError as e:
            logger.error('Error %s deleting file %s:', e, file_path)
    else:
        logger.error('File %s does not exist.', file_path)


def rename_file(current_file_name: str, new_file_name: str):
    """
    Attempt to rename the file
    """
    try:
        logger.info("RENAME file: %s -> %s", current_file_name, new_file_name)
        os.rename(current_file_name, new_file_name)
        logger.info("RENAME OK: %s", new_file_name)
    except FileNotFoundError:
        logger.error("RENAME missing source: %s", current_file_name)
    except PermissionError:
        logger.error("RENAME permission denied: %s", current_file_name)
    except Exception as e:
        logger.error("RENAME unexpected error: %s", e)


def convert_rtx_to_text(rtf_text: str) -> str:
    """
    Converts RTF text to plain text.
    Args:
        rtf_text: RTF formatted text.
    Returns:
        Plain text extracted from the RTF.
    """
    plain_text: str = rtf_to_text(rtf_text)
    return plain_text


def utc_to_local(utc_dt: datetime) -> datetime:
    """
    Convert date/time to local time zone
    Args:
        utc_dt: UTC datetime object to convert.
    Returns:
        datetime: A datetime object in the local time zone.
    """
    time_stamp = utc_dt.replace(tzinfo=timezone.utc)
    return time_stamp


def build_flowise_question(customer_email: str, file_name_with_ext: str) -> str:
    """
    Build Flowise/document-store name:
    - Strip processing suffix (+english/+translated/+original)
    - Ensure .docx extension
    Final format: email+OriginalName.docx
    """
    logger.debug("Entering build_flowise_question()")
    logger.debug("Input - email: %s, file: %s",
                 customer_email, file_name_with_ext)

    base, ext = os.path.splitext(file_name_with_ext or "")
    logger.debug("Base name: %s, extension: %s", base, ext)

    # Remove any processing suffix after the first '+'
    # e.g., "Serhii Zhuk letter+english" -> "Serhii Zhuk letter"
    if '+' in base:
        original_base = base
        base = base.split('+', 1)[0]
        logger.debug("Removed suffix from base: %s -> %s", original_base, base)

    # Enforce .docx extension
    if not ext or ext.lower() != '.docx':
        logger.debug("Enforcing .docx extension (was: %s)",
                     ext or "no extension")
        ext = '.docx'

    clean_name = f"{base}{ext}"
    result = f"{customer_email}+{clean_name}"
    logger.debug("Built Flowise question: %s", result)

    return result


def verify_paragraph_counts(
    ocr_count: int,
    docx_count: int,
    translated_count: int = None
) -> bool:
    """
    Verify paragraph counts across the OCR and translation pipeline.

    Logs a complete chain of counts and checks for consistency.
    This function provides end-to-end verification of paragraph preservation
    throughout the document processing pipeline.

    Args:
        ocr_count: Number of paragraphs extracted from OCR
        docx_count: Number of paragraphs written to DOCX file
        translated_count: Optional number of paragraphs after translation

    Returns:
        True if all counts match, False otherwise

    Example:
        >>> verify_paragraph_counts(ocr_count=25, docx_count=25, translated_count=25)
        # Logs: "Pipeline verification: OCR=25, DOCX=25, Translated=25 ✓"
        True

        >>> verify_paragraph_counts(ocr_count=25, docx_count=23)
        # Logs: "Pipeline verification: OCR=25, DOCX=23 ✗ MISMATCH"
        False
    """
    logger.debug("Entering verify_paragraph_counts()")
    logger.debug("OCR count: %d, DOCX count: %d, Translated count: %s",
                 ocr_count, docx_count, translated_count if translated_count is not None else "N/A")

    # Build verification message
    if translated_count is not None:
        verification_msg = f"OCR={ocr_count}, DOCX={docx_count}, Translated={translated_count}"
        all_match = (ocr_count == docx_count == translated_count)
    else:
        verification_msg = f"OCR={ocr_count}, DOCX={docx_count}"
        all_match = (ocr_count == docx_count)

    # Add status indicator
    status_indicator = "✓" if all_match else "✗ MISMATCH"
    full_message = f"Pipeline verification: {verification_msg} {status_indicator}"

    # Log at info level for visibility
    if all_match:
        logger.info(full_message)
        logger.info("PARAGRAPH_COUNT_VERIFICATION: stage=PIPELINE_COMPLETE, status=SUCCESS")
    else:
        logger.error(full_message)
        logger.error("PARAGRAPH_COUNT_VERIFICATION: stage=PIPELINE_COMPLETE, status=FAILURE")
        logger.error("Paragraph count mismatch detected in processing pipeline")

    return all_match
