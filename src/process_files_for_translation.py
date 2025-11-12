"""src/process_files_for_translation.py"""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import requests

from src.google_drive import GoogleApi
from src.config import load_config
from src.utils import delete_file
from src.pdf_image_ocr import is_pdf_searchable_pypdf, ocr_pdf_image_to_doc
from src.convert_to_docx import convert_pdf_to_docx

logger = logging.getLogger('EmailReader.GoogleDrive')

cwd = os.getcwd()


def find_translator_executable() -> Optional[Tuple[Path, Path]]:
    """
    Find the translator executable with fallback logic.

    Priority:
    1. Configured path from secrets.json (translator_executable_path)
    2. GoogleTranslator project (sibling directory) - Python script
    3. GoogleTranslator project (sibling directory) - compiled executable
    4. EmailReader root directory (legacy) - compiled executable
    5. EmailReader root directory (legacy) - Python script

    Returns:
        Tuple of (script_path, python_interpreter_path) or None if not found.
        For GoogleTranslator Python script, returns its own venv Python.
        For other paths, returns current Python interpreter.
    """
    logger.debug("Searching for translator executable")

    # Try configured path from config
    try:
        config = load_config()
        if config:
            configured_path = config.get('app', {}).get('translator_executable_path')
            if configured_path:
                path = Path(configured_path)
                if path.exists():
                    logger.info("Using configured translator path: %s", path)

                    # Check if configured path is GoogleTranslator's Python script
                    if path.suffix == '.py' and 'GoogleTranslator' in str(path):
                        # Try to use GoogleTranslator's venv
                        google_translator_venv = Path(__file__).parent.parent.parent / 'GoogleTranslator' / 'venv' / 'bin' / 'python'
                        if google_translator_venv.exists():
                            logger.info("Configured path is GoogleTranslator script, using its venv: %s", google_translator_venv)
                            return (path.resolve(), google_translator_venv)
                        else:
                            logger.warning(
                                "GoogleTranslator venv not found, using current Python (may have missing dependencies)"
                            )

                    # For other configured paths, use current Python interpreter
                    return (path, Path(sys.executable))
                else:
                    logger.warning("Configured translator path does not exist: %s", configured_path)
    except Exception as e:
        logger.debug("Error reading configuration: %s", e)

    # Try GoogleTranslator project (sibling directory) - Python script
    google_translator_py = Path(__file__).parent.parent.parent / 'GoogleTranslator' / 'translate_document.py'
    if google_translator_py.exists():
        logger.info("Found GoogleTranslator Python script: %s", google_translator_py)

        # Try to use GoogleTranslator's own venv Python
        google_translator_venv = Path(__file__).parent.parent.parent / 'GoogleTranslator' / 'venv' / 'bin' / 'python'

        if google_translator_venv.exists():
            logger.info("Using GoogleTranslator's venv Python: %s", google_translator_venv)
            return (google_translator_py.resolve(), google_translator_venv)
        else:
            logger.warning(
                "GoogleTranslator venv not found at: %s. "
                "Using current Python interpreter (may have missing dependencies)",
                google_translator_venv
            )
            return (google_translator_py.resolve(), Path(sys.executable))
    else:
        logger.debug("GoogleTranslator Python script not found at: %s", google_translator_py)

    # Try GoogleTranslator project (sibling directory) - compiled executable
    google_translator_bin = Path(__file__).parent.parent.parent / 'GoogleTranslator' / 'translate_document'
    if google_translator_bin.exists():
        logger.info("Found GoogleTranslator executable: %s", google_translator_bin)
        # Compiled executable doesn't need Python interpreter
        return (google_translator_bin, Path(sys.executable))
    else:
        logger.debug("GoogleTranslator executable not found at: %s", google_translator_bin)

    # Try EmailReader root directory (legacy) - compiled executable
    legacy_bin = Path(cwd) / 'translate_document'
    if legacy_bin.exists():
        logger.info("Found legacy translator executable: %s", legacy_bin)
        return (legacy_bin, Path(sys.executable))
    else:
        logger.debug("Legacy executable not found at: %s", legacy_bin)

    # Try EmailReader root directory (legacy) - Python script
    legacy_py = Path(cwd) / 'translate_document.py'
    if legacy_py.exists():
        logger.info("Found legacy translator Python script: %s", legacy_py)
        return (legacy_py, Path(sys.executable))
    else:
        logger.debug("Legacy Python script not found at: %s", legacy_py)

    logger.error("Translator executable not found in any location")
    return None


