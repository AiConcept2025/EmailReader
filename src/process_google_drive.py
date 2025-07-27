"""
Module for processing google drive
"""

import os
import time
from typing import List, Dict

from schedule import every, repeat  # type: ignore

from src.email_sender import send_error_message
from src.flowise_api import FlowiseAiAPI
from src.google_drive import GoogleApi
from src.logger import logger
from src.process_documents import DocProcessor
from src.utils import delete_file

type FilesFoldersDict = dict[str, str]


@repeat(every(15).minutes)
def process_google_drive() -> None:
    """
    Process all new documents from google drive
    """
    logger.info('Start google drive processing')

    client_sub_folders: List[str] = ['inbox', 'incoming', 'temp']
    cwd = os.getcwd()
    google_api = GoogleApi()
    flowise_api = FlowiseAiAPI()

    document_folder = os.path.join(cwd, 'data', "documents")
    doc_processor = DocProcessor(document_folder)
    # Get client list
    clients = google_api.get_subfolders_list_in_folder()
    # Check if each client folder have sub folders
    # inbox - for new documents
    # incoming - for docs sent to flowise and original files
    for client in [c for c in clients
                   if '@' in c['name'] and '.' in c['name']]:
        client_folder_id: str = client.get('id')  # type: ignore
        for sub_folder in client_sub_folders:
            if not google_api.if_folder_exist_by_name(
                    folder_name=sub_folder,
                    parent_folder_id=client_folder_id):
                google_api.create_subfolder_in_folder(
                    parent_folder_id=client_folder_id,
                    folder_name=sub_folder
                )
        # Check for new files in inbox
        client_folder_id = client.get('id')  # type: ignore
        client_email = client['name']  # Client folder ID's
        subs = google_api.get_subfolders_list_in_folder(
            parent_folder_id=client_folder_id)
        incoming_id = [sub['id']
                       for sub in subs if sub['name'] == 'incoming'][0]
        sub = next(
            filter(lambda s: s['name'] == 'inbox', subs), None)
        if sub is None:
            continue
        inbox_id: str = sub['id']
        files = google_api.get_file_list_in_folder(
            parent_folder_id=inbox_id)
        for fl in files:
            file_name = fl['name']
            file_id = fl['id']
            file_path = os.path.join(document_folder, file_name)
            _, file_ext = os.path.splitext(file_name)
            # Download new file from inbox of client on google
            # drive to local folder
            if not google_api.download_file_from_google_drive(
                    file_id=file_id,
                    file_path=file_path):
                continue
            # Check if file is word document file
            if file_ext == '.doc' or file_ext == '.docx':
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
            elif file_ext == '.pdf':
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
                continue
            # upload files to google drive incoming folder
            # original file and translated file if exists
            google_api.upload_file_to_google_drive(
                parent_folder_id=incoming_id,
                file_name=new_file_name,
                file_path=new_file_path, )
            if '+english' not in new_file_name:
                google_api.upload_file_to_google_drive(
                    parent_folder_id=incoming_id,
                    file_name=original_file_name,
                    file_path=original_file_path, )

            # Upload to doc store
            logger.info('Upload to doc store: %s', new_file_name)
            upsert_result: Dict[object, object] = (
                flowise_api.
                upsert_document_to_document_store(
                    doc_name=new_file_name,
                    doc_path=new_file_path
                ))
            if upsert_result.get('name') == 'Error':
                error = upsert_result.get('error', 'Error')
                send_error_message(
                    f"Upload file doc store error: {error}")
                continue
            # run prediction
            print(f'Upload to prediction: {new_file_name}')
            res_prediction = flowise_api.create_new_prediction(
                new_file_name)
            if res_prediction.get('name') == 'Error':
                send_error_message(
                    f"Prediction error: {res_prediction.get('id')}")
                continue
            # Wait 2 min
            time.sleep(120)
            # Delete file from inbox
            print(
                ("Attempting to delete file: "
                    f"{file_name} (ID: {file_id})"))
            result = google_api.move_file_to_deleted_folder(
                file_id=file_id)
            if result:
                print("Delete failed - trying alternative approach...")
                # You could try moving to a "deleted" folder instead
            # Remove files from temp document folder
            delete_file(new_file_path)
            if new_file_path != original_file_path:
                delete_file(original_file_path)
            logger.info('Finish: %s', file_name)
