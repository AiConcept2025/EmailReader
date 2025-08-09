"""
Module implements FlowiseAI API with enhanced logging
"""
import os
import uuid
from typing import Dict, List
import requests
import logging
# import pip._vendor.requests as requests

from src.utils import read_json_secret_file

# Get logger for this module
logger = logging.getLogger('EmailReader.Flowise')


class FlowiseAiAPI:
    """
    Adapter class for FlowiseAI API with enhanced logging
    """

    def __init__(self):
        logger.info("Initializing FlowiseAI API client")
        secrets_file = os.path.join(
            os.getcwd(), 'credentials', 'secrets.json')
        
        logger.debug(f"Loading secrets from: {secrets_file}")
        secrets: Dict[str, str] | None = read_json_secret_file(secrets_file)
        
        if secrets is None:
            logger.error("No secrets file found or it is empty")
            raise ValueError("No secrets file found or it is empty")
            
        flowise_ai_secrets = secrets.get("flowiseAI")
        if not isinstance(flowise_ai_secrets, dict):
            logger.error("flowiseAI secrets must be a dictionary")
            raise ValueError("flowiseAI secrets must be a dictionary")
            
        self.API_KEY = flowise_ai_secrets.get("API_KEY", "")
        self.API_URL = flowise_ai_secrets.get("API_URL")
        self.DOC_STORE_ID = flowise_ai_secrets.get("DOC_STORE_ID")
        self.DOC_LOADER_DOCX_ID = flowise_ai_secrets.get("DOC_LOADER_DOCX_ID")
        self.CHATFLOW_ID = flowise_ai_secrets.get("CHATFLOW_ID")
        
        logger.info(f"FlowiseAI API initialized - URL: {self.API_URL}")
        logger.debug(f"Document Store ID: {self.DOC_STORE_ID}")
        logger.debug(f"Document Loader ID: {self.DOC_LOADER_DOCX_ID}")

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
            loader_id: str | None = None) -> Dict[object, object]:
        """
        Upsert document to document store with enhanced logging
        """
        logger.info(f"Starting document upsert - Name: {doc_name}")
        logger.debug(f"Document path: {doc_path}")
        
        try:
            # Validate inputs
            if doc_name is None:
                logger.error("No document name provided")
                return {'name': 'Error', 'error': 'No document name provided'}
                
            if not os.path.exists(doc_path):
                logger.error(f"Document file not found: {doc_path}")
                return {'name': 'Error', 'error': f'File not found: {doc_path}'}
                
            # Get file size for logging
            file_size = os.path.getsize(doc_path) / (1024 * 1024)  # Size in MB
            logger.debug(f"Document size: {file_size:.2f} MB")
            
            if store_id is None:
                store_id = self.DOC_STORE_ID
                logger.debug(f"Using default store ID: {store_id}")
                
            if loader_id is None:
                loader_id = self.DOC_LOADER_DOCX_ID
                logger.debug(f"Using default loader ID: {loader_id}")
                
            # Prepare the request
            logger.debug("Preparing request to Flowise API")
            
            with open(doc_path, 'rb') as file:
                form_data = {
                    "files": (doc_name, file)
                }
                body_data = {
                    "docId": loader_id
                }
                headers = {
                    "Authorization": f"Bearer {self.API_KEY}"
                }
                
                url = f"{self.API_URL}/document-store/upsert/{store_id}"
                logger.debug(f"POST request to: {url}")
                
                response = requests.post(
                    url=url,
                    files=form_data,
                    data=body_data,
                    headers=headers,
                    timeout=60000
                )
                
            # Log response status
            logger.debug(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Document successfully uploaded: {doc_name}")
                logger.debug(f"Response data: {data}")
                return data
            else:
                logger.error(f"Upload failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {
                    'name': 'Error', 
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while uploading document: {doc_name}")
            return {'name': 'Error', 'error': 'Request timeout'}
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error while uploading document: {e}")
            return {'name': 'Error', 'error': f'Connection error: {str(e)}'}
            
        except Exception as error:
            logger.error(f'Unexpected error during document upload: {error}', exc_info=True)
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
            url=f"{self.API_URL}/document-store/chunks/{store_id}/{doc_id}/{page}",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY"},
            timeout=10000
        )
        data = response.json()
        return data

    def update_docs_in_store(self, store_id: str | None) -> Dict[object, object]:
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
        logger.info(f"Creating prediction for document: {doc_name}")
        
        try:
            # Use the original Flowise API endpoint (without /api/v1/)
            url = f"{self.API_URL}/prediction/{self.CHATFLOW_ID}"
            headers = {
                "Authorization": f"Bearer {self.API_KEY}"
            }
            
            # Use the original body structure that was working
            data_body = {
                "question": doc_name,
                "overrideConfig": {},
                "history": []
            }
            
            logger.debug(f"POST request to: {url}")
            
            response = requests.post(
                url=url,
                json=data_body,  # Use json parameter for proper content-type
                headers=headers,
                timeout=30000
            )
            
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            
            if response.status_code == 200:
                # Check if response has content before trying to parse JSON
                if response.text:
                    data = response.json()
                    logger.info(f"Prediction created successfully for: {doc_name}")
                    return data
                else:
                    logger.warning("Received empty response body with status 200")
                    return {'name': 'Success', 'id': 'empty_response'}
            else:
                logger.error(f"Prediction failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {
                    'name': 'Error',
                    'id': f'HTTP {response.status_code}'
                }
                
        except Exception as error:
            logger.error(f"Error creating prediction: {error}", exc_info=True)
            return {'name': 'Error', 'id': str(error)}
