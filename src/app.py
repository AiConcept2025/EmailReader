"""
Module processes email attachments
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List

import docx2txt
from langdetect import detect
from schedule import every, repeat

from src.email_reader import extract_attachments_from_mailbox
from src.email_sender import send_error_message
from src.flowise_api import FlowiseAiAPI
from src.google_drive import GoogleApi
from src.logger import logger
from src.utils import list_files_in_directory
import shutil


def delete_file(file_path: str):
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"File '{file_path}' deleted successfully.")
        except OSError as e:
            print(f"Error deleting file '{file_path}': {e}")
    else:
        print(f"File '{file_path}' does not exist.")


@repeat(every(2).hours)
def process_emails():
    """
    Check all emails extract attachments, upload attachments to
    google drive and create new prediction
    """
    logger.info('Start email processing')
    flowise_api = FlowiseAiAPI()
    google_api = GoogleApi()
    # extract attachments from_mailbox
    extract_attachments_from_mailbox()
    logger.info('Start process loaded documents.')
    document_folder = os.path.join(os.getcwd(), 'data', 'documents')
    # Get google drive list of clients email
    clients: List[Dict] = google_api.get_file_list_in_folder()
    clients_emails: List = []
    for client in clients:
        clients_emails.append(client.get("name"))

    # Process files in document folder
    # document_folder = os.path.join(os.getcwd(), 'data', 'documents')
    file_list = list_files_in_directory(document_folder)
    for doc_name in file_list:
        logger.info('Start to process document %s', doc_name)
        doc_path: str = os.path.join(document_folder, doc_name)
        client_email: str = doc_name.split('+')[0]
        if not client_email in clients_emails:
            logger.info('Create folder for new client: %s', client_email)
            # create new client subfolder
            res: Dict = google_api.create_subfolder_in_folder(
                folder_name=client_email)
            folder_id = res.get('id')
            # Update clients collections
            clients_emails.append(client_email)
            clients.append({"id": folder_id, "name": client_email})
            # create inbound client subfolder
            res = google_api.create_subfolder_in_folder(
                folder_name='inbound', parent_folder=folder_id)
            sub_folder_id = res.get('id')
        else:
            client_folder_info = next(
                (item for item in clients if item["name"] == client_email), None)
            client_folder_id = client_folder_info.get('id')
            sub_folders_files = google_api.get_file_list_in_folder(
                client_folder_id)
            client_subfolder_info = next(
                (item for item in sub_folders_files if item["name"] == "inbound"), None)
            sub_folder_id = client_subfolder_info.get('id')
        try:
            # Save in google drive original file
            logger.info('Upload file %s to google drive', doc_name)
            res_upload = google_api.upload_file_to_google_drive(
                parent_folder=sub_folder_id,
                file_path=doc_path,
                file_name=doc_name)
            if res_upload.get('name') == 'Error':
                send_error_message(
                    f"Upload file to google: {res_upload.get('id')}")
                return
            # Continue if file not Word format
            _, ext1 = os.path.splitext(doc_name)  # Return extension with '.'
            if ext1 != '.docx' and ext1 != '.doc':
                delete_file(doc_path)
                continue
            # Check if file language is English
            file_path = Path(os.path.join(
                os.getcwd(), 'data', "documents", doc_name))
            my_text = docx2txt.process(file_path)
            language = detect(my_text)
            if language == 'en':
                index = doc_name.find('+') + 1
                mew_doc_name = doc_name[:index] + \
                    'english_' + doc_name[index:]
                new_file_path = Path(os.path.join(
                    os.getcwd(), 'data', "documents", mew_doc_name))
                shutil.copyfile(file_path, new_file_path)
                delete_file(doc_path)
                doc_name = mew_doc_name
                doc_path = new_file_path
            else:
                # If file language not English translate it and save original one
                index = doc_name.find('+') + 1
                translated_doc_name = doc_name[:index] + \
                    'english_' + doc_name[index:]
                translated_file_path = Path(os.path.join(
                    os.getcwd(), 'data', "documents", translated_doc_name))
                logger.info('Translate document %s', doc_name)
                executable_path = Path(os.path.join(
                    os.getcwd(), 'translate_document', "translate_document.exe"))
                arguments = ["-i", file_path, "-o", translated_file_path]
                command = [executable_path] + arguments
                try:
                    subprocess.run(command, capture_output=True,
                                   text=True, check=True)
                except subprocess.CalledProcessError as e:
                    logger.error(
                        'Error executing command: %s Stdout: %s, Stderr: %s',
                        e, e.stdout, e.stderr)
                # Upload translated document to google drive
                res_doc_store = flowise_api.upsert_document_to_document_store(
                    doc_name=translated_doc_name, doc_path=translated_file_path)
                if res_doc_store.get('name') == 'Error':
                    send_error_message(
                        f"Upload file doc store error: {res_doc_store.get('error')}")
                    return
                # Delete original document from temp folder
                delete_file(doc_path)
                # Replace original document with translated one
                doc_name = translated_doc_name
                doc_path = translated_file_path

            delete_file(doc_path)
            continue
            # Upload to doc store
            print(f'Upload to doc store: {doc_name}')
            res_doc_store = flowise_api.upsert_document_to_document_store(
                doc_name=doc_name, doc_path=doc_path)
            if res_doc_store.get('name') == 'Error':
                send_error_message(
                    f"Upload file doc store error: {res_doc_store.get('error')}")
                return
            # run prediction
            print(f'Upload to prediction: {doc_name}')
            res_prediction = flowise_api.create_new_prediction(doc_name)
            if res_prediction.get('name') == 'Error':
                send_error_message(
                    f"Prediction error: {res_prediction.get('id')}")
                return  # TODO send email

            attempt = 0
            while google_api.check_file_exists(file_name=doc_name, folder_id=sub_folder_id) and attempt < 11:
                attempt += 1
                time.sleep(20)
            # Remove file id success
            delete_file(doc_path)
            print(f'Finish: {doc_name}')
        except Exception as error:
            return {"error": error}