def get_translate_folder_id() -> str:
    """Retrieve the Google Drive folder ID for
    translation files from configuration."""
    logger.debug("Entering get_translate_folder_id()")

    config = load_config()
    folder_id = config.get('google_drive', {}).get('parent_folder_id', '')

    if not folder_id:
        logger.warning("No 'parent_folder_id' found in configuration")
    else:
        logger.debug("Translation folder ID: %s", folder_id)

    return folder_id


def convert_to_docx_for_translation(input_path: str, output_path: str) -> None:
    """
    Convert various file formats to DOCX for translation.
    Supports: PDF (searchable and scanned with OCR), images (JPEG, PNG, TIFF).

    Args:
        input_path: Path to input file (PDF, image, etc.)
        output_path: Path to output DOCX file

    Raises:
        ValueError: If file type is not supported
        FileNotFoundError: If input file doesn't exist
    """
    logger.debug("Converting file to DOCX: %s -> %s", input_path, output_path)

    if not os.path.exists(input_path):
        logger.error("Input file not found: %s", input_path)
        raise FileNotFoundError(f"Input file not found: {input_path}")

    _, extension = os.path.splitext(input_path)
    ext_lower = extension.lower()

    # PDF files
    if ext_lower == '.pdf':
        logger.info("Processing PDF file...")
        # Check if PDF is searchable or needs OCR
        is_searchable = is_pdf_searchable_pypdf(input_path)
        logger.info("PDF is %s", "searchable" if is_searchable else "image-based (requires OCR)")

        if is_searchable:
            logger.info("Converting searchable PDF to DOCX")
            convert_pdf_to_docx(input_path, output_path)
        else:
            logger.info("Starting OCR process for scanned PDF")
            ocr_pdf_image_to_doc(input_path, output_path)
        logger.info("PDF to DOCX conversion completed")

    # Image files - use OCR
    elif ext_lower in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif']:
        logger.info("Processing image file with OCR: %s", ext_lower)
        ocr_pdf_image_to_doc(input_path, output_path)
        logger.info("Image to DOCX conversion completed")

    # DOCX files - just copy
    elif ext_lower in ['.docx', '.doc']:
        logger.info("File is already in Word format, no conversion needed")
        # No conversion needed, but we still need to ensure it's at output_path
        if input_path != output_path:
            import shutil
            shutil.copy2(input_path, output_path)
            logger.debug("Copied DOCX file to: %s", output_path)

    else:
        error_msg = f"Unsupported file type: {extension}. Supported: .pdf, .docx, .doc, .jpg, .jpeg, .png, .tiff, .tif, .gif"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Verify output file was created
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / 1024  # KB
        logger.info("DOCX file created successfully: %.2f KB", file_size)
    else:
        logger.error("Conversion failed - output file not found: %s", output_path)
        raise FileNotFoundError(f"Conversion failed: {output_path}")


