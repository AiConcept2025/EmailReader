import requests
import json


# DOC_STORE_ID = "3bb31829-3657-4575-92bd-74e2d424805f"
# DOC_LOADER_ID = "cb6ff3e3-6a65-49e8-9b64-1da8b448d9a4"
# API_URL = "http://localhost:3000/api/v1/document-store/"
# API_KEY = "c2C78pJoezokK91qnqrdkeagWav6vRDTOkaY5XEhY-U"

DOC_STORE_ID = "01aebc69-b969-45d8-9ed6-f7a9146c16e3"
DOC_LOADER_ID = '9c4413bf-d7af-45a4-aaff-2d8ca06760de'
API_URL = "http://74.208.74.244:4000/api/v1/document-store"
API_KEY = "jf38F2NpoiHaWrQTzSTapIrQCHpuLOMNgyWd4zht9RM"
API_KEY_1 = "d9c4eHnHVRML7ckQSQhOTQethhnAgJQy-ufhvwy34YU"


def get_list_documents_store():
    """
    List all document stores
    """
    response1 = requests.get(
        url=f"{API_URL}/store",
        headers={"Authorization": f"Bearer {API_KEY_1}",
                 "Content-Type": "application/json"},
        json={"status": "EMPTY"},
        timeout=1000,
    )

    data = response1.json()
    print(data)
    return data


def get_specific_doc_store():
    """
    Get a specific document store
    """
    response1 = requests.get(
        url=f"{API_URL}/store/{DOC_STORE_ID}",
        headers={"Authorization": f"Bearer {API_KEY}",
                 "Content-Type": "application/json"},
        json={"status": "EMPTY"},
        timeout=1000,
    )

    data = response1.json()
    print(data)
    return data


get_list_documents_store()
# get_specific_doc_store()


form_data = {
    "files": ('flowise.docx', open('flowise.docx', 'rb'))
}

body_data = {
    "docId": DOC_LOADER_ID
}

headers = {
    "Authorization": f"Bearer {API_KEY}"
}


def query(form_data):
    response = requests.post(
        url=f"{API_URL}/upsert/{DOC_STORE_ID}",
        files=form_data,
        data=body_data,
        headers=headers,
        timeout=10000
    )
    print(response)
    return response.json()


output = query(form_data)
print(output)
