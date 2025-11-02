"""src/process_files_for_translation.py"""

import logging
import os
import subprocess
from pathlib import Path
from typing import List

import requests

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
        secrets = read_json_secret_file('credentials/secrets.json')
        if secrets is None:
            logger.error(
                'secrets not specified in secrets.json')
            return
        url = secrets.get('translator_url')
        if not url:
            logger.error(
                'Translator_url not specified in secrets.json')
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
        logger.info("Found %d total folders", len(clients))

        # Filter for client folders (with email format)
        client_folders = [
            c for c in clients if '@' in c['name'] and '.' in c['name']]
        companies_folders = [
            c for c in clients if c not in client_folders]
        logger.info("Processing %d client folders", len(client_folders))

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
                logger.info("Processing file: %s", file_name)
                # Download file to temp inbox folder
                source_file_path = os.path.join(inbox_folder, file_name)
                if not google_api.download_file_from_google_drive(
                        file_id=file_id,
                        file_path=source_file_path):
                    logger.error("Failed to download file: %s", file_name)
                    continue
                filename_without_extension, extension = os.path.splitext(
                    file_name)
                translated_file_name = f"{filename_without_extension}_translated{extension}"
                target_file_path = os.path.join(
                    completed_folder, translated_file_name)

                translate_document(
                    original_path=source_file_path,
                    translated_path=target_file_path,
                    source_lang=source_language,
                    target_lang=target_language
                )

                # Upload translated file to Completed folder on google drive
                if not os.path.exists(target_file_path):
                    logger.error("The file %s does not exist.",
                                 target_file_path)
                    continue

                file_info = google_api.upload_file_to_google_drive(
                    file_path=target_file_path,
                    file_name=file_name,
                    parent_folder_id=completed_id,
                    description=description,
                    properties=properties
                )
                completed_file_id = file_info.get('id', None)
                if not completed_file_id:
                    logger.error(
                        "Failed to upload translated file: %s", file_name)
                    continue
                logger.info("Uploaded translated file: %s, id: %s",
                            file_name, completed_file_id)
                # Move original file from Inbox to Completed folder
                logger.info(
                    "MOVE original Inbox -> Completed: %s", file_name)
                moved = google_api.move_file_to_folder_id(
                    file_id=file_id,
                    dest_folder_id=completed_id
                )
                if not moved:
                    logger.error(
                        "Failed to move original file to Completed: %s",
                        file_name)
                    continue

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
                    "company_name": company_name
                }
                headers = {"Content-Type": "application/json"}
                logger.info("Sending webhook: file=%s, url=%s, user=%s, company=%s",
                           translated_file_name, file_url, client_email, company_name)
                response = requests.post(url, json=data, headers=headers)
                if response.status_code == 200:
                    logger.info(
                        "Successfully submitted data for file: %s", file_name)
                else:
                    logger.error("Failed to submit data for file: %s, Status Code: %d",
                                 file_name, response.status_code)
                # Clean up temp files
                os.remove(source_file_path)
                os.remove(target_file_path)

    except Exception:
        logger.exception("Error during Google Drive processing cycle")
