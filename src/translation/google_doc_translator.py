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
            # Load service account credentials directly from config.dev.json
            from src.config import load_config
            from google.oauth2 import service_account

            # Get full config to access service account
            full_config = load_config()
            sa_info = full_config.get('google_drive', {}).get('service_account')

            if not sa_info:
                raise ValueError(
                    "Service account credentials not found in config. "
                    "Please ensure 'google_drive.service_account' exists in config.dev.json"
                )

            # Create credentials directly from config dict (no temp file needed)
            credentials = service_account.Credentials.from_service_account_info(sa_info)
            logger.debug("Using service account credentials from config.dev.json")

            # Create client with credentials
            self.client = translate_v3.TranslationServiceClient(credentials=credentials)
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

            # Save result to temporary file first
            logger.info("Saving translated document")
            temp_output = output_path + '.tmp'
            with open(temp_output, 'wb') as f:
                f.write(translated_content)

            # Sanitize the translated document to ensure UTF-8 compliance
            logger.info("Sanitizing translated document for UTF-8 compliance")
            self._sanitize_translated_docx(temp_output, output_path)

            # Clean up temp file
            if os.path.exists(temp_output):
                os.remove(temp_output)
                logger.debug("Removed temporary file: %s", temp_output)

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

    def _sanitize_translated_docx(self, input_path: str, output_path: str) -> None:
        """
        Sanitize a translated DOCX file to ensure UTF-8 compliance.

        This method extracts the DOCX ZIP, fixes XML encoding at byte level,
        and repackages to ensure FlowiseAI can process it.

        Args:
            input_path: Path to the translated DOCX file (may contain malformed UTF-8)
            output_path: Path to save the sanitized DOCX file

        Raises:
            RuntimeError: If sanitization fails
        """
        logger.debug("Sanitizing DOCX file at byte level: %s -> %s", input_path, output_path)

        try:
            # Always use byte-level repair to fix any UTF-8 issues in the XML
            # This is more thorough than just reading paragraphs
            self._repair_malformed_docx(input_path, output_path)
            return

            # Extract and sanitize all text content
            logger.debug("Extracting and sanitizing document content")
            sanitized_paragraphs = []
            total_chars_removed = 0

            for para in doc.paragraphs:
                original_text = para.text
                original_length = len(original_text)

                # Sanitize the text for XML compatibility
                sanitized_text = sanitize_text_for_xml(original_text)
                sanitized_length = len(sanitized_text)

                if sanitized_length != original_length:
                    chars_removed = original_length - sanitized_length
                    total_chars_removed += chars_removed
                    logger.debug("Paragraph sanitized: removed %d invalid characters", chars_removed)

                sanitized_paragraphs.append(sanitized_text)

            if total_chars_removed > 0:
                logger.warning("Removed %d invalid characters during sanitization", total_chars_removed)
            else:
                logger.debug("No invalid characters found - document is clean")

            # Create new document with sanitized content
            logger.debug("Creating new document with sanitized content")
            new_doc = Document()

            for sanitized_text in sanitized_paragraphs:
                new_doc.add_paragraph(sanitized_text)

            # Save the sanitized document
            logger.debug("Saving sanitized document to: %s", output_path)
            new_doc.save(output_path)

            logger.info("Document sanitization completed successfully")

        except Exception as e:
            logger.error("Error during document sanitization: %s", e, exc_info=True)
            raise RuntimeError(f"Failed to sanitize translated document: {e}")

    def _repair_malformed_docx(self, input_path: str, output_path: str) -> None:
        """
        Attempt to repair a malformed DOCX file by extracting XML and fixing encoding issues.

        Args:
            input_path: Path to the malformed DOCX file
            output_path: Path to save the repaired DOCX file

        Raises:
            RuntimeError: If repair fails
        """
        logger.debug("Attempting to repair malformed DOCX file")

        try:
            import zipfile
            import tempfile
            import shutil
            from xml.etree import ElementTree as ET
            from src.convert_to_docx import sanitize_text_for_xml

            # DOCX files are ZIP archives containing XML files
            # We'll extract, fix encoding, and repackage

            with tempfile.TemporaryDirectory() as temp_dir:
                logger.debug("Extracting DOCX archive to temp directory")

                # Extract the DOCX (ZIP) contents
                with zipfile.ZipFile(input_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Find and fix ALL XML files in the DOCX archive
                xml_files_fixed = 0
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.xml'):
                            xml_path = os.path.join(root, file)
                            logger.debug("Repairing XML file: %s", file)

                            try:
                                # Read the XML file with error handling
                                with open(xml_path, 'rb') as f:
                                    xml_bytes = f.read()

                                # Try to decode with UTF-8, replacing invalid sequences
                                try:
                                    xml_text = xml_bytes.decode('utf-8', errors='replace')
                                except Exception:
                                    # Fallback to latin-1 then encode to UTF-8
                                    xml_text = xml_bytes.decode('latin-1', errors='replace')

                                # Replace any replacement characters with empty string
                                original_text = xml_text
                                xml_text = xml_text.replace('\ufffd', '')

                                # Parse and reconstruct the XML to ensure validity
                                try:
                                    tree = ET.fromstring(xml_text.encode('utf-8'))

                                    # Extract all text nodes and sanitize them
                                    for elem in tree.iter():
                                        if elem.text:
                                            elem.text = sanitize_text_for_xml(elem.text)
                                        if elem.tail:
                                            elem.tail = sanitize_text_for_xml(elem.tail)

                                    # Write back the sanitized XML
                                    xml_text = ET.tostring(tree, encoding='utf-8', method='xml').decode('utf-8')

                                except ET.ParseError as parse_error:
                                    logger.debug("XML parsing failed for %s: %s. Using text sanitization.", file, parse_error)
                                    # If XML parsing fails, just sanitize the text content
                                    xml_text = sanitize_text_for_xml(xml_text)

                                # Only write if changes were made
                                if xml_text != original_text:
                                    with open(xml_path, 'w', encoding='utf-8') as f:
                                        f.write(xml_text)
                                    xml_files_fixed += 1
                                    logger.debug("%s repaired", file)

                            except Exception as xml_error:
                                logger.warning("Failed to repair %s: %s", file, xml_error)
                                # Continue with other files

                logger.info("Repaired %d XML files in DOCX archive", xml_files_fixed)

                # Repackage the DOCX
                logger.debug("Repackaging repaired DOCX file")
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            archive_name = os.path.relpath(file_path, temp_dir)
                            zip_out.write(file_path, archive_name)

                logger.info("DOCX file repaired successfully")

        except Exception as e:
            logger.error("Failed to repair malformed DOCX: %s", e, exc_info=True)
            raise RuntimeError(f"DOCX repair failed: {e}")
