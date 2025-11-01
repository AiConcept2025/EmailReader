"""src/process_files_for_translation.py"""

import os
import subprocess
from pathlib import Path
import logging
from typing import List
from src.google_drive import GoogleApi
from src.utils import read_json_secret_file

logger = logging.getLogger('EmailReader.GoogleDrive')

cwd = os.getcwd()


def get_translate_folder_id() -> str:
    """Retrieve the Google Drive folder ID for
    translation files from configuration."""

    cfg_path = os.path.join('credentials', 'secrets.json')
    cfg = read_json_secret_file(cfg_path) or {}
    folder_id = cfg.get('parent_folder_id', '')
    if not folder_id:
        logger.warning("No 'parent_folder_id' found in configuration.")
    return folder_id


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
    target_lang: optional language code to translate to (e.g., 'fr')
    """
    executable_path = Path(os.path.join(
        os.getcwd(), "translate_document"))
    arguments = ['-i', original_path, '-o', translated_path]
    if source_lang:
        arguments += ['--source', source_lang]
    if target_lang:
        arguments += ['--target', target_lang]

    command = [str(executable_path)] + arguments  # Convert Path to string
    try:
        subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        error = f'Error executing command: {e} Stdout: {e.stdout}, Stderr: {e.stderr}'
        logger.error(error)


def process_files_for_translation() -> None:
    """Process files on google drive
       for translation."""

    logger.info("="*60)
    logger.info("Starting Google Drive processing cycle")
    logger.info("="*60)

    try:
        # Create temp folders if not exist
        inbox_folder = os.path.join(cwd, 'inbox_temp')
        if not os.path.isdir(inbox_folder):
            os.mkdir(inbox_folder)
        processed_folder = os.path.join(cwd, 'processed_temp')
        if not os.path.isdir(processed_folder):
            os.mkdir(processed_folder)

        client_sub_folders: List[str] = ['Inbox', 'Processed']

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
        logger.info("Found %d total folders", len(clients))

        # Filter for client folders (with email format)
        client_folders = [
            c for c in clients if '@' in c['name'] and '.' in c['name']]
        companies_folders = [
            c for c in clients if c not in client_folders]
        logger.info("Processing %d client folders", len(client_folders))

        # Process each client folder
        for client in client_folders:
            client_folder_id: str | None = client.get('id', None)
            client_name_raw = client['name']
            # Derive pure email token from folder name (handles cases
            # like "Display Name+email")
            _tokens = client_name_raw.split('+')
            client_email = next(
                (t for t in _tokens if '@' in t), client_name_raw)

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
                properties = fl.get('properties', {}) or {}
                if not isinstance(properties, dict):
                    properties = {}
                target_language = properties.get('target_language', None)
                source_language = properties.get('source_language', None)
                logger.info("Processing file: %s", file_name)
                # Download file to temp inbox folder
                source_file_path = os.path.join(inbox_folder, file_name)
                if not google_api.download_file_from_google_drive(
                        file_id=file_id,
                        file_path=source_file_path):
                    logger.error("Failed to download file: %s", file_name)
                    continue
                target_file_path = os.path.join(processed_folder, file_name)

                translate_document(
                    original_path=source_file_path,
                    translated_path=target_file_path,
                    source_lang=source_language,
                    target_lang=target_language
                )

    except Exception:
        logger.exception("Error during Google Drive processing cycle")
