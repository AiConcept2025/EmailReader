"""
Module for processing google drive - TEST VERSION
This version does NOT remove files from Inbox - tracks processing with file properties
Includes metrics collection for quality analysis
"""

import os
import time
import logging
from typing import List
from datetime import datetime


from src.email_sender import send_error_message
from src.flowise_api import FlowiseAiAPI
from src.google_drive import GoogleApi
from src.pinecone_utils import PineconeAssistant
from src.process_documents import DocProcessor
from src.utils import delete_file, build_flowise_question
from src.config import load_config, get_config_value

# Import metrics tracker if available
try:
    from src.metrics_tracker import MetricsTracker
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

type FilesFoldersDict = dict[str, str]

# Get the specific logger for this module
logger = logging.getLogger('EmailReader.GoogleDriveTest')


def process_google_drive_test() -> None:
    """
    TEST VERSION: Process all new documents from google drive without removing from Inbox
    Files are tracked via Google Drive properties to avoid reprocessing
    """
    logger.info("="*60)
    logger.info("Starting Google Drive processing cycle (TEST MODE)")
    logger.info("="*60)

    # Initialize metrics if enabled
    metrics_enabled = get_config_value('metrics.enabled', True)
    metrics_tracker = None
    if metrics_enabled and METRICS_AVAILABLE:
        metrics_tracker = MetricsTracker()
        logger.info("Metrics collection enabled")
    else:
        logger.info("Metrics collection disabled")

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
                    "No Inbox folder found for client %s - skipping", client_email)
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

                # TEST MODE: Check if already processed
                processed_timestamp = google_api.get_file_property(file_id, 'processed_at')
                if processed_timestamp:
                    logger.info(
                        "  File '%s' already processed at %s - skipping",
                        file_name, processed_timestamp
                    )
                    continue

                logger.info("")
                logger.info("-"*60)
                logger.info("Processing file %d/%d: '%s'",
                            file_idx, len(files), file_name)
                logger.info("  Client: %s", client_email)
                logger.info("  File ID: %s", file_id)
                logger.info("-"*60)

                # Start metrics collection for this file
                if metrics_tracker:
                    metrics_tracker.start_file_processing(
                        file_id=file_id,
                        file_name=file_name,
                        client_email=client_email
                    )

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
                    download_start = time.time()
                    if not google_api.download_file_from_google_drive(
                            file_id=file_id,
                            file_path=file_path):
                        logger.error(
                            "Failed to download file '%s' - skipping",
                            file_name)
                        if metrics_tracker:
                            metrics_tracker.record_error("download_failed")
                        continue

                    if metrics_tracker:
                        metrics_tracker.record_timing('download', time.time() - download_start)

                    # Process based on file type
                    logger.info(
                        ("Step 2/6: Processing document "
                         "(language detection/translation)..."))

                    processing_start = time.time()
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
                            target_lang=target_lang
                        )
                    else:
                        logger.warning(
                            "Unsupported file type '%s' - skipping", file_ext)
                        if metrics_tracker:
                            metrics_tracker.record_error("unsupported_file_type")
                        continue

                    if metrics_tracker:
                        metrics_tracker.record_timing('processing', time.time() - processing_start)

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

                    upload_start = time.time()
                    upload_result = google_api.upload_file_to_google_drive(
                        parent_folder_id=in_progress_id,
                        file_name=final_name,
                        file_path=new_file_path
                    )

                    if isinstance(upload_result, dict) and upload_result.get('name') == 'Error':
                        logger.error(
                            "Failed to upload processed file to In-Progress: %s",
                            upload_result.get('id'))
                        if metrics_tracker:
                            metrics_tracker.record_error("upload_failed")
                        continue

                    if metrics_tracker:
                        metrics_tracker.record_timing('upload', time.time() - upload_start)

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

                    flowise_start = time.time()
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
                            if metrics_tracker:
                                metrics_tracker.record_error("flowise_upload_failed")
                            continue

                        logger.info(
                            ("  Document successfully "
                             "uploaded to FlowiseAI store"))

                    if metrics_tracker:
                        metrics_tracker.record_timing('flowise_upload', time.time() - flowise_start)

                    # Create prediction using the SAME name
                    logger.info("Step 5/6: Creating FlowiseAI prediction...")
                    logger.debug("  Prediction query: %s", question)

                    prediction_start = time.time()
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
                        if metrics_tracker:
                            metrics_tracker.record_error("prediction_failed")
                        continue

                    logger.info("  Prediction created successfully")

                    if metrics_tracker:
                        metrics_tracker.record_timing('prediction', time.time() - prediction_start)

                    # Wait before finalization
                    logger.info(
                        "Step 6/6: Finalizing (marking as processed)...")
                    logger.debug(
                        "  Waiting 2 minutes for FlowiseAI processing...")
                    time.sleep(120)

                    # TEST MODE: Mark file as processed instead of moving
                    logger.info(
                        "  Marking file as processed (TEST MODE - file stays in Inbox)...")
                    current_time = datetime.now().isoformat()
                    marked = google_api.set_file_property(
                        file_id=file_id,
                        property_name='processed_at',
                        property_value=current_time
                    )

                    if not marked:
                        logger.warning(
                            "  Failed to mark file as processed - may be reprocessed next run")
                    else:
                        logger.info(
                            "  File marked as processed at %s", current_time)

                    # Clean up local files
                    logger.debug("  Cleaning up temporary local files...")
                    delete_file(new_file_path)
                    if new_file_path != original_file_path:
                        delete_file(original_file_path)
                    logger.debug("  Temporary files cleaned up")

                    logger.info("")
                    logger.info(
                        "SUCCESS: File '%s' fully processed for client %s (TEST MODE)",
                        file_name,
                        client_email)
                    logger.info("-"*60)

                    # Finalize metrics for this file
                    if metrics_tracker:
                        metrics_tracker.finalize_file_processing(success=True)

                except (IOError, OSError, ValueError) as e:
                    logger.error(
                        "Error processing file %s: %s", file_name, e,
                        exc_info=True
                    )
                    if metrics_tracker:
                        metrics_tracker.record_error(f"exception: {type(e).__name__}")
                        metrics_tracker.finalize_file_processing(success=False)
                    continue

        logger.info("Google Drive processing cycle completed (TEST MODE)")
        logger.info("="*60)

        # Save metrics report
        if metrics_tracker:
            report_path = metrics_tracker.save_report()
            logger.info("Metrics report saved to: %s", report_path)

    except Exception as e:
        logger.error(
            "Critical error in process_google_drive_test: %s", e, exc_info=True)
        raise
