"""
Module implements FlowiseAI API
"""

from typing import Dict

import requests

from utils import read_json_secret_file


class FlowiseAiAPI:
    """
    Adapter class for FlowiseAI API
    """

    def __init__(self):
        secrets: Dict = read_json_secret_file("secrets.json")
        flowiseAI_secrets = secrets.get("flowiseAI")
        self.API_KEY = flowiseAI_secrets.get("API_KEY")
        self.API_URL = flowiseAI_secrets.get("API_URL")
        self.DOC_STORE_ID = flowiseAI_secrets.get("DOC_STORE_ID")
        self.DOC_LOADER_DOCX_ID = flowiseAI_secrets.get("DOC_LOADER_DOCX_ID")

    def create_new_doc_store(self):  # ??
        """
        Create a new document store
        """
        response1 = requests.post(
            url=f"{self.API_URL}/store",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY"},
            timeout=1000,
        )
        data = response1.json()
        print(data)
        return data

    def get_list_documents_store(self):
        """
        List all document stores
        """
        response1 = requests.get(
            url=f"{self.API_URL}/store",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY"},
            timeout=1000,
        )
        data = response1.json()
        print(data)
        return data

    def get_specific_doc_store(self, store_id: str):
        """
        Get a specific document store
        """
        if store_id is None:
            store_id = self.DOC_STORE_ID
        response1 = requests.get(
            url=f"{self.API_URL}/store/{store_id}",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY"},
            timeout=1000,
        )
        data = response1.json()
        print(data)
        return data

    def update_specific_doc_store(self, store_id: str):
        """
        Get a specific document store
        """
        if store_id is None:
            store_id = self.DOC_STORE_ID
        response1 = requests.put(
            url=f"{self.API_URL}/store/{store_id}",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY"},
            timeout=1000,
        )
        data = response1.json()
        print(data)
        return data

    def delete_specific_doc_store(self, store_id: str):
        """
        Deletes a document store by its ID
        """
        if store_id is None:
            store_id = self.DOC_STORE_ID
        response1 = requests.delete(
            url=f"{self.API_URL}/store/{store_id}",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY"},
            timeout=1000,
        )
        data = response1.json()
        print(data)
        return data

    def get_document_page(self, store_id: str, loader_id: str, page: int = 0):
        """
            Read page from document store
        """
        if store_id is None:
            store_id = self.DOC_STORE_ID
        if loader_id is None:
            loader_id = self.DOC_LOADER_DOCX_ID
        response1 = requests.get(
            url=f"{self.API_URL}/chunks/{store_id}/{loader_id}/{page}",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY"},
            timeout=10000
        )
        data = response1.json()
        pageContent = data.get('chunks')[0].get('pageContent')
        print(pageContent)
        return pageContent

    def update_docs_in_store(self, store_id):
        """
        Update document in the store and returns
        doc store info
        """
        if store_id is None:
            store_id = self.DOC_STORE_ID
        response1 = requests.put(
            url=f"{self.API_URL}/store/{store_id}",
            headers={"Authorization": f"Bearer {self.API_KEY}",
                     "Content-Type": "application/json"},
            json={"status": "EMPTY"},
            timeout=1000,
        )
        data = response1.json()
        print(data)
        return data

    def upload_doc_to_doc_store(self, doc_name: str, store_id: str, loader_id: str):
        """
        Upload document to the store
        """
        if doc_name is None:
            return
        if store_id is None:
            store_id = self.DOC_STORE_ID
        if loader_id is None:
            loader_id = self.DOC_LOADER_DOCX_ID
        form_data = {
            "files": (doc_name, open(doc_name, 'rb'))
        }
        body_data = {
            "docId": store_id
        }
        headers = {
            "Authorization": f"Bearer {self.API_KEY}"
        }
        response = requests.post(
            url=f"{self.API_URL}/upsert/{store_id}",
            files=form_data,
            data=body_data,
            headers=headers,
            timeout=10000
        )
        print(response)
        return response.json()
