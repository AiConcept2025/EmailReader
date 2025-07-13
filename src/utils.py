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

from src.logger import logger


def read_json_secret_file(file_path: str) -> (Dict[str, str] | None):
    """
    Reads a JSON Secrets file and returns its content as a Python dictionary.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: A dictionary representing the JSON data,
        or None if an error occurs.
    """
    try:
        with open(file_path, encoding="utf-8", mode="r") as file:
            data: Dict[str, str] = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{file_path}'")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def utc_to_local(utc_dt: datetime) -> datetime:
    """
    Convert date/time to local time zone

    Args:

    """
    time_stamp = utc_dt.replace(tzinfo=timezone.utc)
    return time_stamp


def list_all_dir_files():
    """
    List all files in specify folder
    Args:
        folder: folder name
    """
    cwd = os.getcwd()
    secrets: Dict = read_json_secret_file("secrets.json")
    documents_folder = secrets.get("documents").get("documents_folder")
    attachments_path = Path(os.path.join(cwd, documents_folder))
    attachments_dir_list = os.listdir(attachments_path)
    return attachments_dir_list


def list_files_in_directory(folder_path: str) -> List:
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


def translate_document_to_english(original_path: str, translated_path: str) -> None:
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
            'Error executing command: %s Stdout: %s, Stderr: %s', e, e.stdout, e.stderr)


def copy_file(source_file: str, destination_file: str) -> bool:
    """
    Copies file
    source_file: source file
    destination_file: destination file
    """
    try:
        shutil.copy(source_file, destination_file)
        return True
    except FileNotFoundError:
        logger.error('Error: Source file %s not found.', source_file)
        return False
    except Exception as e:
        logger.error('An error occurred: %s', e)
        return False


def delete_file(file_path: str):
    """
    Delete file by path
    """
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            logger.error('Error %s deleting file %s:', e, file_path)
    else:
        logger.error('File %s does not exist.', file_path)


def rename_file(current_file_name: str, new_file_name: str):
    """
    Attempt to rename the file
    """
    try:
        os.rename(current_file_name, new_file_name)
        print(
            f"File '{current_file_name}' successfully renamed to '{new_file_name}'.")
    except FileNotFoundError:
        print(f"Error: File '{current_file_name}' not found.")
    except PermissionError:
        print(
            f"Error: Permission denied. Unable to rename '{current_file_name}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
