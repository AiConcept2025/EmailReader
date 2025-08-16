"""
Utilities
"""

import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
import shutil
from pypdf import PdfReader
from docx import Document
from striprtf.striprtf import rtf_to_text  # type: ignore
from src.logger import logger


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
    try:
        with open(file_path, encoding='utf-8', mode='r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        logger.error('Error: File not found at %s', file_path)
        return None
    except json.JSONDecodeError:
        logger.error('Error: Invalid JSON format in %s', file_path)
        return None
    except OSError as e:
        logger.error('An OS error occurred: %s', e)
        return None


def list_all_dir_files() -> List[str]:
    """
    List all files in specify folder
    Args:
        folder: folder name
    """
    cwd = os.getcwd()
    secrets = read_json_secret_file('secrets.json')
    if secrets is None or secrets.get('documents') is None:
        logger.error('Documents folder not specified in secrets.json')
        return []
    if not isinstance(secrets.get('documents'), dict):
        logger.error('Documents folder not specified in secrets.json')
        return []
    documents_folder: str = secrets.get('documents').get('documents_folder')
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
        translated_path: str
) -> None:
    """
    Translates word document in foreign language to English
    Args:
    original_path: foreign language word document Word format
    translated_path: output english Word document Word format
    """
    executable_path = Path(os.path.join(
        os.getcwd(), "translate_document"))
    arguments = ['-i', original_path, '-o', translated_path]
    command = [executable_path] + arguments
    try:
        subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(
            'Error executing command: %s Stdout: %s, Stderr: %s',
            e,
            e.stdout,
            e.stderr)


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
    base, ext = os.path.splitext(file_name_with_ext or "")
    # Remove any processing suffix after the first '+'
    # e.g., "Serhii Zhuk letter+english" -> "Serhii Zhuk letter"
    if '+' in base:
        base = base.split('+', 1)[0]
    # Enforce .docx extension
    if not ext or ext.lower() != '.docx':
        ext = '.docx'
    clean_name = f"{base}{ext}"
    return f"{customer_email}+{clean_name}"
