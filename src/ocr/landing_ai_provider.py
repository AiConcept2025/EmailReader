"""LandingAI OCR provider using ADE Parse API."""

import os
import time
import logging
from typing import Dict, List, Any, Optional
import requests
from pathlib import Path

from .base_provider import BaseOCRProvider
from src.pdf_image_ocr import is_pdf_searchable_pypdf
from src.convert_to_docx import convert_txt_to_docx


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module name.

    Args:
        name: Logger name (e.g., 'EmailReader.OCR.LandingAI')

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


logger = get_logger('EmailReader.OCR.LandingAI')


class LandingAIOCRProvider(BaseOCRProvider):
    """LandingAI OCR provider using ADE Parse API with layout preservation."""

    def __init__(self, config: dict):
        """
        Initialize LandingAI OCR provider.

        Args:
            config: LandingAI configuration with:
                - api_key: LandingAI API key
                - base_url: API base URL (default: https://api.va.landing.ai/v1)
                - model: Model name (default: dpt-2-latest)
                - split_mode: Split mode (default: page)
                - preserve_layout: Enable layout preservation (default: True)
                - chunk_processing: Grounding configuration
                - retry: Retry configuration
        """
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.va.landing.ai/v1')
        self.model = config.get('model', 'dpt-2-latest')
        self.split_mode = config.get('split_mode', 'page')
        self.preserve_layout = config.get('preserve_layout', True)

        # Chunk processing config
        chunk_config = config.get('chunk_processing', {})
        self.use_grounding = chunk_config.get('use_grounding', True)
        self.maintain_positions = chunk_config.get('maintain_positions', True)

        # Retry config
        retry_config = config.get('retry', {})
        self.max_attempts = retry_config.get('max_attempts', 3)
        self.backoff_factor = retry_config.get('backoff_factor', 2)
        self.timeout = retry_config.get('timeout', 30)

        if not self.api_key:
            logger.error("LandingAI API key is required")
            raise ValueError("LandingAI API key is required")

        logger.info(
            f"Initialized LandingAIOCRProvider "
            f"(model: {self.model}, layout: {self.preserve_layout}, "
            f"grounding: {self.use_grounding})"
        )
        logger.debug(
            f"Configuration: base_url={self.base_url}, split_mode={self.split_mode}, "
            f"timeout={self.timeout}s, max_attempts={self.max_attempts}"
        )

    def process_document(self, ocr_file: str, out_doc_file_path: str) -> None:
        """
        Process document using LandingAI OCR with layout preservation.

        Args:
            ocr_file: Path to input file (PDF or image)
            out_doc_file_path: Path where DOCX output should be saved

        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If file format is invalid
            RuntimeError: If OCR processing fails
        """
        if not os.path.exists(ocr_file):
            logger.error(f"Input file not found: {ocr_file}")
            raise FileNotFoundError(f"Input file not found: {ocr_file}")

        logger.info(f"Processing document with LandingAI OCR: {ocr_file}")
        logger.debug(f"Output path: {out_doc_file_path}")

        # Track current file for JSON debug output
        self._current_processing_file = ocr_file

        start_time = time.time()

        try:
            # Call LandingAI API
            logger.debug("Calling LandingAI API")
            api_response = self._call_api_with_retry(ocr_file)

            # Check if we have grounding data for structured conversion
            chunks = api_response.get('chunks', [])
            has_grounding_data = chunks and any(c.get('grounding') for c in chunks)

            if has_grounding_data and self.use_grounding:
                # Use structured conversion with full formatting preservation
                logger.info("Grounding data available - using structured DOCX conversion")
                self._save_as_docx_structured(api_response, out_doc_file_path)
            else:
                # Fallback to basic text extraction
                if not has_grounding_data:
                    logger.warning("No grounding data in API response - falling back to basic conversion")
                else:
                    logger.info("Grounding disabled in config - using basic conversion")

                # Extract text using layout preservation
                logger.debug("Extracting text with layout preservation")
                extracted_text = self._extract_with_positions(api_response)

                if not extracted_text or extracted_text.strip() == "":
                    logger.warning("No text extracted from document")
                    extracted_text = "[No text content extracted from document]"

                # Convert to DOCX format
                logger.debug("Converting to DOCX format (basic method)")
                self._save_as_docx(extracted_text, out_doc_file_path)

            elapsed = time.time() - start_time
            logger.info(
                f"LandingAI OCR completed in {elapsed:.2f}s: {out_doc_file_path}"
            )

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"LandingAI OCR failed for {ocr_file} after {elapsed:.2f}s: {e}",
                exc_info=True
            )
            raise RuntimeError(f"LandingAI OCR processing failed: {e}") from e

    def _call_api_with_retry(self, file_path: str) -> Dict[str, Any]:
        """
        Call LandingAI API with retry logic.

        Args:
            file_path: Path to document file

        Returns:
            API response dictionary

        Raises:
            RuntimeError: If all retry attempts fail
        """
        url = self.base_url  # Full URL including endpoint path from config
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        logger.debug(f"API endpoint: {url}")

        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.debug(f"LandingAI API call attempt {attempt}/{self.max_attempts}")

                with open(file_path, 'rb') as f:
                    files = {'document': f}
                    data = {
                        'model': self.model,
                        'split_mode': self.split_mode,
                        'preserve_layout': str(self.preserve_layout).lower()
                    }

                    logger.debug(f"Request data: {data}")

                    response = requests.post(
                        url,
                        headers=headers,
                        files=files,
                        data=data,
                        timeout=self.timeout
                    )

                if response.status_code == 200:
                    logger.info(f"LandingAI API call successful (attempt {attempt})")
                    response_data = response.json()

                    # Log response summary
                    chunks = response_data.get('chunks', [])
                    logger.info(f"Received {len(chunks)} chunks from API")

                    # Enhanced logging: Show sample chunk structure with formatting data
                    if chunks and len(chunks) > 0:
                        import json
                        sample_chunk = chunks[0]
                        logger.debug(f"Sample chunk structure (first chunk):\n{json.dumps(sample_chunk, indent=2)}")

                        # Log grounding data availability
                        grounding = sample_chunk.get('grounding', {})
                        if grounding:
                            page = grounding.get('page')
                            box = grounding.get('box', {})
                            logger.info(
                                f"Formatting data available - "
                                f"Page: {page}, "
                                f"Bounding box: left={box.get('left')}, top={box.get('top')}, "
                                f"right={box.get('right')}, bottom={box.get('bottom')}"
                            )

                            # Count how many chunks have grounding data
                            chunks_with_grounding = sum(1 for c in chunks if c.get('grounding'))
                            logger.info(
                                f"Grounding data present: {chunks_with_grounding}/{len(chunks)} chunks "
                                f"({100*chunks_with_grounding/len(chunks):.1f}%)"
                            )
                        else:
                            logger.warning("No grounding data in chunks - formatting will be limited")
                    else:
                        logger.warning("No chunks received from API")

                    # Save JSON response for analysis
                    import json
                    from pathlib import Path
                    import os
                    import datetime

                    # Create a debug filename based on input file with timestamp
                    # This ensures each processing creates a NEW JSON file (not overwriting)
                    if hasattr(self, '_current_processing_file'):
                        input_filename = Path(self._current_processing_file).stem

                        # Use project root directory for consistent path
                        # completed_temp should be at project root (where index.py/app.py are located)
                        project_root = os.getcwd()
                        completed_temp_dir = os.path.join(project_root, 'completed_temp')

                        # Create directory if it doesn't exist
                        os.makedirs(completed_temp_dir, exist_ok=True)

                        # Add timestamp to filename to prevent overwriting (each run creates unique file)
                        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        json_output_path = os.path.join(completed_temp_dir, f"{input_filename}_landing_ai_{timestamp}.json")

                        try:
                            with open(json_output_path, 'w', encoding='utf-8') as f:
                                json.dump(response_data, f, indent=2, ensure_ascii=False)
                            logger.info(f"Saved LandingAI JSON response to: {json_output_path}")

                            # Upload JSON to Google Drive if configured
                            try:
                                from src.google_drive import GoogleApi
                                from src.config import load_config

                                # Get configuration
                                config = load_config()

                                # Initialize Google Drive API
                                drive_api = GoogleApi()

                                # Get the parent folder ID from config
                                # This is the root folder for the client
                                parent_folder_id = config.get('google_drive', {}).get('parent_folder_id', '')

                                if parent_folder_id:
                                    # List subfolders to find "Completed" folder
                                    subfolders = drive_api.get_subfolders_list_in_folder(parent_folder_id)
                                    completed_folder = next(
                                        (f for f in subfolders if f.get('name') == 'Completed'),
                                        None
                                    )

                                    if completed_folder:
                                        completed_folder_id = completed_folder['id']
                                        json_filename = os.path.basename(json_output_path)

                                        # Upload JSON file to Google Drive Completed folder
                                        file_info = drive_api.upload_file_to_google_drive(
                                            file_path=json_output_path,
                                            file_name=json_filename,
                                            parent_folder_id=completed_folder_id,
                                            description="LandingAI API response for analysis"
                                        )

                                        if file_info and file_info.get('id'):
                                            logger.info(
                                                f"Uploaded JSON to Google Drive Completed folder: "
                                                f"{json_filename} (ID: {file_info.get('id')})"
                                            )
                                        else:
                                            logger.warning(f"Failed to upload JSON to Google Drive: No file ID returned")
                                    else:
                                        logger.warning("Completed folder not found in Google Drive - JSON saved locally only")
                                else:
                                    logger.debug("No parent_folder_id configured - JSON saved locally only")

                            except Exception as drive_error:
                                # Don't fail the OCR if Google Drive upload fails
                                logger.warning(f"Could not upload JSON to Google Drive: {drive_error}")
                                logger.info(f"JSON file still available locally at: {json_output_path}")

                        except Exception as e:
                            logger.warning(f"Failed to save JSON response: {e}")

                    return response_data

                else:
                    logger.warning(
                        f"LandingAI API error (attempt {attempt}): "
                        f"Status {response.status_code}, Response: {response.text[:500]}"
                    )

                    # Don't retry on client errors (4xx)
                    if 400 <= response.status_code < 500:
                        error_msg = (
                            f"LandingAI API client error: {response.status_code} - "
                            f"{response.text}"
                        )
                        logger.error(error_msg)
                        raise RuntimeError(error_msg)

            except requests.exceptions.Timeout as e:
                logger.warning(
                    f"LandingAI API timeout (attempt {attempt}): "
                    f"Request exceeded {self.timeout}s timeout"
                )

            except requests.exceptions.ConnectionError as e:
                logger.warning(
                    f"LandingAI API connection error (attempt {attempt}): {e}"
                )

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"LandingAI API request failed (attempt {attempt}): {e}"
                )

            except Exception as e:
                logger.error(
                    f"Unexpected error during API call (attempt {attempt}): {e}",
                    exc_info=True
                )
                raise

            # Exponential backoff before retry
            if attempt < self.max_attempts:
                wait_time = self.backoff_factor ** (attempt - 1)
                logger.debug(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)

        error_msg = f"LandingAI API failed after {self.max_attempts} attempts"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    def _extract_with_positions(self, api_response: Dict[str, Any]) -> str:
        """
        Extract text from API response using grounding data for layout preservation.

        Args:
            api_response: LandingAI API response

        Returns:
            Extracted text with preserved layout
        """
        chunks = api_response.get('chunks', [])

        if not chunks:
            logger.warning("No chunks in API response")
            return ""

        logger.info(
            f"Processing {len(chunks)} chunks "
            f"(grounding: {self.use_grounding}, positions: {self.maintain_positions})"
        )

        if self.use_grounding and self.maintain_positions:
            # Use layout reconstructor for spatial positioning
            try:
                from src.utils.layout_reconstructor import reconstruct_layout
                logger.debug("Using layout reconstructor for spatial positioning")
                result = reconstruct_layout(chunks)
                logger.info(f"Layout reconstruction produced {len(result)} characters")
                return result

            except ImportError as e:
                logger.warning(
                    f"Failed to import layout_reconstructor: {e}. "
                    f"Falling back to simple concatenation"
                )
                # Fall through to simple concatenation

            except Exception as e:
                logger.error(
                    f"Error during layout reconstruction: {e}. "
                    f"Falling back to simple concatenation",
                    exc_info=True
                )
                # Fall through to simple concatenation

        # Simple concatenation without layout preservation
        logger.debug("Using simple concatenation (no layout preservation)")
        result = '\n'.join(chunk.get('text', '') for chunk in chunks)
        logger.info(f"Simple concatenation produced {len(result)} characters")
        return result

    def _save_as_docx(self, text: str, output_path: str) -> None:
        """
        Save extracted text as DOCX file.

        Args:
            text: Extracted text content
            output_path: Path to save DOCX file
        """
        logger.debug(f"Saving text to DOCX: {output_path}")
        logger.debug(f"Text length: {len(text)} characters")

        # Create temp text file
        temp_txt = output_path.replace('.docx', '.tmp.txt')
        logger.debug(f"Using temporary file: {temp_txt}")

        try:
            # Write text to temp file
            with open(temp_txt, 'w', encoding='utf-8') as f:
                f.write(text)

            logger.debug(f"Temporary text file created: {temp_txt}")

            # Convert to DOCX using existing function
            convert_txt_to_docx(text, output_path)

            # Verify output file
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024  # KB
                logger.info(f"DOCX file saved: {output_path} ({output_size:.2f} KB)")
            else:
                logger.error(f"DOCX file was not created: {output_path}")
                raise RuntimeError(f"Failed to create DOCX file: {output_path}")

        except Exception as e:
            logger.error(f"Error saving DOCX file: {e}", exc_info=True)
            raise

        finally:
            # Clean up temp file
            if os.path.exists(temp_txt):
                try:
                    os.remove(temp_txt)
                    logger.debug(f"Temporary file cleaned up: {temp_txt}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file {temp_txt}: {e}")

    def _save_as_docx_structured(self, api_response: Dict[str, Any], output_path: str) -> None:
        """
        Save API response as DOCX with full formatting preservation.

        Uses FormattedDocument model and structured conversion to preserve:
        - Page breaks
        - Column layout
        - Paragraph spacing
        - Font sizes

        Args:
            api_response: LandingAI API response with chunks and grounding data
            output_path: Path to save DOCX file
        """
        from src.models.formatted_document import FormattedDocument
        from src.convert_to_docx import convert_structured_to_docx

        logger.debug(f"Saving structured document to DOCX: {output_path}")

        try:
            # Create FormattedDocument from API response
            logger.debug("Creating FormattedDocument from API response")
            formatted_doc = FormattedDocument.from_landing_ai_response(api_response)

            logger.info(
                f"Structured document created: {formatted_doc.total_pages} pages, "
                f"{formatted_doc.total_paragraphs} paragraphs"
            )

            # Log page and column details
            for page in formatted_doc.pages:
                logger.debug(
                    f"Page {page.page_number + 1}: {len(page.paragraphs)} paragraphs, "
                    f"{page.columns} columns"
                )

            # Convert to DOCX with full formatting
            logger.debug("Converting FormattedDocument to DOCX")
            convert_structured_to_docx(formatted_doc, output_path)

            # Verify output
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024  # KB
                logger.info(
                    f"Structured DOCX file saved: {output_path} ({output_size:.2f} KB) - "
                    f"Formatting preserved: page breaks, columns, spacing, font sizes"
                )
            else:
                logger.error(f"Structured DOCX file was not created: {output_path}")
                raise RuntimeError(f"Failed to create structured DOCX file: {output_path}")

        except Exception as e:
            logger.error(f"Error saving structured DOCX file: {e}", exc_info=True)
            logger.warning("Falling back to basic text conversion")

            # Fallback to basic conversion
            try:
                extracted_text = self._extract_with_positions(api_response)
                self._save_as_docx(extracted_text, output_path)
                logger.info("Fallback conversion completed successfully")
            except Exception as fallback_error:
                logger.error(f"Fallback conversion also failed: {fallback_error}", exc_info=True)
                raise RuntimeError(f"Both structured and fallback conversion failed") from e

    def is_pdf_searchable(self, pdf_path: str) -> bool:
        """
        Check if PDF is searchable (delegates to existing implementation).

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF contains extractable text, False if image-based

        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If file is not a valid PDF
            RuntimeError: If PDF cannot be read
        """
        logger.debug(f"Checking PDF searchability: {pdf_path}")

        try:
            result = is_pdf_searchable_pypdf(pdf_path)
            logger.debug(f"PDF searchable check result for {pdf_path}: {result}")
            return result

        except Exception as e:
            logger.error(
                f"Error checking PDF searchability for {pdf_path}: {e}",
                exc_info=True
            )
            raise
