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
from src.pinecone_utils import PineconeAssistant
from src.process_documents import DocProcessor
from src.file_utils import delete_file, build_flowise_question
from src.config import load_config

# Import the configured logger system
# import src.logger  # This ensures logger is configured

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
        config = load_config()
        use_pinecone = config.get('use_pinecone')
        if use_pinecone:
            logger.warning(
                ("Pinecone integration is deprecated and will "
                 "be removed in future versions.")
            )
            pinecone_assistant = PineconeAssistant()

        client_sub_folders: List[str] = ['Inbox', 'In-Progress', 'Temp']
        cwd = os.getcwd()

        logger.debug("Initializing API clients")
        google_api = GoogleApi()
        flowise_api = FlowiseAiAPI()

        document_folder = os.path.join(cwd, 'data', "documents")
        doc_processor = DocProcessor(document_folder)

        # Get client list
        logger.info("Fetching client folders from Google Drive")

        # Log root folder ID
        root_folder_id = google_api.parent_folder_id
        logger.info("Root folder ID: %s", root_folder_id)

        clients = google_api.get_subfolders_list_in_folder()
        logger.info("Found %d total folders at root level", len(clients))

        # Filter for direct client folders
        # (with email format) and company folders
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
                        "No nested clients found in company '%s'", company_name)

            except Exception as e:
                logger.error(
                    "Error searching company folder '%s': %s", company_name, e)
                continue

        logger.info(
            "Processing total of %d client folders (direct + nested)", len(client_folders))

        for idx, client in enumerate(client_folders, 1):
            client_folder_id: str | None = client.get('id', None)
            client_name_raw = client['name']
            # Derive pure email token from folder name (handles cases
            # like "Display Name+email")
            _tokens = client_name_raw.split('+')
            client_email = next(
                (t for t in _tokens if '@' in t), client_name_raw)

            logger.info("")
            logger.info("="*60)
            logger.info("Processing client %d/%d: %s", idx,
                        len(client_folders), client_email)
            logger.info("  Client folder ID: %s", client_folder_id)
            logger.info("="*60)

            # Check and create sub folders
            logger.debug("Verifying required subfolders: %s",
                         ', '.join(client_sub_folders))
            for sub_folder in client_sub_folders:
                if not google_api.if_folder_exist_by_name(
                        folder_name=sub_folder,
                        parent_folder_id=client_folder_id):
                    logger.info(
                        "Creating missing subfolder '%s' for client %s", sub_folder, client_email)
                    google_api.create_subfolder_in_folder(
                        parent_folder_id=client_folder_id,
                        folder_name=sub_folder
                    )
                else:
                    logger.debug("  Subfolder exists: '%s'", sub_folder)

            # Get subfolder IDs
            logger.debug(
                "Retrieving subfolder IDs for client %s", client_email)
            subs = google_api.get_subfolders_list_in_folder(
                parent_folder_id=client_folder_id)

            # Find In-Progress folder
            try:
                in_progress_id = [sub['id']
                                  for sub in subs if sub['name'] == 'In-Progress'][0]
                logger.debug("  In-Progress folder ID: %s", in_progress_id)
            except IndexError:
                logger.error(
                    "In-Progress folder not found for client %s - skipping",
                    client_email)
                continue

            # Find Inbox folder
            sub = next(
                filter(lambda s: s['name'] == 'Inbox', subs), None)
            if sub is None:
                logger.warning(
                    "No Inbox folder found for client %s - skipping",
                    client_email)
                continue

            inbox_id: str = sub['id']
            logger.debug("  Inbox folder ID: %s", inbox_id)

            # Get files from inbox
            logger.info("Checking Inbox for new files...")
            files = google_api.get_file_list_in_folder(
                parent_folder_id=inbox_id)

            if len(files) == 0:
                logger.info("  No files found in Inbox")
                continue
            else:
                logger.info("  Found %d file(s) in Inbox", len(files))
                if logger.isEnabledFor(logging.DEBUG):
                    file_list = [f"'{f['name']}'" for f in files[:3]]
                    if len(files) > 3:
                        file_list.append(f"... and {len(files) - 3} more")
                    logger.debug("    Files: %s", ', '.join(file_list))

            for file_idx, fl in enumerate(files, 1):
                file_name = fl['name']
                file_id = fl['id']
                metadata = fl.get('metadata', {})

                logger.info("")
                logger.info("-"*60)
                logger.info("Processing file %d/%d: '%s'",
                            file_idx, len(files), file_name)
                logger.info("  Client: %s", client_email)
                logger.info("  File ID: %s", file_id)
                logger.info("-"*60)

                try:
                    file_path = os.path.join(document_folder, file_name)
                    _, file_ext = os.path.splitext(file_name)

                    logger.debug("File extension: %s", file_ext)

                    # Optional target language from Drive appProperties
                    target_lang = google_api.get_file_app_property(
                        file_id, 'targetLanguage')
                    if target_lang:
                        logger.info(
                            "Target language specified: %s", target_lang)

                    # Download file
                    logger.info(
                        "Step 1/6: Downloading file from Google Drive...")
                    if not google_api.download_file_from_google_drive(
                            file_id=file_id,
                            file_path=file_path):
                        logger.error(
                            "Failed to download file '%s' - skipping",
                            file_name)
                        continue

                    # Process based on file type
                    logger.info(
                        ("Step 2/6: Processing document "
                         "(language detection/translation)..."))
                    if file_ext.lower() in ['.doc', '.docx']:
                        logger.info("  Document type: Word document")
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
                        logger.info("  Document type: PDF")
                        (
                            new_file_path,
                            new_file_name,
                            original_file_name,
                            original_file_path
                        ) = doc_processor.convert_pdf_file_to_word(
                            client=client_email,
                            file_name=file_name,
                            document_folder=document_folder,
                            target_lang=target_lang,
                            metadata=metadata
                        )
                    else:
                        logger.warning(
                            "Unsupported file type '%s' - skipping", file_ext)
                        continue

                    logger.info("  Processing complete: %s", new_file_name)

                    # Upload to In-Progress folder
                    # Build final name: email + rhs
                    # (new_file_name already has rhs now)
                    rhs = new_file_name
                    final_name = f"{client_email}+{rhs}"
                    logger.info(("Step 3/6: Uploading processed file to"
                                 " In-Progress folder..."))
                    logger.debug("  Target folder ID: %s", in_progress_id)
                    logger.debug("  Final file name: %s", final_name)
                    upload_result = google_api.upload_file_to_google_drive(
                        parent_folder_id=in_progress_id,
                        file_name=final_name,
                        file_path=new_file_path
                    )

                    if isinstance(upload_result, dict) and upload_result.get(
                            'name') == 'Error':
                        logger.error(
                            "Failed to upload processed file to In-Progress: %s",
                            upload_result.get('id'))
                        continue

                    # Upload original if different
                    if '+english' not in new_file_name:
                        logger.info(
                            "  Also uploading original (non-English) file...")
                        logger.debug("    Original file name: %s",
                                     original_file_name)
                        logger.debug("    Target folder ID: %s",
                                     in_progress_id)
                        google_api.upload_file_to_google_drive(
                            parent_folder_id=in_progress_id,
                            file_name=f"{client_email}+{original_file_name}",
                            file_path=original_file_path
                        )

                    # Build Flowise name once and use identically for doc store
                    # and prediction
                    # Build Flowise/doc store name as: email+<rhs>
                    question = build_flowise_question(client_email, rhs)
                    logger.info(
                        "Step 4/6: Uploading to FlowiseAI document store...")
                    logger.debug("  Document identifier: %s", question)

                    # Build metadata from Google Drive file object
                    metadata = {
                        "client_email": client_email,
                        "file_id": file_id,
                        "original_filename": file_name,
                        "mime_type": fl.get('mimeType', ''),
                        "description": fl.get('description', ''),
                    }

                    # Add any custom properties from Google Drive
                    if 'properties' in fl:
                        metadata.update(fl['properties'])

                    # Add target language if available
                    if target_lang:
                        metadata['target_language'] = target_lang

                    logger.debug("  Metadata: %s", metadata)

                    if use_pinecone:
                        logger.info(
                            "  Uploading file to Pinecone Assistant...")
                        pinecone_file_id = pinecone_assistant.upload_file(
                            file_path=new_file_path,
                            metadata=metadata
                        )
                        logger.info(
                            "  File uploaded to Pinecone with file ID: %s",
                            pinecone_file_id)
                    else:
                        upsert_result = flowise_api.upsert_document_to_document_store(
                            doc_name=question,
                            doc_path=new_file_path,
                            metadata=metadata
                        )

                        logger.debug(
                            "  Document store response: %s", upsert_result)
                        if upsert_result.get('name') == 'Error':
                            error = upsert_result.get('error', 'Unknown error')
                            logger.error(
                                "Document store upload failed: %s", error)
                            send_error_message(
                                f"Upload file doc store error: {error}")
                            continue

                        logger.info(
                            ("  Document successfully "
                             "uploaded to FlowiseAI store"))

                    # Create prediction using the SAME name
                    logger.info("Step 5/6: Creating FlowiseAI prediction...")
                    logger.debug("  Prediction query: %s", question)
                    res_prediction = flowise_api.create_new_prediction(
                        question)
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
                        logger.debug("  Prediction response: %s", compact)
                    else:
                        logger.debug("  Prediction response: %s",
                                     res_prediction)
                    if res_prediction.get('name') == 'Error':
                        error_id = res_prediction.get('id', 'Unknown')
                        logger.error(
                            "Prediction creation failed: %s", error_id)
                        send_error_message(f"Prediction error: {error_id}")
                        continue

                    logger.info("  Prediction created successfully")

                    # Wait before cleanup
                    logger.info(
                        ("Step 6/6: Finalizing (moving original "
                         "file and cleanup)..."))
                    logger.debug(
                        "  Waiting 2 minutes for FlowiseAI processing...")
                    time.sleep(120)

                    # Move original file from Inbox to In-Progress folder
                    logger.info(
                        "  Moving original file from Inbox to In-Progress...")
                    logger.debug("  From folder ID: %s", inbox_id)
                    logger.debug("  To folder ID: %s", in_progress_id)
                    moved = google_api.move_file_to_folder_id(
                        file_id=file_id,
                        dest_folder_id=in_progress_id
                    )

                    if not moved:
                        logger.warning(
                            ("  Failed to move original file "
                             "from Inbox to In-Progress"))

                    # Clean up local files
                    logger.debug("  Cleaning up temporary local files...")
                    delete_file(new_file_path)
                    if new_file_path != original_file_path:
                        delete_file(original_file_path)
                    logger.debug("  Temporary files cleaned up")

                    logger.info("")
                    logger.info(
                        "SUCCESS: File '%s' fully processed for client %s",
                        file_name,
                        client_email)
                    logger.info("-"*60)

                except (IOError, OSError, ValueError) as e:
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
