"""
Google Document Translator

Uses Google Cloud Translation API v3 for document translation with format preservation.
"""

import os
import time
import logging
from typing import Dict, Any

from google.cloud import translate_v3
from google.api_core.exceptions import GoogleAPIError

from src.translation.base_translator import BaseTranslator

logger = logging.getLogger('EmailReader.Translation.GoogleDoc')


class GoogleDocTranslator(BaseTranslator):
    """
    Google Cloud Translation API v3 Document Translator.

    Uses the advanced document translation endpoint that preserves
    formatting and layout in translated documents.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Google Document translator.

        Args:
            config: Configuration dictionary with 'project_id' and optional 'location'

        Raises:
            ValueError: If required config values are missing
        """
        super().__init__(config)

        self.project_id = config.get('project_id')
        self.location = config.get('location', 'us-central1')

        if not self.project_id:
            raise ValueError(
                "Google Document Translation requires 'project_id' in configuration"
            )

        logger.info("Initializing Google Cloud Translation API v3 client")
        logger.debug("Project ID: %s", self.project_id)
        logger.debug("Location: %s", self.location)

        try:
            # Get service account credentials from config
            from src.config import get_service_account_path

            # This will extract service account from config and create temp file
            credentials_path = get_service_account_path()
            logger.debug("Using service account credentials: %s", credentials_path)

            # Set environment variable for Google Cloud client
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

            self.client = translate_v3.TranslationServiceClient()
            self.parent = f"projects/{self.project_id}/locations/{self.location}"
            logger.info("Google Document Translator initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Google Translation client: %s", e)
            raise

    def translate_document(
        self,
        input_path: str,
        output_path: str,
        target_lang: str = 'en'
    ) -> None:
        """
        Translate a DOCX document using Google Cloud Translation API v3.

        Args:
            input_path: Path to input DOCX document
            output_path: Path to save translated DOCX document
            target_lang: Target language code (default: 'en')

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If translation fails
        """
        logger.info("Translating document with Google Translation API v3: %s -> %s",
                   os.path.basename(input_path), target_lang)
        logger.debug("Input: %s", input_path)
        logger.debug("Output: %s", output_path)
        logger.debug("Target language: %s", target_lang)

        if not os.path.exists(input_path):
            logger.error("Input file not found: %s", input_path)
            raise FileNotFoundError(f"File not found: {input_path}")

        # Validate file type
        if not input_path.lower().endswith('.docx'):
            logger.error("Input file must be DOCX format: %s", input_path)
            raise ValueError("Only DOCX files are supported for document translation")

        try:
            # Read document
            logger.info("Reading input document")
            with open(input_path, 'rb') as f:
                document_content = f.read()

            file_size_kb = len(document_content) / 1024
            logger.debug("Document size: %.2f KB", file_size_kb)

            # Translate
            translated_content = self._call_translation_api(document_content, target_lang)

            # Save result
            logger.info("Saving translated document")
            with open(output_path, 'wb') as f:
                f.write(translated_content)

            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024
                logger.info("Translation completed successfully: %s (%.2f KB)",
                           os.path.basename(output_path), output_size)
            else:
                raise RuntimeError("Translation failed to create output file")

        except FileNotFoundError:
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error("Error during Google document translation: %s", e, exc_info=True)
            raise RuntimeError(f"Google document translation failed: {e}")

    def _call_translation_api(
        self,
        content: bytes,
        target_lang: str,
        source_lang: str = None
    ) -> bytes:
        """
        Call Google Cloud Translation API for document translation.

        Args:
            content: Document content as bytes
            target_lang: Target language code
            source_lang: Optional source language code (auto-detect if None)

        Returns:
            Translated document content as bytes

        Raises:
            RuntimeError: If API call fails
        """
        logger.info("Calling Google Translation API v3")
        logger.debug("Parent: %s", self.parent)
        logger.debug("Target language: %s", target_lang)
        logger.debug("Source language: %s", source_lang or "auto-detect")
        logger.debug("Document size: %d bytes", len(content))

        try:
            start_time = time.time()

            # Prepare document input
            document_input_config = translate_v3.DocumentInputConfig(
                content=content,
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

            # Prepare request
            request = translate_v3.TranslateDocumentRequest(
                parent=self.parent,
                target_language_code=target_lang,
                document_input_config=document_input_config
            )

            if source_lang:
                request.source_language_code = source_lang

            logger.info("Sending translation request to Google API")

            # Call API
            response = self.client.translate_document(request=request)

            duration = time.time() - start_time
            logger.info("Translation completed in %.2f seconds", duration)

            # Extract translated document
            translated_content = response.document_translation.byte_stream_outputs[0]

            logger.debug("Received translated document: %d bytes", len(translated_content))

            # Log detected source language if auto-detected
            if not source_lang and hasattr(response, 'document_translation'):
                detected_lang = getattr(
                    response.document_translation,
                    'detected_language_code',
                    'unknown'
                )
                logger.info("Detected source language: %s", detected_lang)

            return translated_content

        except GoogleAPIError as e:
            logger.error("Google Translation API error: %s", e)
            logger.error("Error details: status=%s, message=%s",
                        e.grpc_status_code if hasattr(e, 'grpc_status_code') else 'unknown',
                        e.message if hasattr(e, 'message') else str(e))
            raise RuntimeError(f"Google Translation API failed: {e}")

        except Exception as e:
            logger.error("Unexpected error calling Translation API: %s", e, exc_info=True)
            raise RuntimeError(f"Translation API call failed: {e}")
