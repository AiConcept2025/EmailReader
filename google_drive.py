from typing import Dict, List

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


class GoogleApi:
    """
    Google drive wrapper class
    """

    def __init__(self):
        """
        Initialise service with credentials
        """
        scope = ['https://www.googleapis.com/auth/drive']
        service_account_json_key = 'service-account-key.json'
        credentials = service_account.Credentials.from_service_account_file(
            filename=service_account_json_key,
            scopes=scope)
        self.service = build('drive', 'v3', credentials=credentials)
        self.parent_folder = '1R4g1cSZUZ5nC2bzo7RxRO_46so5uYJS8'  # IrisSolutions

    def create_subfolder_in_folder(
            self,
            folder_name: str,
            parent_folder: str = None):
        """
        Creates subfolder in parent folder
        args:
            folder_name: name
            parent_folder: id string
        """
        try:
            if parent_folder is None:
                parent_folder = self.parent_folder
            folder_metadata = {
                'name': folder_name,
                'parents': [parent_folder],
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id').execute()
            return folder
        except HttpError as error:
            print(f"An error occurred: {error}")

    def get_folders_list(self, parent_folder: str = None) -> List[Dict]:
        """
        Returns list of all the folders
        [{'id': '1XZxSOB1k7MW0QY7XbQ7rd5Xko', 'name': 'folder_name'}]
        """
        try:
            if parent_folder is None:
                parent_folder = self.parent_folder
            page_token = None
            while True:
                # Call the Drive v3 API
                results = (
                    self.service.files()
                    .list(
                        q="mimeType = 'application/vnd.google-apps.folder'",

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

    def get_file_list_in_folder(self, parent_folder: str = None) -> List[Dict]:
        """
        Get file list in folder
        """
        try:
            if parent_folder is None:
                parent_folder = self.parent_folder
            result = self.service.files().list(
                q=f"'{parent_folder}' in parents",
                fields="files(id, name)"
            ).execute()
            # return the result dictionary containing
            # the information about the files
            data = result.get('files')
            return data
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def delete_file(self, file_id: str):
        """
            Delete file by string id
        """
        try:
            result = self.service.files().delete(fileId=file_id).execute()
            return result
        except HttpError as error:
            print(f"An error occurred: {error}")

    def upload_file_to_google_drive(self, parent_folder: str, file_path: str, file_name: str):
        """
        Uploading a File to Google Drive
        """
        try:
            if parent_folder is None:
                parent_folder = self.parent_folder
            file_metadata = {
                'name': file_name,
                # ID of the folder where you want to upload
                'parents': [parent_folder],
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
            resource = self.service.files()
            result = resource.list(fields="files(id, name)").execute()
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

    def check_file_exists(self, file_name, folder_id):
        """
        Checks if a file exists in a specific folder in Google Drive.

        Args:
            file_name: The name of the file to check.
            folder_id: The ID of the folder to search in.

        Returns:
            True if the file exists, False otherwise.
        """
        try:
            results = self.service.files().list(
                q=f"name='{file_name}' and '{folder_id}' in parents and trashed=false",
                fields="files(id)"
            ).execute()
            items = results.get('files', [])
            return len(items) > 0
        except HttpError as error:
            print(f"An error occurred: {error}")
            return False


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
