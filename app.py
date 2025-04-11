"""
Module processes email attachments
"""

import os
import time
from typing import Dict, List

from schedule import every, repeat, run_pending

from email_reader import extract_attachments_from_mailbox
from flowise_api import FlowiseAiAPI
from google_drive import GoogleApi

from utils import list_files_in_directory
from email_sender import send_error_message


@repeat(every(5).minutes)
def process_emails():
    """
    Check all emails extract attachments, upload attachments to
    google drive and create new prediction
    """
    flowise_api = FlowiseAiAPI()
    google_api = GoogleApi()

    # extract attachments from_mailbox
    extract_attachments_from_mailbox()

    # Get google drive list of clients email
    clients: List[Dict] = google_api.get_file_list_in_folder()
    clients_emails: List = []
    for client in clients:
        clients_emails.append(client.get("name"))

    # Process files in document folder
    document_folder = os.path.join(os.getcwd(), 'documents')
    file_list = list_files_in_directory(document_folder)
    for doc_name in file_list:
        doc_path: str = os.path.join(document_folder, doc_name)
        client_email: str = doc_name.split('+')[0]

        if not client_email in clients_emails:
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
            # Save in google drive
            print(f"Process document: {doc_name}")
            print(f'Upload to google: {doc_name}')
            res_upload = google_api.upload_file_to_google_drive(
                parent_folder=sub_folder_id, file_path=doc_path, file_name=doc_name)
            if res_upload.get('name') == 'Error':
                send_error_message(
                    f"Upload file to google: {res_upload.get('id')}")
                return
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
            os.remove(doc_path)
            print(f'Finish: {doc_name}')
        except Exception as error:
            return {"error": error}


if __name__ == "__main__":
    flowiseApi = FlowiseAiAPI()
    googleApi = GoogleApi()

    process_emails()

    # Run on schedule
    while True:
        run_pending()
        time.sleep(1)
