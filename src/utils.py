"""
Utilities
"""

import json
import os
import logging
import subprocess
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
        target_lang: str | None = None
) -> None:
    """
    Translates word document to English (or a specified target language).
    Args:
    original_path: foreign language word document Word format
    translated_path: output english Word document Word format
    target_lang: optional language code to translate to (e.g., 'fr')
    """
    logger.debug("Entering translate_document_to_english()")
    logger.debug("Original: %s", original_path)
    logger.debug("Translated: %s", translated_path)
    logger.debug("Target language: %s", target_lang or 'en (default)')

    if not os.path.exists(original_path):
        logger.error("Original file not found: %s", original_path)
        raise FileNotFoundError(f"File not found: {original_path}")

    # Try to get translator path from config
    from src.config import load_config
    config = load_config()
    translator_script = config.get('app', {}).get('translator_executable_path')

    if translator_script and os.path.exists(translator_script):
        executable_path = Path(translator_script)
    else:
        # Fallback to old location
        executable_path = Path(os.path.join(os.getcwd(), "translate_document"))

    logger.debug("Translation executable: %s", executable_path)

    if not executable_path.exists():
        logger.error("Translation executable not found: %s", executable_path)
        raise FileNotFoundError(f"Executable not found: {executable_path}")

    arguments = ['-i', original_path, '-o', translated_path]
    if target_lang:
        arguments += ['--target', target_lang]

    # Call with python if it's a .py file
    if str(executable_path).endswith('.py'):
        # Use GoogleTranslator's virtual environment Python interpreter
        translator_dir = executable_path.parent
        venv_python = translator_dir / 'venv' / 'bin' / 'python'

        if venv_python.exists():
            command = [str(venv_python), str(executable_path)] + arguments
            logger.debug("Using GoogleTranslator venv: %s", venv_python)
        else:
            # Fallback to system python3
            command = ['python3', str(executable_path)] + arguments
            logger.warning("GoogleTranslator venv not found, using system python3")
    else:
        command = [str(executable_path)] + arguments

    logger.debug("Translation command: %s", ' '.join(command))

    try:
        logger.info("Starting translation subprocess")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True)
        logger.debug("Translation stdout: %s",
                     result.stdout if result.stdout else "(empty)")
        logger.info("Translation completed successfully: %s",
                    os.path.basename(translated_path))

        if os.path.exists(translated_path):
            file_size = os.path.getsize(translated_path) / 1024  # KB
            logger.debug("Translated file size: %.2f KB", file_size)
        else:
            logger.error(
                "Translation completed but output file not found: %s", translated_path)

    except subprocess.CalledProcessError as e:
        logger.error(
            'Translation command failed with exit code %d', e.returncode)
        logger.error('Command: %s', ' '.join(command))
        logger.error('Stdout: %s', e.stdout)
        logger.error('Stderr: %s', e.stderr)
        raise
    except Exception as e:
        logger.error('Unexpected error during translation: %s',
                     e, exc_info=True)
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
