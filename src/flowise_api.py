"""
Module implements FlowiseAI API with enhanced logging
"""
import json
import logging
import os
# import uuid
from typing import Dict, List

import requests

from src.config import load_config

# import pip._vendor.requests as requests


# Get logger for this module
logger = logging.getLogger('EmailReader.Flowise')


class FlowiseAiAPI:
    """
    Adapter class for FlowiseAI API with enhanced logging
    """

    def __init__(self):
        logger.info("Initializing FlowiseAI API client")

        # Load configuration
        config = load_config()

        if 'flowise' not in config:
            logger.error("'flowise' section not found in configuration")
            raise ValueError("'flowise' section not found in configuration")

        flowise_config = config['flowise']
        if not isinstance(flowise_config, dict):
            logger.error("flowise configuration must be a dictionary")
            raise ValueError("flowise configuration must be a dictionary")

        self.API_KEY: str = flowise_config.get("api_key", "")
        self.API_URL: str = flowise_config.get("api_url")
        self.DOC_STORE_ID: str = flowise_config.get("doc_store_id")
        self.DOC_LOADER_DOCX_ID: str = flowise_config.get("doc_loader_docx_id")
        self.CHATFLOW_ID: str = flowise_config.get("chatflow_id")

        logger.info("FlowiseAI API initialized - URL: %s", self.API_URL)
        logger.debug("Document Store ID: %s", self.DOC_STORE_ID)
        logger.debug("Document Loader ID: %s", self.DOC_LOADER_DOCX_ID)
        logger.debug("Chatflow ID: %s", self.CHATFLOW_ID)

    def create_new_doc_store(
            self,
            name: str,
            description: str | None = None
    ) -> Dict[object, object]:
        """
        Create a new document store
        Args:
            name: name of new store
            description
        Return:
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "text",
                "description": "text",
                "loaders": "text",
                "whereUsed": "text",
                "vectorStoreConfig": "text",
                "embeddingConfig": "text",
                "recordManagerConfig": "text",
                "createdDate": "2025-03-01T09:42:53.090Z",
                "updatedDate": "2025-03-01T09:42:53.090Z",
                "status": "EMPTY"
            }
        """
        response = requests.post(
            url=f"{self.API_URL}/document-store/store",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY",
                  "name": name,
                  "description": description, },
            timeout=10000,
        )
        data = response.json()
        return data

    def get_list_documents_store(self) -> List[Dict[object, object]]:
        """
        List all document stores

        """
        response = requests.get(
            url=f"{self.API_URL}/document-store/store",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={
                "status": "EMPTY"
            },
            timeout=10000,  # 10 sec
        )
        data = response.json()
        return data

    def get_specific_doc_store(
            self,
            store_id: str | None = None
    ) -> Dict[object, object]:
        """
        Get a specific document store
        Args:
            store_id: id of document store
        """
        if store_id is None:
            store_id = self.DOC_STORE_ID
        response = requests.get(
            url=f"{self.API_URL}/document-store/store/{store_id}",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY"},
            timeout=10000,
        )
        data = response.json()
        return data

    def update_specific_doc_store(
            self,
            store_id: str | None = None
    ) -> Dict[object, object]:
        """
        Updates the details of a specific document store by its ID
        Args:
            store_id: id of document store
        """
        if store_id is None:
            store_id = self.DOC_STORE_ID
        response = requests.put(
            url=f"{self.API_URL}/document-store/store/{store_id}",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY"},
            timeout=10000,
        )
        data = response.json()
        return data

    def delete_specific_doc_store(self, store_id: str) -> Dict[object, object]:
        """
        Deletes a document store by its ID
        Args:
            store_id: id of document store
        Returns: {'deleted': 1}
        """
        response = requests.delete(
            url=f"{self.API_URL}/document-store/store/{store_id}",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY"},
            timeout=10000,
        )
        data = response.json()
        return data

    def upsert_document_to_document_store(
            self,
            doc_path: str,
            doc_name: str | None = None,
            store_id: str | None = None,
            loader_id: str | None = None,
            metadata: Dict[str, str] | None = None) -> Dict[object, object]:
        """
        Upsert document to document store with enhanced logging

        Args:
            doc_path: Path to the document file
            doc_name: Name of the document
            store_id: Document store ID (uses default if None)
            loader_id: Document loader ID (uses default if None)
            metadata: Optional metadata dict to attach to the document
        """
        logger.info("Starting document upsert - Name: %s", doc_name)
        logger.debug("Document path: %s", doc_path)
        if metadata:
            logger.debug("Metadata provided: %s", metadata)

        try:
            # Validate inputs
            if doc_name is None:
                logger.error("No document name provided")
                return {'name': 'Error', 'error': 'No document name provided'}

            if not os.path.exists(doc_path):
                logger.error("Document file not found: %s", doc_path)
                return {'name': 'Error', 'error': f'File not found: {doc_path}'}

            # Get file size for logging
            file_size = os.path.getsize(doc_path) / (1024 * 1024)  # Size in MB
            logger.debug("Document size: %.2f MB", file_size)

            if store_id is None:
                store_id = self.DOC_STORE_ID
                logger.debug("Using default store ID: %s", store_id)

            if loader_id is None:
                loader_id = self.DOC_LOADER_DOCX_ID
                logger.debug("Using default loader ID: %s", loader_id)

            # Prepare the request
            logger.debug("Preparing request to Flowise API")

            # Note: File was already sanitized during translation step
            # No need for additional sanitization here
            file_to_upload = doc_path
            temp_sanitized_path = None

            with open(file_to_upload, 'rb') as file:
                # Use ASCII-safe filename in the upload to avoid encoding issues
                # The original filename is preserved in metadata
                import string
                safe_chars = string.ascii_letters + string.digits + '.-_'
                ascii_filename = ''.join(c if c in safe_chars else '_' for c in doc_name)
                logger.debug("Original filename: %s", doc_name)
                logger.debug("Upload filename (ASCII-safe): %s", ascii_filename)

                form_data = {
                    "files": (ascii_filename, file, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                }

                # Add metadata field if provided
                # Store original filename in metadata to preserve it
                if metadata is None:
                    metadata = {}

                # Add original filename to metadata
                metadata['original_filename'] = doc_name

                # Explicitly encode metadata as UTF-8 bytes to prevent encoding issues
                metadata_json = json.dumps(metadata, ensure_ascii=False)
                metadata_bytes = metadata_json.encode('utf-8')
                form_data["metadata"] = (
                    None, metadata_bytes, 'application/json; charset=utf-8')
                logger.debug("Added UTF-8 encoded metadata with original filename: %s", doc_name)

                body_data = {
                    "docId": loader_id
                }
                headers = {
                    "Authorization": f"Bearer {self.API_KEY}"
                }

                url = f"{self.API_URL}/document-store/upsert/{store_id}"
                logger.debug("POST request to: %s", url)

                response = requests.post(
                    url=url,
                    files=form_data,
                    data=body_data,
                    headers=headers,
                    timeout=60000
                )

            # Log response status
            logger.debug("Response status code: %s", response.status_code)

            if response.status_code == 200:
                data = response.json()
                logger.info("Document successfully uploaded: %s", doc_name)
                logger.debug("Response data: %s", data)
                return data
            else:
                logger.error(
                    "Upload failed with status %s", response.status_code)
                logger.error("Response: %s", response.text)
                return {
                    'name': 'Error',
                    'error': f'HTTP {response.status_code}: {response.text}'
                }

        except requests.exceptions.Timeout:
            logger.error("Timeout while uploading document: %s", doc_name)
            return {'name': 'Error', 'error': 'Request timeout'}

        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error while uploading document: %s", e)
            return {'name': 'Error', 'error': f'Connection error: {str(e)}'}

        except Exception as error:
            logger.error(
                'Unexpected error during document upload: %s',
                error,
                exc_info=True)
            return {'name': 'Error', 'error': str(error)}

    def get_document_page(
            self,
            store_id: str | None,
            doc_id: str | None, page: int = 0
    ) -> Dict[object, object]:
        """
            Read page from document store
            Args:
                store_id
                doc_id
                page
            Return:
            {
                'chunks': [],
                'count': 14,
                'file': {
                    'id': '418234e6-68cc-4fd9-92fe-2a2513f2fad8',
                    'loaderId': 'docxFile',
                    'loaderName': 'Docx File',
                    'loaderConfig': {...},
                    'splitterId': 'characterTextSplitter',
                    'splitterName': 'Character Text Splitter',
                    'splitterConfig': {...},
                    'totalChunks': 14,
                    'totalChars': 9854,
                    'status': 'EMPTY',
                    'files': [...]},
                'currentPage': 1,
                'storeName': 'Document Store 1740194744531',
                'description': None,
                'docId': '418234e6-68cc-4fd9-92fe-2a2513f2fad8',
                'characters': 9854
                }
        """
        if store_id is None:
            store_id = self.DOC_STORE_ID
        if doc_id is None:
            doc_id = self.DOC_LOADER_DOCX_ID
        response = requests.get(
            url=(f"{self.API_URL}/document-store/chunks/"
                 f"{store_id}/{doc_id}/{page}"),
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY"},
            timeout=10000
        )
        data = response.json()
        return data

    def update_docs_in_store(
            self,
            store_id: str | None
    ) -> Dict[object, object]:
        """
        Update document in the store and returns
        doc store info
        """
        if store_id is None:
            store_id = self.DOC_STORE_ID
        response = requests.put(
            url=f"{self.API_URL}/document-store/store/{store_id}",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY"},
            timeout=10000,
        )
        data = response.json()
        return data

    def create_new_prediction(self, doc_name: str) -> Dict[object, object]:
        """
        Create new prediction with enhanced logging
        """
        logger.info("Creating prediction for document: %s", doc_name)

        try:
            # Use the original Flowise API endpoint (without /api/v1/)
            url = f"{self.API_URL}/prediction/{self.CHATFLOW_ID}"
            headers = {
                "Authorization": f"Bearer {self.API_KEY}",
                "Content-Type": "application/json"
            }

            # Use simplified body structure with streaming flag
            data_body: Dict[str, object] = {
                "question": doc_name,
                "streaming": False
            }

            logger.debug("POST request to: %s", url)

            response = requests.post(
                url=url,
                json=data_body,  # Use json parameter for proper content-type
                headers=headers,
                timeout=30000
            )

            logger.debug("Response status code: %s", response.status_code)
            logger.debug("Response headers: %s", response.headers)

            if response.status_code == 200:
                # Check if response has content before trying to parse JSON
                if response.text:
                    data = response.json()
                    logger.info(
                        "Prediction created successfully for: %s", doc_name)
                    return data
                else:
                    logger.warning(
                        "Received empty response body with status 200")
                    return {'name': 'Success', 'id': 'empty_response'}
            else:
                logger.error(
                    "Prediction failed with status %s", response.status_code)
                logger.error("Response: %s", response.text)
                return {
                    'name': 'Error',
                    'id': f'HTTP {response.status_code}'
                }

        except Exception as error:
            logger.error("Error creating prediction: %s", error, exc_info=True)
            return {'name': 'Error', 'id': str(error)}
