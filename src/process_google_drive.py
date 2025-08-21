"""
Module for processing google drive
"""

import os
import time
import logging
from typing import List


from src.email_sender import send_error_message
from src.flowise_api import FlowiseAiAPI
from src.google_drive import GoogleApi
from src.process_documents import DocProcessor
from src.utils import delete_file, build_flowise_question

# Import the configured logger system
import src.logger  # This ensures logger is configured

type FilesFoldersDict = dict[str, str]

# Get the specific logger for this module
logger = logging.getLogger('EmailReader.GoogleDrive')


def process_google_drive() -> None:
    """
    Process all new documents from google drive with enhanced logging
    """
    logger.info("="*60)
    logger.info("Starting Google Drive processing cycle")
    logger.info("="*60)

    try:
        client_sub_folders: List[str] = ['Inbox', 'In-Progress', 'Temp']
        cwd = os.getcwd()

        logger.debug("Initializing API clients")
        google_api = GoogleApi()
        flowise_api = FlowiseAiAPI()

        document_folder = os.path.join(cwd, 'data', "documents")
        doc_processor = DocProcessor(document_folder)

        # Get client list
        logger.info("Fetching client folders from Google Drive")
        clients = google_api.get_subfolders_list_in_folder()
        logger.info("Found %d total folders", len(clients))

        # Filter for client folders (with email format)
        client_folders = [
            c for c in clients if '@' in c['name'] and '.' in c['name']]
        logger.info("Processing %d client folders", len(client_folders))

        for client in client_folders:
            client_folder_id: str = client.get('id')
            client_name_raw = client['name']
            # Derive pure email token from folder name (handles cases like "Display Name+email")
            _tokens = client_name_raw.split('+')
            client_email = next((t for t in _tokens if '@' in t), client_name_raw)

            logger.info("Processing client: %s", client_email)

            # Check and create subfolders
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

            # Find In-Progress folder
            try:
                in_progress_id = [sub['id']
                                  for sub in subs if sub['name'] == 'In-Progress'][0]
                logger.debug("In-Progress folder ID: %s", in_progress_id)
            except IndexError:
                logger.error(
                    "In-Progress folder not found for client: %s",
                    client_email)
                continue

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

            for fl in files:
                file_name = fl['name']
                file_id = fl['id']

                logger.info("Processing file: %s", file_name)

                try:
                    file_path = os.path.join(document_folder, file_name)
                    _, file_ext = os.path.splitext(file_name)

                    # Optional target language from Drive appProperties
                    target_lang = google_api.get_file_app_property(
                        file_id, 'targetLanguage')

                    # Download file
                    logger.info(
                        "DOWNLOAD original: id=%s name=%s -> %s",
                        file_id,
                        file_name,
                        file_path,
                    )
                    if not google_api.download_file_from_google_drive(
                            file_id=file_id,
                            file_path=file_path):
                        logger.error("Failed to download file: %s", file_name)
                        continue

                    logger.info("DOWNLOAD OK: %s", file_path)

                    # Process based on file type
                    if file_ext.lower() in ['.doc', '.docx']:
                        logger.debug("Processing as Word document")
                        (
                            new_file_path,
                            new_file_name,
                            original_file_name,
                            original_file_path
                        ) = doc_processor.process_word_file(
                            client=client_email,
                            file_name=file_name,
                            document_folder=document_folder,
                            target_lang=target_lang
                        )
                    elif file_ext.lower() == '.pdf':
                        logger.debug("Processing as PDF document")
                        (
                            new_file_path,
                            new_file_name,
                            original_file_name,
                            original_file_path
                        ) = doc_processor.convert_pdf_file_to_word(
                            client=client_email,
                            file_name=file_name,
                            document_folder=document_folder,
                            target_lang=target_lang
                        )
                    else:
                        logger.warning("Unsupported file type: %s", file_ext)
                        continue

                    logger.info("Processed file (temp): %s", new_file_name)

                    # Upload to In-Progress folder
                    # Build final name: email + rhs (new_file_name already has rhs now)
                    rhs = new_file_name
                    final_name = f"{client_email}+{rhs}"
                    logger.info("UPLOAD to In-Progress: %s", final_name)
                    upload_result = google_api.upload_file_to_google_drive(
                        parent_folder_id=in_progress_id,
                        file_name=final_name,
                        file_path=new_file_path
                    )

                    if isinstance(upload_result, dict) and upload_result.get('name') == 'Error':
                        logger.error(
                            "Failed to upload to In-Progress: %s",
                            upload_result.get('id'))
                        continue

                    # Upload original if different
                    if '+english' not in new_file_name:
                        logger.debug(
                            "Uploading original file: %s", original_file_name)
                        google_api.upload_file_to_google_drive(
                            parent_folder_id=in_progress_id,
                            file_name=f"{client_email}+{original_file_name}",
                            file_path=original_file_path
                        )

                    # Build Flowise name once and use identically for doc store and prediction
                    # Build Flowise/doc store name as: email+<rhs>
                    question = build_flowise_question(client_email, rhs)
                    logger.info("DOC STORE upload name: %s", question)
                    upsert_result = flowise_api.upsert_document_to_document_store(
                        doc_name=question,
                        doc_path=new_file_path
                    )

                    logger.debug("DOC STORE response: %s", upsert_result)
                    if upsert_result.get('name') == 'Error':
                        error = upsert_result.get('error', 'Unknown error')
                        logger.error("Document store upload failed: %s", error)
                        send_error_message(
                            f"Upload file doc store error: {error}")
                        continue

                    logger.info("Document successfully uploaded to store")

                    # Create prediction using the SAME name
                    logger.info("PREDICTION send: %s", question)
                    res_prediction = flowise_api.create_new_prediction(question)
                    # Limit long 'text' fields to 60 chars for logging clarity
                    if isinstance(res_prediction, dict):
                        text_val = res_prediction.get('text')
                        if isinstance(text_val, str) and len(text_val) > 60:
                            text_val = text_val[:60] + '…'
                        compact = {
                            'name': res_prediction.get('name'),
                            'id': res_prediction.get('id'),
                            'text': text_val
                        }
                        logger.info("PREDICTION response: %s", compact)
                    else:
                        logger.info("PREDICTION response: %s", res_prediction)
                    if res_prediction.get('name') == 'Error':
                        error_id = res_prediction.get('id', 'Unknown')
                        logger.error(
                            "Prediction creation failed: %s", error_id)
                        send_error_message(f"Prediction error: {error_id}")
                        continue

                    logger.info("Prediction created successfully")

                    # Wait before cleanup
                    logger.debug("Waiting 2 minutes before cleanup")
                    time.sleep(120)

                    # Move original file from Inbox to In-Progress folder
                    logger.info("MOVE original Inbox -> In-Progress: %s", file_name)
                    moved = google_api.move_file_to_folder_id(
                        file_id=file_id,
                        dest_folder_id=in_progress_id
                    )

                    if not moved:
                        logger.warning("Failed to move file to In-Progress")
                    # Clean up local files
                    logger.debug("Cleaning up temporary files")
                    delete_file(new_file_path)
                    if new_file_path != original_file_path:
                        delete_file(original_file_path)

                    logger.info(
                        "Successfully completed processing: %s", file_name)

                except Exception as e:
                    logger.error(
                        "Error processing file %s: %s", file_name, e,
                        exc_info=True
                    )
                    continue

        logger.info("Google Drive processing cycle completed")
        logger.info("="*60)

    except Exception as e:
        logger.error(
            "Critical error in process_google_drive: %s", e, exc_info=True)
        raise
