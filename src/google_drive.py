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

from src.config import load_config, get_service_account_path
from src.logger import logger


class GoogleApi:
    """
    Google drive wrapper class
    """

    def __init__(self) -> None:
        """
        Initialise service with credentials from environment-aware config
        """
        logger.debug("Initializing Google Drive API client")

        # Load configuration
        config = load_config()

        # Get parent folder ID from config
        if 'google_drive' not in config or 'parent_folder_id' not in config['google_drive']:
            logger.error('google_drive.parent_folder_id not found in configuration')
            raise KeyError('google_drive.parent_folder_id not specified in config')

        self.parent_folder_id: str = config['google_drive']['parent_folder_id']
        logger.debug("Parent folder ID: %s", self.parent_folder_id)

        # Get service account credentials
        scope = ['https://www.googleapis.com/auth/drive']
        service_account_json_key = get_service_account_path()
        logger.debug("Using service account from: %s", service_account_json_key)

        credentials = (service_account.Credentials
                       .from_service_account_file(  # type: ignore
                           filename=service_account_json_key,
                           scopes=scope))
        self.service = build(
            serviceName='drive',
            version='v3',
            credentials=credentials)

        logger.info("Google Drive API client initialized successfully")

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

        item_type = 'files' if get_files else 'folders'
        logger.debug("Listing %s in folder ID: %s", item_type, parent_folder_id)

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
        fields = 'nextPageToken, files(id, name, mimeType, parents, properties, appProperties, description)'
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

            logger.info("Found %d %s in folder ID: %s", len(files_in_folder), item_type, parent_folder_id)
            if files_in_folder:
                logger.debug("  First %d items: %s", min(5, len(files_in_folder)),
                           ', '.join([f"'{f['name']}'" for f in files_in_folder[:5]]))

            return files_in_folder
        except HttpError as error:
            logger.error(
                "Failed to list %s in folder ID: %s - %s",
                item_type, parent_folder_id, error
            )
            return []
        except Exception as e:
            logger.error(
                "Unexpected error listing %s in folder ID: %s - %s",
                item_type, parent_folder_id, e
            )
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
        description: str = "",
        properties: Dict[str, str] = {'source_language': '', }
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

            file_size = os.path.getsize(file_path) / 1024  # KB

            logger.info(
                "DRIVE UPLOAD: Uploading file '%s' (%.2f KB) to folder ID: %s",
                file_name, file_size, parent_folder_id
            )
            logger.debug("  Source path: %s", file_path)
            if properties and any(v for v in properties.values() if v):
                logger.debug("  Properties: %s", properties)

            file_metadata: Dict[str, str | List[str]] = {
                'name': file_name,
                'parents': [parent_folder_id],
                'mimeType': 'application/msword',
                'description': description,
                'properties': properties
            }
            media = MediaFileUpload(filename=file_path, mimetype='*/*')
            file: Dict[str, str] = self.service.files().create(  # type: ignore
                body=file_metadata,
                media_body=media,
                fields='id,name').execute()

            logger.info(
                "DRIVE UPLOAD SUCCESS: File '%s' uploaded to folder ID: %s (File ID: %s)",
                file.get('name'), parent_folder_id, file.get('id')
            )
            return file  # type: ignore
        except HttpError as error:
            logger.error(
                "DRIVE UPLOAD FAILED: Could not upload '%s' to folder ID: %s - %s",
                file_name, parent_folder_id, error
            )
            return {"name": "Error", "id": None}
        except FileNotFoundError:
            logger.error(
                "DRIVE UPLOAD FAILED: Source file not found - %s", file_path
            )
            return {"name": "Error", "id": "File not found"}
        except Exception as e:
            logger.error(
                "DRIVE UPLOAD FAILED: Unexpected error uploading '%s' - %s",
                file_name, e
            )
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
            # Get file name for better logging
            file_name = self.get_file_name_by_id(file_id)
            if not file_name:
                file_name = "unknown"

            logger.info(
                "DRIVE DOWNLOAD: Starting download of '%s' (ID: %s)",
                file_name, file_id
            )
            logger.debug("  Destination: %s", file_path)

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
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(fh, f)

            # Log file size
            file_size = os.path.getsize(file_path) / 1024  # KB
            logger.info(
                "DRIVE DOWNLOAD SUCCESS: File '%s' downloaded (%.2f KB) to %s",
                file_name, file_size, file_path
            )
            return True
        except HttpError as error:
            file_name = self.get_file_name_by_id(file_id) if file_id else "unknown"
            logger.error(
                "DRIVE DOWNLOAD FAILED: Could not download '%s' (ID: %s) - %s",
                file_name, file_id, error
            )
            return False
        except FileNotFoundError:
            logger.error(
                "DRIVE DOWNLOAD FAILED: Destination path not found - %s", file_path
            )
            return False
        except PermissionError:
            logger.error(
                "DRIVE DOWNLOAD FAILED: Permission denied for path - %s", file_path
            )
            return False
        except Exception as e:
            file_name = self.get_file_name_by_id(file_id) if file_id else "unknown"
            logger.error(
                "DRIVE DOWNLOAD FAILED: Unexpected error downloading '%s' - %s",
                file_name, e
            )
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

            logger.info(
                "DRIVE CREATE FOLDER: Creating subfolder '%s' in parent folder ID: %s",
                folder_name, parent_folder_id
            )

            folder_metadata: dict[str, str | List[str]] = {
                'name': folder_name,
                'parents': [parent_folder_id],
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(  # type: ignore
                body=folder_metadata,
                fields='id').execute()

            new_folder_id = folder.get('id', '')
            logger.info(
                "DRIVE CREATE FOLDER SUCCESS: Created subfolder '%s' (ID: %s) in parent ID: %s",
                folder_name, new_folder_id, parent_folder_id
            )
            return {'id': new_folder_id, 'name': folder_name}
        except HttpError as error:
            logger.error(
                "DRIVE CREATE FOLDER FAILED: Could not create subfolder '%s' in parent ID: %s - %s",
                folder_name, parent_folder_id, error
            )
            return {'id': '', 'name': ''}
        except FileNotFoundError:
            logger.error(
                "DRIVE CREATE FOLDER FAILED: Parent folder not found - ID: %s",
                parent_folder_id
            )
            return {'id': '', 'name': ''}
        except PermissionError:
            logger.error(
                "DRIVE CREATE FOLDER FAILED: Permission denied for parent folder - ID: %s",
                parent_folder_id
            )
            return {'id': '', 'name': ''}
        except Exception as e:
            logger.error(
                "DRIVE CREATE FOLDER FAILED: Unexpected error creating '%s' in parent ID: %s - %s",
                folder_name, parent_folder_id, e
            )
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
                    "DRIVE MOVE FAILED: File (ID: %s) not found or has no parent folder", file_id)
                return False

            file_name: str = self.get_file_name_by_id(file_id=file_id)

            logger.info(
                "DRIVE MOVE: Moving file '%s' from folder ID: %s to folder ID: %s",
                file_name, current_parent, dest_folder_id
            )
            logger.debug("  File ID: %s", file_id)

            self.service.files().update(  # type: ignore
                fileId=file_id,
                addParents=dest_folder_id,
                removeParents=current_parent,
                fields='id,name,parents',
                supportsAllDrives=True
            ).execute()

            logger.info(
                "DRIVE MOVE SUCCESS: File '%s' moved to folder ID: %s",
                file_name, dest_folder_id
            )
            return True
        except Exception as e:
            file_name = self.get_file_name_by_id(file_id) if file_id else "unknown"
            logger.error(
                "DRIVE MOVE FAILED: Could not move file '%s' to folder ID: %s - %s",
                file_name, dest_folder_id, e
            )
            return False

    def get_file_web_link(self, file_id: str) -> str:
        """
        Get shareable web view link for a Google Drive file
        Args:
            file_id: ID of the file
        Returns:
            Web view link (URL) if successful, empty string otherwise
        Raises:
            HttpError: if an error occurs while making the API request
            Exception: if any other error occurs
        """
        try:
            file_info = self.service.files().get(  # type: ignore
                fileId=file_id,
                fields='webViewLink',
                supportsAllDrives=True
            ).execute()
            if not isinstance(file_info, dict):
                logger.error("Invalid file info received for webViewLink: %s", file_id)
                return ''
            web_link = file_info.get('webViewLink', '')
            logger.info("Got webViewLink for file %s: %s", file_id, web_link)
            return web_link
        except HttpError as error:
            logger.error(
                'get_file_web_link: HttpError for file %s: %s', file_id, error)
            return ''
        except Exception as e:
            logger.error(
                'get_file_web_link: Error getting web link for file %s: %s',
                file_id, e)
            return ''

    def get_folder_name_by_id(self, folder_id: str) -> str:
        """
        Get the name of a folder by its ID
        Args:
            folder_id: ID of the folder
        Returns:
            The name of the folder if found, otherwise an empty string
        Raises:
            HttpError: if an error occurs while making the API request
            Exception: if any other error occurs
        """
        try:
            folder_info = self.service.files().get(  # type: ignore
                fileId=folder_id,
                fields='name,mimeType,trashed',
                supportsAllDrives=True
            ).execute()
            if not isinstance(folder_info, dict) or folder_info.get('trashed', True):
                logger.error("Invalid folder info received: %s", folder_id)
                return ''
            mime_type = folder_info.get('mimeType', '')
            if mime_type != 'application/vnd.google-apps.folder':
                logger.warning(
                    "ID %s is not a folder (mimeType: %s)", folder_id, mime_type)
            return folder_info.get('name', '')
        except HttpError as error:
            logger.error(
                'get_folder_name_by_id: HttpError for folder %s: %s',
                folder_id, error)
            return ''
        except Exception as e:
            logger.error(
                'get_folder_name_by_id: Error getting folder name for %s: %s',
                folder_id, e)
            return ''
