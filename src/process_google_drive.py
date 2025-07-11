"""
Module for processing google drive
"""

import os
import time
from typing import Dict, List, NamedTuple

from schedule import every, repeat

from src.email_sender import send_error_message
from src.flowise_api import FlowiseAiAPI
from src.google_drive import FileFolder, GoogleApi
from src.logger import logger
from src.process_documents import DocProcessor
from src.utils import copy_file, delete_file

type FilesFoldersDict = dict[str, str]

# @repeat(every(2).hours)


def process_google_drive():
    """
    Process all new documents from google drive
    """
    logger.info('Start google drive processing')

    client_sub_folders: List[str] = ['inbox', 'incoming', 'temp']
    cwd = os.getcwd()
    google_api = GoogleApi()
    flowise_api = FlowiseAiAPI()
    document_folder = os.path.join(cwd, 'data', "documents")
    docProcessor = DocProcessor(document_folder)
    # Get client list
    clients = google_api.get_folders_list()
    # Check if each client folder have sub folders
    # inbox - for new documents
    # temp - for temp doc
    # incoming - for docs sent to flowise
    for client in clients:
        client_folder_id = client.get('id')
        for sub_folder in client_sub_folders:
            if not google_api.if_folder_exist_by_name(
                    folder_name=sub_folder,
                    parent_folder_id=client_folder_id):
                google_api.create_subfolder_in_folder(
                    parent_folder_id=client_folder_id,
                    folder_name=sub_folder
                )
    time.sleep(20)
    # Check for new files in inbox
    for client in clients:
        client_folder_id = client.get('id')
        client_email = client['name']  # Client folder ID's
        subs = google_api.get_folders_list(parent_folder_id=client_folder_id)
        temp_id = [sub['id'] for sub in subs if sub['name'] == 'temp'][0]
        incoming_id = [sub['id']
                       for sub in subs if sub['name'] == 'incoming'][0]

        for sub in subs:
            if sub['name'] == 'inbox':
                inbox_id = sub['id']
                files = google_api.get_file_list_in_folder1(
                    parent_folder_id=inbox_id)
                for fl in files:
                    file_name = fl['name']
                    file_id = fl['id']
                    file_path = os.path.join(document_folder, file_name)
                    _, file_ext = os.path.splitext(file_name)
                    # Download new file from inbox of client on google drive to local folder
                    google_api.file_download(
                        file_id=file_id, file_path=file_path)
                    # Check if file is word document file
                    if file_ext == '.doc' or file_ext == '.docx':
                        doc_path_name, doc_name, original_file_name, original_file_path = docProcessor.process_word_file(
                            client=client_email,
                            file_name=file_name,
                            document_folder=document_folder
                        )
                        # upload files to google drive incoming folder
                        # original file and translated file if exists
                        google_api.upload_file_to_google_drive(
                            parent_folder_id=incoming_id,
                            file_name=doc_name,
                            file_path=doc_path_name, )
                        if '+english' not in doc_name:
                            google_api.upload_file_to_google_drive(
                                parent_folder_id=incoming_id,
                                file_name=original_file_name,
                                file_path=original_file_path, )

                        # Temp
                        temp_file: object | Dict[str, object] = google_api.upload_file_to_google_drive(
                            parent_folder_id=temp_id,
                            file_name=doc_name,
                            file_path=doc_path_name, )
                        temp_file_id = temp_file.get('id')
                        # Upload to doc store
                        print(f'Upload to doc store: {doc_name}')
                        res_doc_store: Dict[object, object] = flowise_api.upsert_document_to_document_store(
                            doc_name=doc_name, doc_path=doc_path_name)
                        if res_doc_store.get('name') == 'Error':
                            error = res_doc_store.get('error', 'Error')
                            send_error_message(
                                f"Upload file doc store error: {error}")
                            return
                        # run prediction
                        print(f'Upload to prediction: {doc_name}')
                        res_prediction = flowise_api.create_new_prediction(
                            doc_name)
                        if res_prediction.get('name') == 'Error':
                            send_error_message(
                                f"Prediction error: {res_prediction.get('id')}")
                            return  # TODO send email

                        attempt = 0
                        while attempt < 11:
                            if not google_api.check_file_exists(file_id=temp_file_id, parent_folder_id=temp_id):
                                google_api.delete_file(file_id=file_id)
                                google_api.delete_file(file_id=temp_file_id)
                                break
                            attempt += 1
                            time.sleep(20)
                        else:
                            logger.error(
                                'File %s not deleted from temp folder after 10 attempts.', doc_name)
                            send_error_message(
                                f"File {doc_name} not deleted from temp folder after 10 attempts.")
                            return
                        # Remove files from temp document folder
                        delete_file(doc_path_name)
                        if doc_path_name != original_file_path:
                            delete_file(original_file_path)
                        print(f'Finish: {file_name}')


def create_test():
    """
    Create test folders
    """

    google_api = GoogleApi()

    sub_folders: List[FileFolder] = []

    sub_folder_0 = google_api.create_subfolder_in_folder(
        folder_name='kaplanmn@msn.com',
        parent_folder_id='1R4g1cSZUZ5nC2bzo7RxRO_46so5uYJS8')
    sub_folders.append(sub_folder_0)

    sub_folder_1 = google_api.create_subfolder_in_folder(
        folder_name='danishevsky@gmail.com',
        parent_folder_id='1R4g1cSZUZ5nC2bzo7RxRO_46so5uYJS8')
    sub_folders.append(sub_folder_1)

    for sub_folder in sub_folders:
        google_api.create_subfolder_in_folder(
            folder_name='incoming',
            parent_folder_id=sub_folder.id)
        google_api.create_subfolder_in_folder(
            folder_name='original',
            parent_folder_id=sub_folder.id)
