"""
Module implements FlowiseAI API with enhanced logging
"""
import logging
import os
import time
import json
from typing import Dict, List, Optional, Any
from functools import wraps

import requests

from src.utils import read_json_secret_file

# import pip._vendor.requests as requests


# Get logger for this module
logger = logging.getLogger('EmailReader.Flowise')


def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Sanitize headers to hide sensitive information
    """
    sanitized = headers.copy()
    sensitive_keys = ['authorization', 'api-key', 'x-api-key', 'bearer']

    for key in sanitized:
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            if sanitized[key]:
                # Show only first 10 and last 4 characters
                value = sanitized[key]
                if len(value) > 20:
                    sanitized[key] = f"{value[:10]}...{value[-4:]}"
                else:
                    sanitized[key] = "***HIDDEN***"

    return sanitized


def truncate_data(data: Any, max_length: int = 500) -> str:
    """
    Truncate data for logging if too long
    """
    data_str = str(data)
    if len(data_str) > max_length:
        return f"{data_str[:max_length]}... (truncated, total length: {len(data_str)})"
    return data_str


def log_http_request(method: str, url: str, **kwargs):
    """
    Log HTTP request details comprehensively
    """
    logger.info("="*80)
    logger.info("HTTP REQUEST: %s %s", method.upper(), url)
    logger.info("-"*80)

    # Log headers (sanitized)
    if 'headers' in kwargs and kwargs['headers']:
        sanitized_headers = sanitize_headers(kwargs['headers'])
        logger.debug("Request Headers: %s", json.dumps(sanitized_headers, indent=2))

    # Log request body/data
    if 'json' in kwargs and kwargs['json']:
        logger.debug("Request JSON Body: %s", truncate_data(kwargs['json']))

    if 'data' in kwargs and kwargs['data'] and not isinstance(kwargs['data'], dict):
        # Don't log binary file data, just metadata
        logger.debug("Request Data: <binary or form data>")
    elif 'data' in kwargs and kwargs['data']:
        logger.debug("Request Data: %s", truncate_data(kwargs['data']))

    if 'files' in kwargs and kwargs['files']:
        logger.debug("Request Files: %s file(s) attached", len(kwargs['files']))

    if 'params' in kwargs and kwargs['params']:
        logger.debug("Request Params: %s", kwargs['params'])

    # Log timeout
    if 'timeout' in kwargs:
        logger.debug("Request Timeout: %s seconds", kwargs['timeout']/1000)


def log_http_response(response: requests.Response, duration: float):
    """
    Log HTTP response details comprehensively
    """
    logger.info("-"*80)
    logger.info("HTTP RESPONSE: Status %s - Duration: %.2f seconds",
                response.status_code, duration)
    logger.info("-"*80)

    # Log response headers
    sanitized_headers = sanitize_headers(dict(response.headers))
    logger.debug("Response Headers: %s", json.dumps(sanitized_headers, indent=2))

    # Log response body (truncated)
    try:
        if response.text:
            # Try to parse as JSON for better formatting
            try:
                response_json = response.json()
                logger.debug("Response Body (JSON): %s", truncate_data(response_json, 1000))
            except:
                logger.debug("Response Body (Text): %s", truncate_data(response.text, 1000))
        else:
            logger.debug("Response Body: <empty>")
    except Exception as e:
        logger.debug("Could not log response body: %s", e)

    # Log response size
    content_length = response.headers.get('content-length')
    if content_length:
        logger.debug("Response Size: %s bytes", content_length)
    else:
        logger.debug("Response Size: %s bytes", len(response.content))

    logger.info("="*80)


class FlowiseAiAPI:
    """
    Adapter class for FlowiseAI API with enhanced logging
    """

    def __init__(self):
        logger.info("Initializing FlowiseAI API client")
        secrets_file = os.path.join(
            os.getcwd(), 'credentials', 'secrets.json')

        logger.debug("Loading secrets from: %s", secrets_file)
        secrets: Dict[str, str] | None = read_json_secret_file(secrets_file)

        if secrets is None:
            logger.error("No secrets file found or it is empty")
            raise ValueError("No secrets file found or it is empty")

        flowise_ai_secrets = secrets.get("flowiseAI")
        if not isinstance(flowise_ai_secrets, dict):
            logger.error("flowiseAI secrets must be a dictionary")
            raise ValueError("flowiseAI secrets must be a dictionary")

        self.API_KEY: str = flowise_ai_secrets.get("API_KEY", "")
        self.API_URL: str = flowise_ai_secrets.get("API_URL")
        self.DOC_STORE_ID: str = flowise_ai_secrets.get("DOC_STORE_ID")
        self.DOC_LOADER_DOCX_ID: str = flowise_ai_secrets.get(
            "DOC_LOADER_DOCX_ID")
        self.CHATFLOW_ID: str = flowise_ai_secrets.get("CHATFLOW_ID")

        logger.info("FlowiseAI API initialized - URL: %s", self.API_URL)
        logger.debug("Document Store ID: %s", self.DOC_STORE_ID)
        logger.debug("Document Loader ID: %s", self.DOC_LOADER_DOCX_ID)

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
        logger.info("Creating new document store: %s", name)

        url = f"{self.API_URL}/document-store/store"
        headers = {"Authorization": f"Bearer {self.API_KEY}",
                   "Content-Type": "application/json"}
        json_body = {"status": "EMPTY", "name": name, "description": description}

        # Log request
        log_http_request("POST", url, headers=headers, json=json_body, timeout=10000)

        # Execute request
        start_time = time.time()
        response = requests.post(
            url=url,
            headers=headers,
            json=json_body,
            timeout=10000,
        )
        duration = time.time() - start_time

        # Log response
        log_http_response(response, duration)

        data = response.json()
        logger.info("Document store created successfully: %s (ID: %s)", name, data.get('id'))
        return data

    def get_list_documents_store(self) -> List[Dict[object, object]]:
        """
        List all document stores

        """
        logger.info("Getting list of all document stores")

        url = f"{self.API_URL}/document-store/store"
        headers = {"Authorization": f"Bearer {self.API_KEY}",
                   "Content-Type": "application/json"}
        json_body = {"status": "EMPTY"}

        # Log request
        log_http_request("GET", url, headers=headers, json=json_body, timeout=10000)

        # Execute request
        start_time = time.time()
        response = requests.get(
            url=url,
            headers=headers,
            json=json_body,
            timeout=10000,
        )
        duration = time.time() - start_time

        # Log response
        log_http_response(response, duration)

        data = response.json()
        logger.info("Retrieved %s document store(s)", len(data) if isinstance(data, list) else 'unknown')
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

        logger.info("Getting document store: %s", store_id)

        url = f"{self.API_URL}/document-store/store/{store_id}"
        headers = {"Authorization": f"Bearer {self.API_KEY}",
                   "Content-Type": "application/json"}
        json_body = {"status": "EMPTY"}

        # Log request
        log_http_request("GET", url, headers=headers, json=json_body, timeout=10000)

        # Execute request
        start_time = time.time()
        response = requests.get(
            url=url,
            headers=headers,
            json=json_body,
            timeout=10000,
        )
        duration = time.time() - start_time

        # Log response
        log_http_response(response, duration)

        data = response.json()
        logger.info("Retrieved document store: %s", data.get('name', store_id))
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

        logger.info("Updating document store: %s", store_id)

        url = f"{self.API_URL}/document-store/store/{store_id}"
        headers = {"Authorization": f"Bearer {self.API_KEY}",
                   "Content-Type": "application/json"}
        json_body = {"status": "EMPTY"}

        # Log request
        log_http_request("PUT", url, headers=headers, json=json_body, timeout=10000)

        # Execute request
        start_time = time.time()
        response = requests.put(
            url=url,
            headers=headers,
            json=json_body,
            timeout=10000,
        )
        duration = time.time() - start_time

        # Log response
        log_http_response(response, duration)

        data = response.json()
        logger.info("Document store updated: %s", store_id)
        return data

    def delete_specific_doc_store(self, store_id: str) -> Dict[object, object]:
        """
        Deletes a document store by its ID
        Args:
            store_id: id of document store
        Returns: {'deleted': 1}
        """
        logger.info("Deleting document store: %s", store_id)

        url = f"{self.API_URL}/document-store/store/{store_id}"
        headers = {"Authorization": f"Bearer {self.API_KEY}",
                   "Content-Type": "application/json"}
        json_body = {"status": "EMPTY"}

        # Log request
        log_http_request("DELETE", url, headers=headers, json=json_body, timeout=10000)

        # Execute request
        start_time = time.time()
        response = requests.delete(
            url=url,
            headers=headers,
            json=json_body,
            timeout=10000,
        )
        duration = time.time() - start_time

        # Log response
        log_http_response(response, duration)

        data = response.json()
        logger.info("Document store deleted: %s (deleted: %s)", store_id, data.get('deleted'))
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
        logger.info("Starting document upsert - Name: %s", doc_name)
        logger.debug("Document path: %s", doc_path)

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
            logger.debug(f"Document size: {file_size:.2f} MB")

            if store_id is None:
                store_id = self.DOC_STORE_ID
                logger.debug("Using default store ID: %s", store_id)

            if loader_id is None:
                loader_id = self.DOC_LOADER_DOCX_ID
                logger.debug("Using default loader ID: %s", loader_id)

            # Prepare the request
            logger.debug("Preparing request to Flowise API")

            url = f"{self.API_URL}/document-store/upsert/{store_id}"
            headers = {"Authorization": f"Bearer {self.API_KEY}"}
            body_data = {"docId": loader_id}

            with open(doc_path, 'rb') as file:
                form_data = {"files": (doc_name, file)}

                # Log request (before opening file to avoid binary data in logs)
                log_http_request("POST", url, headers=headers, data=body_data,
                               files={'files': doc_name}, timeout=60000)

                # Execute request
                start_time = time.time()
                response = requests.post(
                    url=url,
                    files=form_data,
                    data=body_data,
                    headers=headers,
                    timeout=60000
                )
                duration = time.time() - start_time

            # Log response
            log_http_response(response, duration)

            if response.status_code == 200:
                data = response.json()
                logger.info("Document successfully uploaded: %s", doc_name)
                return data
            else:
                logger.error("Upload failed with status %s", response.status_code)
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

        logger.info("Getting document page: store=%s, doc=%s, page=%s", store_id, doc_id, page)

        url = f"{self.API_URL}/document-store/chunks/{store_id}/{doc_id}/{page}"
        headers = {"Authorization": f"Bearer {self.API_KEY}",
                   "Content-Type": "application/json"}
        json_body = {"status": "EMPTY"}

        # Log request
        log_http_request("GET", url, headers=headers, json=json_body, timeout=10000)

        # Execute request
        start_time = time.time()
        response = requests.get(
            url=url,
            headers=headers,
            json=json_body,
            timeout=10000
        )
        duration = time.time() - start_time

        # Log response
        log_http_response(response, duration)

        data = response.json()
        chunk_count = data.get('count', 0)
        logger.info("Retrieved document page %s with %s chunks", page, chunk_count)
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

        logger.info("Updating documents in store: %s", store_id)

        url = f"{self.API_URL}/document-store/store/{store_id}"
        headers = {"Authorization": f"Bearer {self.API_KEY}",
                   "Content-Type": "application/json"}
        json_body = {"status": "EMPTY"}

        # Log request
        log_http_request("PUT", url, headers=headers, json=json_body, timeout=10000)

        # Execute request
        start_time = time.time()
        response = requests.put(
            url=url,
            headers=headers,
            json=json_body,
            timeout=10000,
        )
        duration = time.time() - start_time

        # Log response
        log_http_response(response, duration)

        data = response.json()
        logger.info("Documents in store updated: %s", store_id)
        return data

    def create_new_prediction(self, doc_name: str) -> Dict[object, object]:
        """
        Create new prediction with enhanced logging
        """
        logger.info("Creating prediction for document: %s", doc_name)

        try:
            url = f"{self.API_URL}/prediction/{self.CHATFLOW_ID}"
            headers = {"Authorization": f"Bearer {self.API_KEY}"}
            data_body: Dict[str, object] = {
                "question": doc_name,
                "overrideConfig": {},
                "history": []
            }

            # Log request
            log_http_request("POST", url, headers=headers, json=data_body, timeout=30000)

            # Execute request
            start_time = time.time()
            response = requests.post(
                url=url,
                json=data_body,
                headers=headers,
                timeout=30000
            )
            duration = time.time() - start_time

            # Log response
            log_http_response(response, duration)

            if response.status_code == 200:
                # Check if response has content before trying to parse JSON
                if response.text:
                    data = response.json()
                    logger.info("Prediction created successfully for: %s", doc_name)
                    return data
                else:
                    logger.warning("Received empty response body with status 200")
                    return {'name': 'Success', 'id': 'empty_response'}
            else:
                logger.error("Prediction failed with status %s", response.status_code)
                return {
                    'name': 'Error',
                    'id': f'HTTP {response.status_code}'
                }

        except Exception as error:
            logger.error("Error creating prediction: %s", error, exc_info=True)
            return {'name': 'Error', 'id': str(error)}
