"""
Google Drive API wrapper class
"""
import os
import io
import shutil
from typing import Dict, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from src.utils import read_json_secret_file
from src.logger import logger


class GoogleApi:
    """
    Google drive wrapper class
    """

    def __init__(self) -> None:
        """
        Initialise service with credentials
        """
        secrets_path = os.path.join(
            os.getcwd(), 'credentials', 'secrets.json')
        secrets = read_json_secret_file(secrets_path)
        if not isinstance(secrets, Dict):
            logger.error('Secrets file not found or invalid')
            raise FileNotFoundError('Secrets file not found or invalid')
        google_drive_settings = secrets.get('google_drive')
        if not isinstance(google_drive_settings, Dict):
            logger.error('Google Drive settings not found in secrets.json')
            raise KeyError('Google Drive settings not found in secrets.json')
        self.parent_folder_id: str = google_drive_settings.get(
            'parent_folder_id', '')
        if self.parent_folder_id == '':
            logger.error('Parent folder ID not specified in secrets.json')
            raise KeyError('Parent folder ID not specified in secrets.json')
        scope = ['https://www.googleapis.com/auth/drive']
        service_account_json_key = os.path.join(
            os.getcwd(), 'credentials', 'service-account-key.json')

        credentials = (service_account.Credentials
                       .from_service_account_file(  # type: ignore
                           filename=service_account_json_key,
                           scopes=scope))
        self.service = build(
            serviceName='drive',
            version='v3',
            credentials=credentials)

    def get_item_list_in_folder(
        self,
        parent_folder_id: str = '',
        get_files: bool = True
    ) -> List[Dict[str, str]]:
        """
            Get item list in folder
            Args:
                parent_folder_id: parent folder id
                get_files: if True, return only files, if False,
                return folders
            Returns:
                List of items in folder as dicts
                [{'id': '1XZxSOB1k7MW0QY7XbQ7rd5Xko', 'name': 'item_name'}]
            Raises:
                HttpError: if an error occurs while making the API request
                Exception: if any other error occurs
            """
        if parent_folder_id == '':
            parent_folder_id = self.parent_folder_id
        mime_type: str = 'application/vnd.google-apps.folder'
        if get_files:
            mime_condition = f"mimeType != '{mime_type}'"
        else:
            mime_condition = f"mimeType = '{mime_type}'"
        files_in_folder: List[Dict[str, str]] = []
        page_token: str | None = None
        query = (
            f"'{parent_folder_id}' in parents and {mime_condition} "
            "and trashed=false ")
        fields = 'nextPageToken, files(id, name, mimeType, parents,properties, description)'
        try:
            while True:
                response = self.service.files().list(  # type: ignore
                    q=query,
                    fields=fields,
                    pageToken=page_token
                ).execute()
                files: List[Dict[str, str]] = response.get(  # type: ignore
                    'files', [])
                files_in_folder.extend(files)
                page_token: str | None = response.get('nextPageToken', None)
                if page_token is None:
                    break
            return files_in_folder
        except HttpError as error:
            print(f"get_file_list_in_folder: An error occurred: {error}")
            logger.error(
                'get_file_list_in_folder: An error occurred: %s', error)
            return []
        except Exception as e:
            print(f"get_file_list_in_folder: An error occurred: {e}")
            logger.error('get_file_list_in_folder: An error occurred: %s', e)
            return []

    def get_file_list_in_folder(
        self,
        parent_folder_id: str = '',
    ) -> List[Dict[str, str]]:
        """
        Get file list in folder
        Args:
            parent_folder_id: parent folder id
        Returns:
            List of files in folder as dicts
            [{'id': '1XZxSOB1k7MW0QY7XbQ7rd5Xko', 'name': 'file_name'}]
        """
        return self.get_item_list_in_folder(
            parent_folder_id=parent_folder_id,
            get_files=True)

    def get_subfolders_list_in_folder(
        self,
        parent_folder_id: str = '',
    ) -> List[Dict[str, str]]:
        """
        Get file sub folders list in folder
        Args:
            parent_folder_id: parent folder id
        Returns:
            List of sub folders in folder as dicts
            [{'id': '1XZxSOB1k7MW0QY7XbQ7rd5Xko', 'name': 'file_name'}]
        """
        return self.get_item_list_in_folder(
            parent_folder_id=parent_folder_id,
            get_files=False)

    def upload_file_to_google_drive(
        self,
        file_path: str,
        file_name: str,
        parent_folder_id: str = '',
    ) -> (object | dict[str, object]):
        """
        Upload file to Google Drive
        Args:
            file_path: path to the file to upload
            file_name: name of the file to upload
            parent_folder_id: id of the folder where you want to upload
        Returns:
            File object on success, dict with error message on failure
        Raises:
            FileNotFoundError: if file not found
            Exception: if any other error occurs
        """
        try:
            if parent_folder_id == '':
                parent_folder_id = self.parent_folder_id
            logger.info("DRIVE UPLOAD: name=%s parent=%s path=%s",
                        file_name, parent_folder_id, file_path)
            file_metadata: Dict[str, str | List[str]] = {
                'name': file_name,
                'parents': [parent_folder_id],
                'mimeType': 'application/msword'
            }
            media = MediaFileUpload(filename=file_path, mimetype='*/*')
            file: Dict[str, str] = self.service.files().create(  # type: ignore
                body=file_metadata,
                media_body=media,
                fields='id,name').execute()
            logger.info("DRIVE UPLOAD OK: name=%s id=%s",
                        file.get('name'), file.get('id'))
            return file  # type: ignore
        except HttpError as error:
            print(f"upload_file_to_google_drive: An error occurred: {error}")
            logger.error(
                'upload_file_to_google_drive: An error occurred: %s', error)
            return {"name": "Error", "id": None}
        except FileNotFoundError:
            print(f"upload_file_to_google_drive: File not found: {file_path}")
            logger.error(
                'upload_file_to_google_drive: File not found: %s', file_path)
            return {"name": "Error", "id": "File not found"}
        except Exception as e:
            print(f"upload_file_to_google_drive: An error occurred: {e}")
            logger.error(
                'upload_file_to_google_drive: An error occurred: %s', e)
            return {"name": "Error", "id": e}

    def download_file_from_google_drive(
            self,
            file_id: str,
            file_path: str
    ) -> bool:
        """
        Download file from Google Drive to local path
        Args:
            file_id: ID of the file to download
            file_path: Local path where the file will be saved
        Returns:
            True if file downloaded successfully, False otherwise
        Raises:
            HttpError: if an error occurs while making the API request
            Exception: if any other error occurs
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            # Initialise a downloader object to download the file
            downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
            done: bool = False
            # Download the data in chunks
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            # Write the received data to the file
            logger.info("DRIVE DOWNLOAD: id=%s -> %s", file_id, file_path)
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(fh, f)
            logger.info("DRIVE DOWNLOAD OK: %s", file_path)
            # Return True if file Downloaded successfully
            return True
        except HttpError as error:
            print(f"file_download: An error occurred: {error}")
            logger.error('file_download: An error occurred: %s', error)
            return False
        except FileNotFoundError:
            print(f"file_download: File path not found: {file_path}")
            logger.error('file_download: File path not found: %s', file_path)
            return False
        except PermissionError:
            print(
                f"file_download: Permission denied for file path: {file_path}")
            logger.error(
                'file_download: Permission denied for file path: %s',
                file_path)
            return False
        except Exception as e:
            print(f"file_download: An error occurred: {e}")
            logger.error('file_download: An error occurred: %s', e)
            return False

    def move_file_to_deleted_folder(
        self,
        file_id: str,
        client_folder_id: str,
        deleted_folder_name: str = 'deleted'
    ) -> bool:
        """
        Move file to 'deleted' folder instead of trashing
        If 'deleted' folder doesn't exist, create it
        Args:
            file_id: ID of the file to move
            client_folder_id: ID of the parent folder where the file is located
            deleted_folder: Name of the folder to move the file to
        Returns:
            Response object if successful, None if failed
        Raises:
            HttpError: if an error occurs while making the API request
            FileNotFoundError: if the file is not found
            PermissionError: if permission is denied for the file
            Exception: if any other error occurs
        """
        try:
            current_parent: str = self.get_file_parent_folder_id(
                file_id=file_id)
            if current_parent == '':
                logger.error(
                    "File %s not found or has no parent folder", file_id)
                return False
            # Check if 'deleted' folder exists in the current parent
            folders = self.get_subfolders_list_in_folder(
                parent_folder_id=client_folder_id)
            deleted_folder: Dict[str, str] | None = next(
                filter(
                    lambda f: f['name'] == deleted_folder_name, folders), None)
            # Create 'deleted' folder if it doesn't exist
            if deleted_folder:
                deleted_folder_id = deleted_folder['id']
            else:
                # Create 'deleted' folder in the current parent folder
                logger.info(
                    "Creating 'deleted' folder in parent: %s", client_folder_id)
                deleted_folder = self.create_subfolder_in_folder(
                    folder_name='deleted',
                    parent_folder_id=client_folder_id
                )
                deleted_folder_id = deleted_folder.get('id', '')
                if deleted_folder_id == '':
                    logger.error("Failed to create 'deleted' folder")
                    return False
                logger.info("Created 'deleted' folder: %s", deleted_folder_id)
            # Move the file to 'deleted' folder
            file_name: str = self.get_file_name_by_id(file_id=file_id)
            logger.info("DRIVE MOVE: '%s' -> 'deleted'", file_name)
            self.service.files().update(  # type: ignore
                fileId=file_id,
                addParents=deleted_folder_id,
                removeParents=current_parent,
                fields='id,name,parents',
                supportsAllDrives=True
            ).execute()
            logger.info(
                "DRIVE MOVE OK: '%s' (ID: %s) -> 'deleted'",
                file_name,
                file_id)
            print(f"Moved file '{file_name}' to 'deleted' folder")
            return True

        except HttpError as error:
            print(f"delete_file: An error occurred: {error}")
            logger.error(('delete_file: An error "'
                          '"occurred while moving file %s: %s'),
                         file_id, error)
            return False
        except FileNotFoundError:
            print(f"delete_file: File not found: {file_id}")
            logger.error('delete_file: File not found: %s', file_id)
            return False
        except PermissionError:
            print(f"delete_file: Permission denied for file ID: {file_id}")
            logger.error(
                'delete_file: Permission denied for file ID: %s', file_id)
            return False
        except Exception as e:
            print(f"delete_file: An error occurred: {e}")
            logger.error(('delete_file: An error '
                          'occurred while moving file %s: %s'),
                         file_id, e)
            return False

    def create_subfolder_in_folder(
            self,
            folder_name: str,
            parent_folder_id: str = ''
    ) -> Dict[str, str]:
        """
        Creates subfolder in parent folder
        args:
            folder_name: name
            parent_folder_id: id string
        Returns:
            dict with id and name of created folder
        Raises:
            HttpError: if an error occurs while making the API request
            FileNotFoundError: if the parent folder is not found
            PermissionError: if permission is denied for the parent folder
            Exception: if any other error occurs
        """
        try:
            if parent_folder_id == '':
                parent_folder_id = self.parent_folder_id
            folder_metadata: dict[str, str | List[str]] = {
                'name': folder_name,
                'parents': [parent_folder_id],
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(  # type: ignore
                body=folder_metadata,
                fields='id').execute()
            return {'id': folder.get('id', ''), 'name': folder_name}
        except HttpError as error:
            print(f"create_subfolder_in_folder: An error occurred: {error}")
            logger.error(
                'create_subfolder_in_folder: An error occurred: %s', error)
            return {'id': '', 'name': ''}
        except FileNotFoundError:
            print(
                ("create_subfolder_in_folder: "
                 f"File not found: {parent_folder_id}"))
            logger.error(
                'create_subfolder_in_folder: File not found: %s',
                parent_folder_id)
            return {'id': '', 'name': ''}
        except PermissionError:
            print(
                ("create_subfolder_in_folder: Permission "
                 f"denied for folder: {parent_folder_id}"))
            logger.error(
                'create_subfolder_in_folder: Permission denied for folder: %s',
                parent_folder_id)
            return {'id': '', 'name': ''}
        except Exception as e:
            print(f"create_subfolder_in_folder: An error occurred: {e}")
            logger.error(
                'create_subfolder_in_folder: An error occurred: %s', e)
            return {'id': '', 'name': ''}

    def get_file_parent_folder_id(self, file_id: str) -> str:
        """
        Get the parent folder ID of a file
        Args:
            file_id: ID of the file to check
        Returns:
            The ID of the parent folder if found, otherwise an empty string
        Raises:
            HttpError: if an error occurs while making the API request
            FileNotFoundError: if the file is not found
            PermissionError: if permission is denied for the file
            Exception: if any other error occurs"""
        try:
            file_info: Dict[str, str | List[str]] = self.service.files(
            ).get(  # type: ignore
                    fileId=file_id,
                    fields='parents,name',
                    supportsAllDrives=True
            ).execute()
            if not isinstance(file_info, dict):
                logger.error("Invalid file info received: %s", file_id)
                return ''
            file_name: str = file_info.get('name', '')  # type: ignore
            parents: List[str] = file_info.get('parents', [])  # type: ignore
            if not parents:
                logger.error("File %s has no parent folder", file_name)
                return ''
            current_parent: str = parents[0]
            return current_parent
        except HttpError as error:
            print(f"get_file_parent_folder_id: An error occurred: {error}")
            logger.error(
                'get_file_parent_folder_id: An error occurred while getting "'
                '"parent folder ID for file %s: %s',
                file_id, error)
            return ''
        except FileNotFoundError:
            print(f"get_file_parent_folder_id: File not found: {file_id}")
            logger.error(
                'get_file_parent_folder_id: File not found: %s', file_id)
            return ''
        except PermissionError:
            print(
                "get_file_parent_folder_id: "
                f"Permission denied for file ID: {file_id}")
            logger.error(
                'get_file_parent_folder_id: Permission denied for file ID: %s',
                file_id)
            return ''
        except Exception as e:
            print(f"get_file_parent_folder_id: An error occurred: {e}")
            logger.error(
                ('get_file_parent_folder_id: An error occurred while "'
                 '"getting parent folder ID for file %s: %s'),
                file_id, e)
            return ''

    def get_file_name_by_id(self, file_id: str) -> str:
        """
        Get the name of a file by its ID
        Args:
            file_id: ID of the file to check
        Returns:
            The name of the file if found, otherwise an empty string
        Raises:
            HttpError: if an error occurs while making the API request
            FileNotFoundError: if the file is not found
            PermissionError: if permission is denied for the file
            Exception: if any other error occurs
        """
        try:
            file_info = self.service.files().get(  # type: ignore
                fileId=file_id,
                fields='name,trashed',
                supportsAllDrives=True
            ).execute()
            if not isinstance(
                    file_info, dict) or file_info.get('trashed', True):
                logger.error("Invalid file info received: %s", file_id)
                return ''
            return file_info.get('name', '')
        except HttpError as error:
            print(f"get_file_name_by_id: An error occurred: {error}")
            logger.error(
                'get_file_name_by_id: An error occurred while getting "'
                '"file name for ID %s: %s', file_id, error)
            return ''
        except FileNotFoundError:
            print(f"get_file_name_by_id: File not found: {file_id}")
            logger.error(
                'get_file_name_by_id: File not found: %s', file_id)
            return ''
        except PermissionError:
            print(
                "get_file_name_by_id: "
                f"Permission denied for file ID: {file_id}")
            logger.error(
                'get_file_name_by_id: Permission denied for file ID: %s',
                file_id)
            return ''
        except Exception as e:
            print(f"get_file_name_by_id: An error occurred: {e}")
            logger.error(
                ('get_file_name_by_id: An error occurred while "'
                 '"getting file name for ID %s: %s'),
                file_id, e)
            return ''

    def get_file_app_property(self, file_id: str, name: str) -> str | None:
        """
        Return a specific appProperties value for a file, or None if not set.
        """
        try:
            info = self.service.files().get(  # type: ignore
                fileId=file_id,
                fields='appProperties',
                supportsAllDrives=True
            ).execute()
            if not isinstance(info, dict):
                return None
            app_props = info.get('appProperties') or {}
            if not isinstance(app_props, dict):
                return None
            value = app_props.get(name)
            return value if isinstance(value, str) and value else None
        except Exception as e:
            logger.error(
                "get_file_app_property failed for %s (%s): %s", file_id, name, e)
            return None

    def if_folder_exist_by_name(
        self,
        folder_name: str,
        parent_folder_id: str = ''
    ) -> bool:
        """
        Check if folder exists by name in parent folder
        Args:
            folder_name: name of the folder to check
            parent_folder_id: ID of the parent folder
        Returns:
            True if folder exists, False otherwise
        """
        folders = self.get_subfolders_list_in_folder(
            parent_folder_id=parent_folder_id)
        return any(folder['name'] == folder_name for folder in folders)

    def move_file_to_folder_id(
        self,
        file_id: str,
        dest_folder_id: str
    ) -> bool:
        """
        Move a file from its current parent to a destination folder by ID.
        """
        try:
            current_parent: str = self.get_file_parent_folder_id(
                file_id=file_id)
            if current_parent == '':
                logger.error(
                    "File %s not found or has no parent folder", file_id)
                return False

            file_name: str = self.get_file_name_by_id(file_id=file_id)
            logger.info("DRIVE MOVE: '%s' -> parent=%s",
                        file_name, dest_folder_id)
            self.service.files().update(  # type: ignore
                fileId=file_id,
                addParents=dest_folder_id,
                removeParents=current_parent,
                fields='id,name,parents',
                supportsAllDrives=True
            ).execute()
            logger.info("DRIVE MOVE OK: '%s' (ID=%s) -> parent=%s",
                        file_name, file_id, dest_folder_id)
            return True
        except Exception as e:
            logger.error("Failed to move file %s to folder '%s': %s",
                         file_id, dest_folder_id, e)
            return False