def translate_document(
        original_path: str,
        translated_path: str,
        source_lang: str | None = None,
        target_lang: str | None = None
) -> None:
    """
    Translates word document to target_lang.
    Args:
    original_path: foreign language word document Word format
    translated_path: output english Word document Word format
    source_lang: optional source language code (e.g., 'es')
    target_lang: optional language code to translate to (e.g., 'fr')
    """
    logger.debug("Entering translate_document()")
    logger.debug("Original: %s", original_path)
    logger.debug("Translated: %s", translated_path)
    logger.debug("Source lang: %s, Target lang: %s", source_lang or 'auto', target_lang or 'en')

    if not os.path.exists(original_path):
        logger.error("Original file not found: %s", original_path)
        raise FileNotFoundError(f"File not found: {original_path}")

    # Find translator executable with intelligent fallback
    translator_info = find_translator_executable()

    if not translator_info:
        error_msg = (
            "Translator executable not found. Please ensure one of the following:\n"
            "1. Set 'translator_executable_path' in credentials/secrets.json\n"
            "2. Place GoogleTranslator project at ../GoogleTranslator/\n"
            "3. Place translate_document executable in EmailReader root directory\n"
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Unpack the tuple: (script_path, python_interpreter)
    executable_path, python_interpreter = translator_info

    # Validate Python interpreter exists
    if not python_interpreter.exists():
        logger.error("Python interpreter not found: %s", python_interpreter)
        raise FileNotFoundError(f"Python interpreter not found: {python_interpreter}")

    # Build command arguments
    arguments = ['-i', original_path, '-o', translated_path]
    if source_lang:
        arguments += ['--source', source_lang]
    if target_lang:
        arguments += ['--target', target_lang]

    # Determine if we need to invoke with Python
    if executable_path.suffix == '.py':
        command = [str(python_interpreter), str(executable_path)] + arguments
        logger.info("Using Python script for translation")
        logger.info("  Script: %s", executable_path)
        logger.info("  Python: %s", python_interpreter)
    else:
        command = [str(executable_path)] + arguments
        logger.info("Using compiled executable for translation: %s", executable_path)

    logger.debug("Translation command: %s", ' '.join(command))

    try:
        logger.info("Starting translation subprocess")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.debug("Translation stdout: %s", result.stdout if result.stdout else "(empty)")
        logger.info("Translation completed successfully")

        if os.path.exists(translated_path):
            file_size = os.path.getsize(translated_path) / 1024  # KB
            logger.debug("Translated file size: %.2f KB", file_size)
        else:
            logger.error("Translation completed but output file not found: %s", translated_path)

    except subprocess.CalledProcessError as e:
        error = f'Translation failed with exit code {e.returncode}'
        logger.error(error)
        logger.error('Command: %s', ' '.join(command))
        logger.error('Stdout: %s', e.stdout)
        logger.error('Stderr: %s', e.stderr)
        raise
    except Exception as e:
        logger.error('Unexpected error during translation: %s', e, exc_info=True)
        raise


def process_files_for_translation() -> None:
    """Process files on google drive
       for translation."""

    logger.info("="*60)
    logger.info("Starting Google Drive processing cycle")
    logger.info("="*60)

    try:
        config = load_config()
        if config is None:
            logger.error('Configuration not loaded')
            return
        url = config.get('app', {}).get('translator_url')
        if not url:
            logger.error('translator_url not specified in configuration')
            return
        # Create temp folders if not exist
        inbox_folder = os.path.join(cwd, 'inbox_temp')
        if not os.path.isdir(inbox_folder):
            os.mkdir(inbox_folder)
        completed_folder = os.path.join(cwd, 'completed_temp')
        if not os.path.isdir(completed_folder):
            os.mkdir(completed_folder)

        client_sub_folders: List[str] = ['Inbox', 'Completed']

        logger.debug("Initializing API clients")
        google_api = GoogleApi()

        # Get client list
        logger.info("Fetching client folders from Google Drive")
        translate_folder_id = get_translate_folder_id()
        if not translate_folder_id:
            logger.error(
                "Translation folder ID is not set. Aborting processing.")
            return
        clients = google_api.get_subfolders_list_in_folder(
            parent_folder_id=translate_folder_id)
        logger.info("Found %d total folders at root level", len(clients))

        # Filter for direct client folders (with email format) and company folders
        client_folders = [
            c for c in clients if '@' in c['name'] and '.' in c['name']]
        companies_folders = [
            c for c in clients if c not in client_folders]

        logger.info("Found %d direct client folders at root level", len(client_folders))
        logger.info("Found %d potential company folders", len(companies_folders))

        # Search for nested client folders inside company folders
        for company in companies_folders:
            company_name = company['name']
            company_id = company['id']
            logger.debug("Searching for nested clients in company folder: %s", company_name)

            try:
                nested_folders = google_api.get_subfolders_list_in_folder(
                    parent_folder_id=company_id)

                # Filter for client folders (with email format)
                nested_client_folders = [
                    c for c in nested_folders if '@' in c['name'] and '.' in c['name']]

                if nested_client_folders:
                    logger.info("Found %d nested client(s) in company '%s': %s",
                              len(nested_client_folders),
                              company_name,
                              ', '.join(c['name'] for c in nested_client_folders))
                    client_folders.extend(nested_client_folders)
                else:
                    logger.debug("No nested clients found in company '%s'", company_name)

            except Exception as e:
                logger.error("Error searching company folder '%s': %s", company_name, e)
                continue

        logger.info("Processing total of %d client folders (direct + nested)", len(client_folders))

        # Process each client folder
        for client in client_folders:
            client_email: str = client.get('name', '')
            client_folder_id: str | None = client.get('id', None)

            logger.info("Processing client: %s", client_email)

            # Check and create sub folders
            for sub_folder in client_sub_folders:
                if not google_api.if_folder_exist_by_name(
                        folder_name=sub_folder,
                        parent_folder_id=client_folder_id):
                    logger.debug("Creating missing subfolder: %s", sub_folder)
                    google_api.create_subfolder_in_folder(
                        parent_folder_id=client_folder_id,
                        folder_name=sub_folder
                    )
            # Get subfolder IDs
            subs = google_api.get_subfolders_list_in_folder(
                parent_folder_id=client_folder_id)
            # Find Inbox folder
            sub = next(
                filter(lambda s: s['name'] == 'Inbox', subs), None)
            if sub is None:
                logger.warning(
                    "No Inbox folder found for client: %s", client_email)
                continue
            try:
                completed_id = [sub['id']
                                for sub in subs if sub['name'] == 'Completed'][0]
                logger.debug("In-Progress folder ID: %s", completed_id)
            except IndexError:
                logger.error(
                    "Completed folder not found for client: %s",
                    client_email)
                continue
            inbox_id: str = sub['id']
            logger.debug("Inbox folder ID: %s", inbox_id)

            # Get files from inbox
            files = google_api.get_file_list_in_folder(
                parent_folder_id=inbox_id)
            logger.info("Found %d files in %s inbox", len(files), client_email)

            # Process each file
            for fl in files:
                file_name = fl['name']
                file_id = fl['id']
                # Ensure properties is a dict before accessing keys
                properties: dict[str, str] = fl.get('properties', {}) or {}
                description: str = fl.get('description', '') or ''
                if not isinstance(properties, dict):
                    properties = {}
                target_language = properties.get('target_language', None)
                source_language = properties.get('source_language', None)
                transaction_id = properties.get('transaction_id', None)

                logger.info("="*60)
                logger.info("Processing file: %s (ID: %s)", file_name, file_id)
                logger.debug("File properties: %s", properties)
                logger.debug("Source language: %s, Target language: %s",
                           source_language or 'auto', target_language or 'default')

                # CRITICAL VALIDATION: Check if transaction_id is missing
                if not transaction_id:
                    logger.error("="*60)
                    logger.error("CRITICAL ERROR: transaction_id is MISSING!")
                    logger.error("="*60)
                    logger.error("File Name: %s", file_name)
                    logger.error("File ID: %s", file_id)
                    logger.error("Client: %s", client_email)
                    logger.error("File Properties: %s", properties)
                    logger.error("")
                    logger.error("CAUSE: The file was uploaded to Google Drive Inbox WITHOUT the 'transaction_id' property.")
                    logger.error("")
                    logger.error("IMPACT:")
                    logger.error("  - File WILL be translated and uploaded to Completed folder")
                    logger.error("  - Webhook notification WILL FAIL with 422 error")
                    logger.error("  - Server cannot update transaction without transaction_id")
                    logger.error("")
                    logger.error("ACTION REQUIRED:")
                    logger.error("  1. Find the external system/API that uploads files to this Inbox folder")
                    logger.error("  2. Update that code to include 'transaction_id' in the properties dict:")
                    logger.error("     properties = {")
                    logger.error("         'source_language': source_lang,")
                    logger.error("         'target_language': target_lang,")
                    logger.error("         'transaction_id': transaction_id  # <-- ADD THIS")
                    logger.error("     }")
                    logger.error("  3. See TRANSACTION_ID_MISSING_ROOT_CAUSE_ANALYSIS.md for details")
                    logger.error("="*60)
                    logger.error("")
                    logger.warning("Continuing with file processing, but webhook will fail...")
                # Download file to temp inbox folder
                source_file_path = os.path.join(inbox_folder, file_name)
                logger.debug("Downloading to: %s", source_file_path)

                if not google_api.download_file_from_google_drive(
                        file_id=file_id,
                        file_path=source_file_path):
                    logger.error("Failed to download file: %s", file_name)
                    continue

                logger.info("File downloaded successfully")

                # IMPORTANT: Move original file from Inbox to Completed NOW
                # This prevents race conditions where multiple runs process the same file
                logger.info("MOVE original Inbox -> Completed (before translation): %s", file_name)
                moved = google_api.move_file_to_folder_id(
                    file_id=file_id,
                    dest_folder_id=completed_id
                )
                if not moved:
                    logger.error(
                        "Failed to move original file to Completed: %s - skipping",
                        file_name)
                    delete_file(source_file_path)
                    continue
                logger.info("Original file moved successfully to Completed")

                filename_without_extension, extension = os.path.splitext(
                    file_name)

                # Step 2: Convert to DOCX if needed (PDF, images, etc.)
                ext_lower = extension.lower()
                docx_for_translation = None  # Track temp DOCX file

                if ext_lower in ['.docx', '.doc']:
                    # Already in DOCX format
                    translation_source = source_file_path
                    logger.info("File is already in Word format, no conversion needed")
                else:
                    # Need to convert to DOCX first
                    logger.info("Step 2: Converting %s to DOCX for translation...", ext_lower)
                    docx_for_translation = os.path.join(
                        inbox_folder, f"{filename_without_extension}_temp.docx")
                    try:
                        convert_to_docx_for_translation(source_file_path, docx_for_translation)
                        translation_source = docx_for_translation
                    except (ValueError, FileNotFoundError, RuntimeError) as e:
                        logger.error("="*60)
                        logger.error("FILE CONVERSION FAILED - SKIPPING FILE")
                        logger.error("="*60)
                        logger.error("File: %s", file_name)
                        logger.error("Error: %s", e)
                        logger.error("="*60)
                        # Clean up downloaded file
                        delete_file(source_file_path)
                        if docx_for_translation:
                            delete_file(docx_for_translation)
                        continue

                # Step 3: Translate the DOCX file
                translated_file_name = f"{filename_without_extension}_translated.docx"
                target_file_path = os.path.join(
                    completed_folder, translated_file_name)

                logger.debug("Translation output will be: %s", target_file_path)

                step_label = "Step 3:" if docx_for_translation else "Step 2:"
                logger.info("%s Translating document...", step_label)
                try:
                    translate_document(
                        original_path=translation_source,
                        translated_path=target_file_path,
                        source_lang=source_language,
                        target_lang=target_language
                    )
                    logger.info("Translation process completed")
                except Exception as e:
                    logger.error("Translation failed: %s - skipping", e)
                    # Clean up temp files
                    delete_file(source_file_path)
                    if docx_for_translation:
                        delete_file(docx_for_translation)
                    continue

                # Upload translated file to Completed folder on google drive
                if not os.path.exists(target_file_path):
                    logger.error("Translated file does not exist: %s",
                                 target_file_path)
                    continue

                translated_size = os.path.getsize(target_file_path) / 1024  # KB
                logger.debug("Translated file size: %.2f KB", translated_size)

                logger.info("Uploading translated file to Completed folder")
                file_info = google_api.upload_file_to_google_drive(
                    file_path=target_file_path,
                    file_name=translated_file_name,
                    parent_folder_id=completed_id,
                    description=description,
                    properties=properties
                )
                completed_file_id = file_info.get('id', None)
                if not completed_file_id:
                    logger.error(
                        "Failed to upload translated file: %s", translated_file_name)
                    continue
                logger.info("Uploaded translated file successfully: %s (ID: %s)",
                            translated_file_name, completed_file_id)

                # Note: Original file was already moved to Completed earlier (before translation)
                # to prevent race conditions with concurrent runs

                # Get file URL for webhook
                file_url = google_api.get_file_web_link(completed_file_id)
                if not file_url:
                    logger.warning("Could not retrieve webViewLink for file: %s", file_name)
                    file_url = ""

                # Determine company name from folder hierarchy
                # Get parent folder of client folder
                parent_folder_id = google_api.get_file_parent_folder_id(client_folder_id)
                if parent_folder_id == translate_folder_id:
                    # Client is at root level (individual)
                    company_name = "Ind"
                    logger.debug("Client %s is individual (at root level)", client_email)
                else:
                    # Client is under a company folder
                    company_name = google_api.get_folder_name_by_id(parent_folder_id)
                    if not company_name:
                        # Fallback: check if parent name looks like email
                        company_name = "Ind"
                        logger.warning("Could not determine company name for %s, using 'Ind'", client_email)
                    else:
                        # Additional check: if parent folder name contains @ and ., it's likely individual
                        if '@' in company_name and '.' in company_name:
                            company_name = "Ind"
                            logger.debug("Parent folder %s looks like email, treating as individual", company_name)
                        else:
                            logger.debug("Client %s belongs to company: %s", client_email, company_name)

                # Send webhook notification
                data = {
                    "file_name": translated_file_name,
                    "file_url": file_url,
                    "user_email": client_email,
                    "company_name": company_name,
                    "transaction_id": transaction_id
                }
                headers = {"Content-Type": "application/json"}
                logger.info("Sending webhook notification")
                logger.debug("Webhook URL: %s", url)
                logger.debug("Webhook data: file=%s, url=%s, user=%s, company=%s, transaction_id=%s",
                           translated_file_name, file_url, client_email, company_name, transaction_id)

                try:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
                    logger.debug("Webhook response status: %d", response.status_code)

                    if response.status_code == 200:
                        logger.info("Webhook notification sent successfully for: %s", file_name)
                    elif response.status_code == 422:
                        logger.error("="*60)
                        logger.error("WEBHOOK FAILED: 422 Unprocessable Content")
                        logger.error("="*60)
                        logger.error("File: %s", file_name)
                        logger.error("Transaction ID sent: %s", transaction_id)
                        logger.error("Server Response: %s", response.text)
                        logger.error("")
                        logger.error("REASON: Server rejected the webhook because 'transaction_id' is invalid.")
                        logger.error("")
                        logger.error("Most likely causes:")
                        logger.error("  1. transaction_id is None/null (file uploaded without transaction_id property)")
                        logger.error("  2. transaction_id format is invalid")
                        logger.error("  3. transaction_id doesn't exist in the server database")
                        logger.error("")
                        logger.error("CHECK THE ERROR MESSAGE ABOVE (when file was first processed)")
                        logger.error("If you saw 'CRITICAL ERROR: transaction_id is MISSING!' then:")
                        logger.error("  - The file in Google Drive Inbox lacks the transaction_id property")
                        logger.error("  - Fix the external upload system to set transaction_id in file properties")
                        logger.error("="*60)
                    else:
                        logger.error("Webhook failed for: %s, Status: %d, Response: %s",
                                   file_name, response.status_code, response.text)
                except Exception as e:
                    logger.error("Error sending webhook for %s: %s", file_name, e, exc_info=True)

                # Clean up temp files
                logger.debug("Cleaning up temporary files")
                try:
                    if os.path.exists(source_file_path):
                        os.remove(source_file_path)
                        logger.debug("Removed source file: %s", source_file_path)
                    if os.path.exists(target_file_path):
                        os.remove(target_file_path)
                        logger.debug("Removed translated file: %s", target_file_path)
                    # Clean up temp DOCX if it was created
                    if docx_for_translation and os.path.exists(docx_for_translation):
                        os.remove(docx_for_translation)
                        logger.debug("Removed temp DOCX file: %s", docx_for_translation)
                except Exception as e:
                    logger.warning("Error cleaning up temp files: %s", e)

                logger.info("File processing completed: %s", file_name)
                logger.info("="*60)

    except Exception:
        logger.exception("Error during Google Drive processing cycle")
