"""src/process_files_for_formatting.py

Process files from Google Drive for formatting using Landing AI OCR.
This mode performs rotation detection and OCR without translation.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
import asyncio

from src.google_drive import GoogleApi
from src.config import load_config
from src.utils import delete_file
from src.ocr import OCRProviderFactory

logger = logging.getLogger('EmailReader.GoogleDrive')

cwd = os.getcwd()

google_api = GoogleApi()


def get_format_folder_id() -> str:
    """Retrieve the Google Drive folder ID for formatting files from configuration."""
    logger.debug("Entering get_format_folder_id()")

    config = load_config()
    folder_id = config.get('google_drive', {}).get('parent_folder_id', '')

    if not folder_id:
        logger.warning("No 'parent_folder_id' found in configuration")
    else:
        logger.debug("Formatting folder ID: %s", folder_id)
    return folder_id


def convert_to_docx_for_formatting(input_path: str, output_path: str) -> None:
    """
    Convert various file formats to DOCX using Landing AI OCR with rotation detection.
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

    # Apply rotation detection if enabled
    config = load_config()
    preprocessing_config = config.get('preprocessing', {})
    rotation_config = preprocessing_config.get('rotation_detection', {})
    rotation_enabled = rotation_config.get('enabled', False)

    # Track if we need to use rotated file
    file_to_process = input_path
    rotated_file = None

    if rotation_enabled and ext_lower in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif']:
        logger.info("Rotation detection is enabled - checking document orientation")
        try:
            from src.preprocessing.rotation_detector import RotationDetector

            detector = RotationDetector(rotation_config)
            angle, confidence = detector.detect_rotation(input_path)

            logger.info("Detected rotation: %d degrees (confidence: %.2f)", angle, confidence)

            if angle != 0:
                # Create rotated version
                rotated_file = input_path.replace(ext_lower, f'_rotated{ext_lower}')
                logger.info("Rotating document %d degrees before OCR", angle)
                detector.correct_rotation(input_path, rotated_file, angle)
                file_to_process = rotated_file
                logger.info("Document rotated successfully")
            else:
                logger.info("No rotation needed")

        except Exception as e:
            logger.warning("Rotation detection failed: %s - proceeding without rotation", e)
            # Continue with original file
            file_to_process = input_path

    try:
        # PDF files - process with Landing AI OCR
        if ext_lower == '.pdf':
            logger.info("Processing PDF file with Landing AI OCR...")
            _process_with_landing_ai(file_to_process, output_path)
            logger.info("Landing AI OCR PDF to DOCX conversion completed")

        # Image files - use Landing AI OCR
        elif ext_lower in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif']:
            logger.info("Processing image file with Landing AI OCR: %s", ext_lower)
            _process_with_landing_ai(file_to_process, output_path)
            logger.info("Landing AI OCR image to DOCX conversion completed")

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
            logger.error(
                "Conversion failed - output file not found: %s", output_path)
            raise FileNotFoundError(f"Conversion failed: {output_path}")

    finally:
        # Clean up rotated temp file if it was created
        if rotated_file and os.path.exists(rotated_file):
            try:
                os.remove(rotated_file)
                logger.debug("Cleaned up rotated temp file: %s", rotated_file)
            except Exception as e:
                logger.warning("Failed to clean up rotated file %s: %s", rotated_file, e)


def _process_with_landing_ai(input_file: str, output_file: str) -> None:
    """
    Process document with Landing AI OCR provider.

    Args:
        input_file: Path to input file (PDF or image)
        output_file: Path to save output DOCX file
    """
    try:
        # Load config and force Landing AI provider
        config = load_config()

        # Override OCR provider to Landing AI
        if 'ocr' not in config:
            config['ocr'] = {}

        # Temporarily override provider to landing_ai
        original_provider = config['ocr'].get('provider', 'default')
        config['ocr']['provider'] = 'landing_ai'

        logger.info("Using Landing AI OCR provider for formatting")
        ocr_provider = OCRProviderFactory.get_provider(config)

        # Restore original provider setting
        config['ocr']['provider'] = original_provider

        ocr_provider.process_document(input_file, output_file)
        logger.info("Landing AI OCR completed successfully")

    except Exception as e:
        logger.error(f"Landing AI OCR failed: {e}")
        raise RuntimeError(
            f"Landing AI OCR processing failed: {e}"
        ) from e


