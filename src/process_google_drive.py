"""
Module for processing google drive
"""

import os
import time
import logging
from typing import List, Dict

from schedule import every, repeat  # type: ignore

from src.email_sender import send_error_message
from src.flowise_api import FlowiseAiAPI
from src.google_drive import GoogleApi
from src.process_documents import DocProcessor
from src.utils import delete_file

# Import the configured logger system
import src.logger  # This ensures logger is configured

type FilesFoldersDict = dict[str, str]

# Get the specific logger for this module
logger = logging.getLogger('EmailReader.GoogleDrive')


@repeat(every(15).minutes)
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
        logger.info(f"Found {len(clients)} total folders")
        
        # Filter for client folders (with email format)
        client_folders = [c for c in clients if '@' in c['name'] and '.' in c['name']]
        logger.info(f"Processing {len(client_folders)} client folders")
        
        for client in client_folders:
            client_folder_id: str = client.get('id')
            client_email = client['name']
            
            logger.info(f"Processing client: {client_email}")
            
            # Check and create subfolders
            for sub_folder in client_sub_folders:
                if not google_api.if_folder_exist_by_name(
                        folder_name=sub_folder,
                        parent_folder_id=client_folder_id):
                    logger.debug(f"Creating missing subfolder: {sub_folder}")
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
                logger.debug(f"In-Progress folder ID: {in_progress_id}")
            except IndexError:
                logger.error(f"In-Progress folder not found for client: {client_email}")
                continue
                
            # Find Inbox folder
            sub = next(
                filter(lambda s: s['name'] == 'Inbox', subs), None)
            if sub is None:
                logger.warning(f"No Inbox folder found for client: {client_email}")
                continue
                
            inbox_id: str = sub['id']
            logger.debug(f"Inbox folder ID: {inbox_id}")
            
            # Get files from inbox
            files = google_api.get_file_list_in_folder(
                parent_folder_id=inbox_id)
            logger.info(f"Found {len(files)} files in {client_email} inbox")
            
            for fl in files:
                file_name = fl['name']
                file_id = fl['id']
                
                logger.info(f"Processing file: {file_name}")
                
                try:
                    file_path = os.path.join(document_folder, file_name)
                    _, file_ext = os.path.splitext(file_name)
                    
                    # Download file
                    logger.debug(f"Downloading file from Google Drive: {file_name}")
                    if not google_api.download_file_from_google_drive(
                            file_id=file_id,
                            file_path=file_path):
                        logger.error(f"Failed to download file: {file_name}")
                        continue
                    
                    logger.debug(f"File downloaded successfully to: {file_path}")
                    
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
                            document_folder=document_folder
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
                            document_folder=document_folder
                        )
                    else:
                        logger.warning(f"Unsupported file type: {file_ext}")
                        continue
                    
                    logger.info(f"Document processed: {new_file_name}")
                    
                    # Upload to In-Progress folder
                    logger.debug(f"Uploading to In-Progress folder: {new_file_name}")
                    upload_result = google_api.upload_file_to_google_drive(
                        parent_folder_id=in_progress_id,
                        file_name=new_file_name,
                        file_path=new_file_path
                    )
                    
                    if upload_result.get('name') == 'Error':
                        logger.error(f"Failed to upload to In-Progress: {upload_result.get('id')}")
                        continue
                        
                    # Upload original if different
                    if '+english' not in new_file_name:
                        logger.debug(f"Uploading original file: {original_file_name}")
                        google_api.upload_file_to_google_drive(
                            parent_folder_id=in_progress_id,
                            file_name=original_file_name,
                            file_path=original_file_path
                        )
                    
                    # Upload to Flowise/Pinecone
                    logger.info(f"Uploading to document store: {new_file_name}")
                    upsert_result = flowise_api.upsert_document_to_document_store(
                        doc_name=new_file_name,
                        doc_path=new_file_path
                    )
                    
                    if upsert_result.get('name') == 'Error':
                        error = upsert_result.get('error', 'Unknown error')
                        logger.error(f"Document store upload failed: {error}")
                        send_error_message(f"Upload file doc store error: {error}")
                        continue
                    
                    logger.info("Document successfully uploaded to store")
                    
                    # Create prediction
                    logger.info(f"Creating prediction for: {new_file_name}")
                    res_prediction = flowise_api.create_new_prediction(new_file_name)
                    
                    if res_prediction.get('name') == 'Error':
                        error_id = res_prediction.get('id', 'Unknown')
                        logger.error(f"Prediction creation failed: {error_id}")
                        send_error_message(f"Prediction error: {error_id}")
                        continue
                    
                    logger.info("Prediction created successfully")
                    
                    # Wait before cleanup
                    logger.debug("Waiting 2 minutes before cleanup")
                    time.sleep(120)
                    
                    # Move file to deleted folder
                    logger.info(f"Moving file to deleted folder: {file_name}")
                    result = google_api.move_file_to_deleted_folder(
                        file_id=file_id,
                        client_folder_id=client_folder_id
                    )
                    
                    if not result:
                        logger.warning("Failed to move file to deleted folder")
                    
                    # Clean up local files
                    logger.debug("Cleaning up temporary files")
                    delete_file(new_file_path)
                    if new_file_path != original_file_path:
                        delete_file(original_file_path)
                    
                    logger.info(f"Successfully completed processing: {file_name}")
                    
                except Exception as e:
                    logger.error(f"Error processing file {file_name}: {e}", exc_info=True)
                    continue
        
        logger.info("Google Drive processing cycle completed")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Critical error in process_google_drive: {e}", exc_info=True)
        raise
