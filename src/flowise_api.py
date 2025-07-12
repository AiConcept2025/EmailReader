"""
Module implements FlowiseAI API
"""
import os
from typing import Dict, List
# import requests
import pip._vendor.requests as requests

from src.utils import read_json_secret_file


class FlowiseAiAPI:
    """
    Adapter class for FlowiseAI API
    """

    def __init__(self):
        secrets_file = os.path.join(
            os.getcwd(), 'credentials', 'secrets.json')
        secrets: Dict[str, str] | None = read_json_secret_file(secrets_file)
        if secrets is None:
            raise ValueError("No secrets file found or it is empty")
        flowise_ai_secrets = secrets.get("flowiseAI")
        if not isinstance(flowise_ai_secrets, dict):
            raise ValueError("flowiseAI secrets must be a dictionary")
        self.API_KEY = flowise_ai_secrets.get("API_KEY", "")
        self.API_URL = flowise_ai_secrets.get("API_URL")
        self.DOC_STORE_ID = flowise_ai_secrets.get("DOC_STORE_ID")
        self.DOC_LOADER_DOCX_ID = flowise_ai_secrets.get("DOC_LOADER_DOCX_ID")
        self.CHATFLOW_ID = flowise_ai_secrets.get("CHATFLOW_ID")

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
        Upsert document to document store
        """
        try:
            if doc_name is None:
                return {'name': 'Error', 'error': 'No document name provided'}
            if store_id is None:
                store_id = self.DOC_STORE_ID
            if loader_id is None:
                loader_id = self.DOC_LOADER_DOCX_ID
            form_data = {
                "files": (doc_name, open(doc_path, 'rb'))
            }
            body_data = {
                "docId": self.DOC_LOADER_DOCX_ID
            }
            headers = {
                "Authorization": f"Bearer {self.API_KEY}"
            }

            response = requests.post(
                url=f"{self.API_URL}/document-store/upsert/{store_id}",
                files=form_data,
                data=body_data,
                headers=headers,
                timeout=60000
            )
            data = response.json()
            return data
        except Exception as error:
            print(f'Upsert document to document store: {error}')
            return {'name': 'Error', 'error': error}

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

    def create_new_prediction(self, question: str) -> Dict[object, object]:
        """
        Create a new prediction
        Returns:
        {
            "text": "text",
            "json": {},
            "question": "text",
            "chatId": "text",
            "chatMessageId": "text",
            "sessionId": "text",
            "memoryType": "text",
            "sourceDocuments": [
                {
                "pageContent": "This is the content of the page.",
                "metadata": {
                    "author": "John Doe",
                    "date": "2024-08-24"
                }
                }
            ],
            "usedTools": [
                {
                "tool": "Name of the tool",
                "toolOutput": "text",
                "toolInput": {
                    "input": "search query"
                }
                }
            ],
            "fileAnnotations": [
                {
                "filePath": "path/to/file",
                "fileName": "file.txt"
                }
            ]
        }
        """
        try:
            data_body: Dict[str, object] = {
                "overrideConfig": {},
                "history": [{
                    "content": question,
                    "role": "apiMessage"}],
                "question": question,

                "uploads": [{
                    "type": "file",
                    "name": "image.png",
                    "data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAABjElEQVRIS+2Vv0oDQRDG",
                    "mime": "image/png"}]
            }
            response = requests.post(
                url=f"{self.API_URL}/prediction/{self.CHATFLOW_ID}",
                headers={"Authorization": f"Bearer {self.API_KEY}"},
                data=data_body,
                timeout=300000
            )
            data = response.json()
            return data
        except requests.RequestException as error:
            print(f'Create a new prediction: {error}')
            return {'name': 'Error', 'error': str(error)}