async def format_file(
        fl: Dict[str, str],
        client_email: str,
        inbox_folder: str,
        completed_id: str,
        completed_folder: str,
        client_folder_id: str | None,
        format_folder_id: str) -> None:
    """Process files on Google Drive for formatting with Landing AI OCR."""
    file_name = fl['name']
    file_id = fl['id']

    # Ensure properties is a dict before accessing keys
    properties: dict[str, str] = fl.get('properties', {}) or {}
    description: str = fl.get('description', '') or ''
    if not isinstance(properties, dict):
        properties = {}

    logger.info("="*60)
    logger.info("Processing file for formatting: %s (ID: %s)", file_name, file_id)
    logger.debug("File properties: %s", properties)

    # Download file to temp inbox folder
    source_file_path = os.path.join(inbox_folder, file_name)
    logger.debug("Downloading to: %s", source_file_path)

    if not google_api.download_file_from_google_drive(
            file_id=file_id,
            file_path=source_file_path):
        logger.error("Failed to download file: %s", file_name)
        return

    logger.info("File downloaded successfully")

    # IMPORTANT: Move original file from Inbox to Completed NOW
    # This prevents race conditions where multiple runs process the same file
    logger.info(
        "MOVE original Inbox -> Completed (before formatting): %s", file_name)
    moved = google_api.move_file_to_folder_id(
        file_id=file_id,
        dest_folder_id=completed_id
    )
    if not moved:
        logger.error(
            "Failed to move original file to Completed: %s - skipping",
            file_name)
        delete_file(source_file_path)
        return
    logger.info("Original file moved successfully to Completed")

    filename_without_extension, extension = os.path.splitext(file_name)

    # Convert to DOCX if needed (PDF, images, etc.)
    ext_lower = extension.lower()
    docx_for_formatting = None  # Track temp DOCX file

    if ext_lower in ['.docx', '.doc']:
        # Already in DOCX format - apply OCR to reformat
        logger.info("File is already in Word format, applying Landing AI OCR for reformatting")
        formatted_file_name = f"{filename_without_extension}_formatted.docx"
        target_file_path = os.path.join(completed_folder, formatted_file_name)

        try:
            # Still process through Landing AI for consistency
            convert_to_docx_for_formatting(source_file_path, target_file_path)
        except (ValueError, FileNotFoundError) as e:
            logger.error("File formatting failed: %s - skipping", e)
            delete_file(source_file_path)
            return
    else:
        # Need to convert to DOCX first
        logger.info("Converting %s to DOCX with Landing AI OCR...", ext_lower)
        formatted_file_name = f"{filename_without_extension}_formatted.docx"
        target_file_path = os.path.join(completed_folder, formatted_file_name)

        try:
            convert_to_docx_for_formatting(source_file_path, target_file_path)
        except (ValueError, FileNotFoundError) as e:
            logger.error("File conversion failed: %s - skipping", e)
            delete_file(source_file_path)
            return

    # Upload formatted file to Completed folder on Google Drive
    if not os.path.exists(target_file_path):
        logger.error("Formatted file does not exist: %s", target_file_path)
        return

    formatted_size = os.path.getsize(target_file_path) / 1024  # KB
    logger.debug("Formatted file size: %.2f KB", formatted_size)

    logger.info("Uploading formatted file to Completed folder")
    file_info = google_api.upload_file_to_google_drive(
        file_path=target_file_path,
        file_name=formatted_file_name,
        parent_folder_id=completed_id,
        description=description,
        properties=properties
    )
    completed_file_id = file_info.get('id', None)
    if not completed_file_id:
        logger.error(
            "Failed to upload formatted file: %s", formatted_file_name)
        return
    logger.info("Uploaded formatted file successfully: %s (ID: %s)",
                formatted_file_name, completed_file_id)

    # Clean up temp files
    logger.debug("Cleaning up temporary files")
    try:
        if os.path.exists(source_file_path):
            os.remove(source_file_path)
            logger.debug("Removed source file: %s", source_file_path)
        if os.path.exists(target_file_path):
            os.remove(target_file_path)
            logger.debug("Removed formatted file: %s", target_file_path)
    except Exception as e:
        logger.warning("Error cleaning up temp files: %s", e)

    logger.info("File formatting completed: %s", file_name)
    logger.info("="*60)


def process_files_for_formatting() -> None:
    """Process files on Google Drive for formatting using Landing AI OCR."""

    logger.info("="*60)
    logger.info("Starting Google Drive formatting cycle")
    logger.info("="*60)

    try:
        config = load_config()
        if config is None:
            logger.error('Configuration not loaded')
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

        # Get client list
        logger.info("Fetching client folders from Google Drive")
        format_folder_id = get_format_folder_id()
        if not format_folder_id:
            logger.error(
                "Formatting folder ID is not set. Aborting processing.")
            return
        clients = google_api.get_subfolders_list_in_folder(
            parent_folder_id=format_folder_id)
        logger.info("Found %d total folders at root level", len(clients))

        # Filter for direct client folders (with email format)
        # and company folders
        client_folders = [
            c for c in clients if '@' in c['name'] and '.' in c['name']]
        companies_folders = [
            c for c in clients if c not in client_folders]

        logger.info("Found %d direct client folders at root level",
                    len(client_folders))
        logger.info("Found %d potential company folders",
                    len(companies_folders))

        # Search for nested client folders inside company folders
        for company in companies_folders:
            company_name = company['name']
            company_id = company['id']
            logger.debug(
                "Searching for nested clients in company folder: %s",
                company_name)

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
                    logger.debug(
                        "No nested clients found in company '%s'",
                        company_name)

            except Exception as e:
                logger.error(
                    "Error searching company folder '%s': %s", company_name, e)
                continue

        logger.info(
            "Processing total of %d client folders (direct + nested)",
            len(client_folders))

        # Process each client folder
        for client in client_folders:
            client_email: str = client.get('name', '')
            client_folder_id: str = client.get('id')

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
                logger.debug("Completed folder ID: %s", completed_id)
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
                asyncio.run(format_file(
                    fl,
                    client_email,
                    inbox_folder,
                    completed_id,
                    completed_folder,
                    client_folder_id,
                    format_folder_id))
    except Exception:
        logger.exception("Error during Google Drive formatting cycle")
