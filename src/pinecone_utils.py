"""
PineCode utilities
"""

import logging

from pinecone import Pinecone

from src.config import load_config

logger = logging.getLogger('PineCone Utils')


class PineconeAssistant:
    """Pinecone Assistant class"""

    def __init__(self):
        config = load_config()
        api_key = config.get('pinecone', {}).get('api_key')
        pc = Pinecone(api_key=api_key)
        # Create an assistant
        self.assistant = pc.assistant.Assistant(
            assistant_name="example-assistant")

    def upload_file(self, file_path: str, metadata: object) -> str:
        """Upload a file to Pinecone Assistant"""
        response = self.assistant.upload_file(
            file_path=file_path,
            metadata=metadata
        )
        logger.info("File uploaded successfully: %s", response.file_id)
        return response.file_id
