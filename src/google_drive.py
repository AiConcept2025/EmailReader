"""
Google Drive API wrapper class
"""

import os
import io
import shutil
from typing import Dict, List, NamedTuple

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from src.logger import logger


class FileFolder(NamedTuple):
    name: str
    id: str


class GoogleApi:
    """
    Google drive wrapper class
    """

    def __init__(self):
        """
        Initialise service with credentials
        """
        scope = ['https://www.googleapis.com/auth/drive']
        service_account_json_key = os.path.join(
            os.getcwd(), 'credentials', 'service-account-key.json')

        credentials = service_account.Credentials.from_service_account_file(
            filename=service_account_json_key,
            scopes=scope)
        self.service = build('drive', 'v3', credentials=credentials)
        self.parent_folder_id = '1R4g1cSZUZ5nC2bzo7RxRO_46so5uYJS8'  # IrisSolutions

    def upload_file_to_google_drive(self, parent_folder_id: str, file_path: str, file_name: str):
        """
        Uploading a File to Google Drive
        """
        try:
            if parent_folder_id is None:
                parent_folder_id = self.parent_folder_id
            file_metadata = {
                'name': file_name,
                # ID of the folder where you want to upload
                'parents': [parent_folder_id],
                'mimeType': '*/*'
            }
            media = MediaFileUpload(filename=file_path, mimetype='*/*')
            file = self.service.files().create(
                body=file_metadata, media_body=media, fields='id,name').execute()
            return file
        except HttpError as error:
            print(f"An error occurred: {error}")
            return {"name": "Error", "id": error}

    def get_root_file_list(self) -> List[Dict]:
        """
        Returns file list
        """
        try:
            result = self.service.files().list(fields="files(id, name)").execute()
            # return the result dictionary containing
            # the information about the files
            data = result.get('files')
            return data
        except HttpError as error:
            print(f"An error occurred: {error}")

    def file_exists(self, file_id: str):
        """
        Check if file exist
        """
        try:
            self.service.files().get(fileId=file_id, fields='id').execute()
            return True
        except Exception:
            return False

    #################################################
    #################################################
    #################################################
    #################################################

    def get_folders_list(self, parent_folder_id: str = None) -> List[Dict]:
        """
        Returns list of all the folders
        [{'id': '1XZxSOB1k7MW0QY7XbQ7rd5Xko', 'name': 'folder_name'}]
        parent_folder_id: parent folder id
        """
        if parent_folder_id is None:
            parent_folder_id = self.parent_folder_id
        page_token = None
        mime_type = 'application/vnd.google-apps.folder'
        query = f"'{parent_folder_id}' in parents and mimeType = '{mime_type}'"
        try:
            while True:
                # Call the Drive v3 API
                results = (
                    self.service.files()
                    .list(
                        q=query,
                        spaces="drive",
                        fields="nextPageToken, files(id, name)",
                        pageToken=page_token)
                    .execute()
                )
                folders = results.get("files", [])
                if page_token is None:
                    break
            return folders
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def if_folder_exist_by_name(self, folder_name: str, parent_folder_id: str = None) -> bool:
        """
        Check by name if sub folder exist
        """
        folders = self.get_folders_list(parent_folder_id=parent_folder_id)
        if len(folders) < 1:
            return False
        for folder in folders:
            if folder.get('name', None) == folder_name:
                return True
        return False

    def if_folder_exist_by_id(self, folder_name_id: str, parent_folder_id: str = None) -> bool:
        """
        Check by name if sub folder exist
        """
        folders = self.get_folders_list(parent_folder_id=parent_folder_id)
        if len(folders) < 1:
            return False
        for folder in folders:
            if folder.get('name', None) == folder_name_id:
                return True
        return False

    def get_file_list(self, parent_folder_id: str = None) -> List[Dict]:
        """
        Returns list of all the folders
        [{'id': '1XZxSOB1k7MW0QY7XbQ7rd5Xko', 'name': 'folder_name'}]
        parent_folder_id: parent folder id
        """
        if parent_folder_id is None:
            parent_folder_id = self.parent_folder_id
        page_token = None
        mime_type = 'application/vnd.google-apps.file'
        query = f"'{parent_folder_id}' in parents and mimeType = '{mime_type}'"
        try:
            while True:
                # Call the Drive v3 API
                results = (
                    self.service.files()
                    .list(
                        q=query,
                        spaces="drive",
                        fields="nextPageToken, files(id, name)",
                        pageToken=page_token)
                    .execute()
                )
                folders = results.get("files", [])
                if page_token is None:
                    break
            return folders
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def get_file_list_in_folder1(self, parent_folder_id: str = None) -> List[Dict]:
        """
        Get file list in folder
        """
        mime_type = 'application/vnd.google-apps.file'
        try:
            if parent_folder_id is None:
                parent_folder_id = self.parent_folder_id
            pageToken = ""
            result = self.service.files().list(q="'" + parent_folder_id + "' in parents", pageSize=1000,
                                               pageToken=pageToken, fields="nextPageToken, files(id, name)").execute()
            # query = f"'{parent_folder_id}' in parents and mimeType='{mime_type}'"
            # result = self.service.files().list(
            #     q=query,
            #     fields="files(id, name)"
            # ).execute()
            # return the result dictionary containing
            # the information about the files
            data = result.get('files')
            return data
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def check_file_exists(self, file_id: str, parent_folder_id: str = None) -> bool:
        files = self.get_file_list_in_folder1(
            parent_folder_id=parent_folder_id)
        temp_id = [fl['id'] for fl in files if fl['id'] == file_id][0]
        return temp_id == file_id

    def create_subfolder_in_folder(
            self,
            folder_name: str,
            parent_folder_id: str = None) -> FileFolder:
        """
        Creates subfolder in parent folder
        args:
            folder_name: name
            parent_folder_id: id string
        """
        try:
            if parent_folder_id is None:
                parent_folder_id = self.parent_folder_id
            folder_metadata = {
                'name': folder_name,
                'parents': [parent_folder_id],
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id').execute()
            return FileFolder(id=folder.get('id'), name=folder_name)
        except HttpError as error:
            logger.error('An error occurred: %s', error)
            return FileFolder(id=None, name=None)

    def delete_file(self, file_id: str):
        """
        Delete file by string id
        Args:
        file_id: file id
        """
        try:
            result = self.service.files().delete(fileId=file_id).execute()
            return result
        except HttpError as error:
            print(f"An error occurred: {error}")

    def if_file_exists_by_name(self, file_name, folder_id=None):
        """
        Checks if a file exists in a specific folder in Google Drive.
        Args:
            file_name: The name of the file to check.
            folder_id: The ID of the folder to search in.

        Returns:
            True if the file exists, False otherwise.
        """
        if folder_id == None:
            folder_id = self.parent_folder_id
        query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
        try:

            results = self.service.files().list(
                q=query,
                fields="files(id)"
            ).execute()
            items = results.get('files', [])
            return len(items) > 0
        except HttpError as error:
            print(f"An error occurred: {error}")
            return False

##########################################################################################

    def FileDownload(self, file_id, file_path):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()

        # Initialise a downloader object to download the file
        downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
        done = False

        try:
            # Download the data in chunks
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)

            # Write the received data to the file
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(fh, f)

            print("File Downloaded")
            # Return True if file Downloaded successfully
            return True
        except HttpError as error:
            print(f"An error occurred: {error}")
            return False
##########################################################################################


"""
List of MimeTypes

"application/vnd.google-apps.audio"
"application/vnd.google-apps.document"
"application/vnd.google-apps.drawing"
"application/vnd.google-apps.file"
"application/vnd.google-apps.folder"
"application/vnd.google-apps.form"
"application/vnd.google-apps.fusiontable"
"application/vnd.google-apps.photo"
"application/vnd.google-apps.presentation"
"application/vnd.google-apps.sites"
"application/vnd.google-apps.spreadsheet"
"application/vnd.google-apps.unknown"
"application/vnd.google-apps.video"
"application/pdf"
"application/msword"
"application/vnd.openxmlformats-officedocument.wordprocessingml.document"
"application/vnd.ms-powerpoint.presentation.macroEnabled.12"
"application/vnd.ms-excel"
"image/jpeg"
"audio/mpeg"
"video/mpeg"
"application/zip"
"text/plain"
"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
"application/vnd.android.package-archive"
"application/vnd.google-apps.kix"
"""
