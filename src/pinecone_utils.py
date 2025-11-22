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
        if not api_key:
            logger.error("Pinecone API key not found in configuration")
            raise ValueError(
                "Pinecone API key is required. Please set 'pinecone.api_key' in config"
            )

        try:
            pc = Pinecone(api_key=api_key)
            # Create an assistant
            self.assistant = pc.assistant.Assistant(
                assistant_name="example-assistant")
            logger.info("Pinecone Assistant initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Pinecone Assistant: %s", e)
            raise

    def upload_file(self, file_path: str, metadata: object) -> str:
        """
        Upload a file to Pinecone Assistant.

        Args:
            file_path (str): Path to the file to upload
            metadata (object): Dictionary containing file metadata

        Returns:
            str: The unique file ID assigned by Pinecone

        Raises:
            Exception: If the upload fails

        Example:
            >>> assistant = PineconeAssistant()
            >>> file_id = assistant.upload_file(
            ...     file_path="/path/to/document.pdf",
            ...     metadata={"client": "user@example.com", "type": "invoice"}
            ... )
        """
        try:
            response = self.assistant.upload_file(
                file_path=file_path,
                metadata=metadata
            )
            logger.info("File uploaded successfully: %s", response.id)
            return response.id
        except Exception as e:
            logger.error("Failed to upload file %s: %s", file_path, e)
            raise

    def query_documents(
        self,
        query_text: str,
        top_k: int = 5,
        filter: dict = None
    ) -> dict:
        """
        Query/search documents by text using the Pinecone Assistant.

        This method retrieves relevant document context based on a text query.
        It uses the assistant's context() method to find matching documents.

        Args:
            query_text (str): The search query text
            top_k (int, optional): Number of top results to return. Defaults to 5.
            filter (dict, optional): Metadata filters to narrow down search.
                Example: {"client_email": "user@example.com"}

        Returns:
            dict: Search results containing relevant document chunks and metadata

        Raises:
            Exception: If the query fails

        Example:
            >>> assistant = PineconeAssistant()
            >>> results = assistant.query_documents(
            ...     query_text="What is the total amount?",
            ...     top_k=3,
            ...     filter={"client_email": "user@example.com"}
            ... )
        """
        try:
            logger.info(
                "Querying documents with text: '%s' (top_k=%d)",
                query_text[:100], top_k
            )
            if filter:
                logger.debug("Applying filter: %s", filter)

            response = self.assistant.context(
                query=query_text,
                filter=filter,
                top_k=top_k
            )
            logger.info("Query completed successfully")
            return response
        except Exception as e:
            logger.error("Failed to query documents: %s", e)
            raise

    def delete_file(self, file_id: str) -> None:
        """
        Delete a document by its file ID.

        Args:
            file_id (str): The unique ID of the file to delete

        Raises:
            Exception: If the deletion fails

        Example:
            >>> assistant = PineconeAssistant()
            >>> assistant.delete_file(file_id="file-abc123")
        """
        try:
            logger.info("Deleting file with ID: %s", file_id)
            self.assistant.delete_file(file_id=file_id)
            logger.info("File deleted successfully: %s", file_id)
        except Exception as e:
            logger.error("Failed to delete file %s: %s", file_id, e)
            raise

    def list_files(
        self,
        filter: dict = None,
        limit: int = 100
    ) -> list:
        """
        List uploaded documents with optional filtering.

        Note: The Pinecone Assistant API does not natively support a limit parameter.
        This method retrieves all files matching the filter and returns the first
        'limit' results.

        Args:
            filter (dict, optional): Metadata filters to narrow down results.
                Example: {"client_email": "user@example.com"}
            limit (int, optional): Maximum number of files to return. Defaults to 100.

        Returns:
            list: List of file objects with metadata. Each file contains:
                - id: File ID
                - name: File name
                - status: Processing status
                - metadata: Custom metadata
                - created_on: Creation timestamp
                - updated_on: Last update timestamp
                - size: File size in bytes
                - percent_done: Processing completion percentage

        Raises:
            Exception: If listing files fails

        Example:
            >>> assistant = PineconeAssistant()
            >>> files = assistant.list_files(
            ...     filter={"client_email": "user@example.com"},
            ...     limit=50
            ... )
            >>> for file in files:
            ...     print(f"{file.name} - {file.status}")
        """
        try:
            logger.info("Listing files (limit=%d)", limit)
            if filter:
                logger.debug("Applying filter: %s", filter)

            files = self.assistant.list_files(filter=filter)
            logger.info("Retrieved %d file(s)", len(files))

            # Apply limit manually since API doesn't support it
            if len(files) > limit:
                logger.debug("Limiting results to first %d files", limit)
                files = files[:limit]

            return files
        except Exception as e:
            logger.error("Failed to list files: %s", e)
            raise

    def get_file_metadata(self, file_id: str) -> dict:
        """
        Get metadata and details for a specific file.

        Args:
            file_id (str): The unique ID of the file

        Returns:
            dict: File details including:
                - id: File ID
                - name: File name
                - status: Processing status
                - metadata: Custom metadata dictionary
                - created_on: Creation timestamp
                - updated_on: Last update timestamp
                - size: File size in bytes
                - percent_done: Processing completion percentage (0.0 to 1.0)
                - error_message: Error message if status is 'Failed'

        Raises:
            Exception: If fetching file metadata fails

        Example:
            >>> assistant = PineconeAssistant()
            >>> metadata = assistant.get_file_metadata(file_id="file-abc123")
            >>> print(f"Status: {metadata['status']}")
            >>> print(f"Metadata: {metadata['metadata']}")
        """
        try:
            logger.info("Fetching metadata for file ID: %s", file_id)
            file_model = self.assistant.describe_file(file_id=file_id)

            # Convert FileModel to dict for easier use
            result = {
                'id': file_model.id,
                'name': file_model.name,
                'status': file_model.status,
                'metadata': file_model.metadata,
                'created_on': file_model.created_on,
                'updated_on': file_model.updated_on,
                'size': file_model.size,
                'percent_done': file_model.percent_done,
                'error_message': file_model.error_message,
                'multimodal': file_model.multimodal
            }

            logger.info(
                "File metadata retrieved: %s (status: %s)",
                file_model.name,
                file_model.status
            )
            return result
        except Exception as e:
            logger.error("Failed to get file metadata for %s: %s", file_id, e)
            raise

    def update_metadata(self, file_id: str, metadata: dict) -> dict:
        """
        Update file metadata.

        Note: The Pinecone Assistant API does not provide a direct method to update
        file metadata after upload. This method provides a workaround by:
        1. Retrieving the current file details
        2. Logging the limitation
        3. Returning current metadata

        To update metadata, you would need to:
        - Delete the old file
        - Re-upload with new metadata

        Args:
            file_id (str): The unique ID of the file
            metadata (dict): New metadata dictionary to set

        Returns:
            dict: Current file metadata (unchanged)

        Raises:
            NotImplementedError: This method is not fully supported by Pinecone API

        Example:
            >>> assistant = PineconeAssistant()
            >>> try:
            ...     updated = assistant.update_metadata(
            ...         file_id="file-abc123",
            ...         metadata={"status": "processed", "reviewed": True}
            ...     )
            ... except NotImplementedError:
            ...     print("Metadata update not supported, re-upload required")
        """
        logger.warning(
            "Pinecone Assistant API does not support direct metadata updates"
        )
        logger.info(
            ("To update metadata for file %s, you must delete and "
             "re-upload the file"),
            file_id
        )
        logger.debug("Requested metadata update: %s", metadata)

        # Return current metadata
        current = self.get_file_metadata(file_id)
        logger.info("Current metadata returned (not updated)")

        raise NotImplementedError(
            "Pinecone Assistant API does not support updating file metadata. "
            "To change metadata, delete the file and re-upload with new metadata."
        )

    def chat(
        self,
        messages: list,
        filter: dict = None,
        model: str = None,
        temperature: float = None
    ) -> dict:
        """
        Chat with the assistant using conversation history.

        This is a bonus method that enables conversational AI interactions
        with the assistant using uploaded documents as context.

        Args:
            messages (list): List of message dictionaries with 'role' and 'content'.
                Example: [{"role": "user", "content": "What is in this document?"}]
            filter (dict, optional): Metadata filters to narrow context.
                Example: {"client_email": "user@example.com"}
            model (str, optional): LLM model to use
            temperature (float, optional): Sampling temperature (0.0-1.0)

        Returns:
            dict: Chat response with generated answer and source citations

        Raises:
            Exception: If the chat request fails

        Example:
            >>> assistant = PineconeAssistant()
            >>> messages = [
            ...     {"role": "user", "content": "Summarize the uploaded documents"}
            ... ]
            >>> response = assistant.chat(
            ...     messages=messages,
            ...     filter={"client_email": "user@example.com"}
            ... )
            >>> print(response.message.content)
        """
        try:
            logger.info("Sending chat request with %d message(s)", len(messages))
            if filter:
                logger.debug("Applying filter: %s", filter)

            response = self.assistant.chat(
                messages=messages,
                filter=filter,
                model=model,
                temperature=temperature
            )
            logger.info("Chat response received")
            return response
        except Exception as e:
            logger.error("Failed to process chat request: %s", e)
            raise
