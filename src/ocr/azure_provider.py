"""
Azure OCR Provider

Implements Azure Document Intelligence Read API integration for OCR.
"""

import os
import time
import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path

import pdfplumber
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_BREAK
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

from src.ocr.base_provider import BaseOCRProvider

logger = logging.getLogger('EmailReader.OCR.Azure')


class AzureOCRProvider(BaseOCRProvider):
    """
    Azure Document Intelligence OCR provider.

    Uses Azure's Read API for intelligent document analysis with
    layout preservation and high accuracy OCR.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Azure OCR provider.

        Args:
            config: Configuration dictionary with 'endpoint' and 'api_key'

        Raises:
            ValueError: If required config values are missing
        """
        super().__init__(config)

        self.endpoint = config.get('endpoint')
        self.api_key = config.get('api_key')

        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Azure OCR provider requires 'endpoint' and 'api_key' in configuration"
            )

        logger.info("Initializing Azure Document Intelligence client")
        logger.debug("Azure endpoint: %s", self.endpoint)

        try:
            self.client = DocumentAnalysisClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.api_key)
            )
            logger.info("Azure OCR provider initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Azure client: %s", e)
            raise

    def process_document(self, input_path: str, output_path: str) -> None:
        """
        Process a document with Azure OCR and save the result.

        Detects searchable vs scanned pages and processes accordingly.

        Args:
            input_path: Path to input PDF file
            output_path: Path to save output DOCX file

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If OCR processing fails
        """
        logger.info("Processing document with Azure OCR: %s", os.path.basename(input_path))
        logger.debug("Input: %s", input_path)
        logger.debug("Output: %s", output_path)

        if not os.path.exists(input_path):
            logger.error("Input file not found: %s", input_path)
            raise FileNotFoundError(f"File not found: {input_path}")

        try:
            # Detect which pages need OCR
            logger.info("Analyzing PDF pages for searchability")
            page_searchability = self._detect_page_searchability(input_path)
            total_pages = len(page_searchability)
            searchable_count = sum(1 for is_searchable in page_searchability if is_searchable)
            ocr_count = total_pages - searchable_count

            logger.info("PDF analysis: %d total pages, %d searchable, %d need OCR",
                       total_pages, searchable_count, ocr_count)

            # Extract all pages content
            pages_content: List[str] = []

            with pdfplumber.open(input_path) as pdf:
                for page_num, (page, is_searchable) in enumerate(zip(pdf.pages, page_searchability), 1):
                    logger.debug("Processing page %d/%d (searchable: %s)",
                               page_num, total_pages, is_searchable)

                    if is_searchable:
                        # Extract text directly
                        text = page.extract_text() or ""
                        logger.debug("Page %d: extracted %d characters directly",
                                   page_num, len(text))
                        pages_content.append(text)
                    else:
                        # This page needs OCR - we'll OCR the entire document
                        # Break out and use Azure for all pages
                        logger.info("Found non-searchable page %d - using Azure OCR for entire document",
                                  page_num)
                        break
                else:
                    # All pages are searchable, save directly
                    logger.info("All pages are searchable - saving without OCR")
                    self._save_as_docx(pages_content, output_path)
                    return

            # At least one page needs OCR - use Azure for entire document
            logger.info("Reading PDF file for Azure OCR")
            with open(input_path, 'rb') as f:
                pdf_bytes = f.read()

            file_size_kb = len(pdf_bytes) / 1024
            logger.debug("PDF file size: %.2f KB", file_size_kb)

            # Perform OCR with Azure
            ocr_result = self._ocr_with_azure(pdf_bytes)

            # Save result as DOCX
            self._save_as_docx(ocr_result, output_path)

            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024
                logger.info("Azure OCR completed: %s (%.2f KB)",
                           os.path.basename(output_path), output_size)
            else:
                raise RuntimeError("OCR processing failed to create output file")

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error("Error during Azure OCR processing: %s", e, exc_info=True)
            raise RuntimeError(f"Azure OCR processing failed: {e}")

    def is_pdf_searchable(self, pdf_path: str) -> bool:
        """
        Check if a PDF contains searchable text.

        Uses pdfplumber to check if >50% of pages have >50 characters.

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF has extractable text, False otherwise
        """
        logger.debug("Checking if PDF is searchable: %s", os.path.basename(pdf_path))

        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_with_text = 0
                total_pages = len(pdf.pages)

                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text and len(text.strip()) > 50:
                        pages_with_text += 1
                        logger.debug("Page %d has sufficient text", page_num)

                is_searchable = pages_with_text > (total_pages * 0.5)
                logger.debug("PDF searchable: %s (%d/%d pages with text)",
                           is_searchable, pages_with_text, total_pages)
                return is_searchable

        except Exception as e:
            logger.error("Error checking PDF searchability: %s", e)
            raise

    def _detect_page_searchability(self, pdf_path: str) -> List[bool]:
        """
        Analyze each page individually to determine if it needs OCR.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of booleans indicating if each page is searchable
        """
        logger.debug("Detecting searchability for each page")

        try:
            page_searchability: List[bool] = []

            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    char_count = len(text.strip()) if text else 0
                    is_searchable = char_count > 50

                    logger.debug("Page %d: %d characters, searchable: %s",
                               page_num, char_count, is_searchable)
                    page_searchability.append(is_searchable)

            return page_searchability

        except Exception as e:
            logger.error("Error detecting page searchability: %s", e)
            raise

    def _ocr_with_azure(self, pdf_bytes: bytes, max_retries: int = 3) -> List[str]:
        """
        Call Azure Read API to perform OCR.

        Args:
            pdf_bytes: PDF file content as bytes
            max_retries: Maximum number of retry attempts

        Returns:
            List of text content for each page

        Raises:
            RuntimeError: If OCR fails after retries
        """
        logger.info("Starting Azure Document Intelligence Read API call")
        logger.debug("Document size: %d bytes", len(pdf_bytes))

        for attempt in range(1, max_retries + 1):
            try:
                logger.debug("Azure API attempt %d/%d", attempt, max_retries)

                start_time = time.time()

                # Begin analyzing document
                logger.debug("Calling begin_analyze_document with prebuilt-read model")
                poller = self.client.begin_analyze_document(
                    "prebuilt-read",
                    document=pdf_bytes
                )

                logger.info("Azure analysis started, waiting for completion...")

                # Wait for completion
                result = poller.result()

                duration = time.time() - start_time
                logger.info("Azure analysis completed in %.2f seconds", duration)
                logger.debug("Result contains %d pages", len(result.pages))

                # Extract text from each page
                pages_content: List[str] = []

                for page_num, page in enumerate(result.pages, 1):
                    logger.debug("Extracting text from page %d/%d",
                               page_num, len(result.pages))

                    # Get all lines on this page
                    page_lines = [
                        line.content
                        for line in result.pages[page_num - 1].lines
                    ]

                    page_text = "\n".join(page_lines)
                    char_count = len(page_text)

                    logger.debug("Page %d: extracted %d characters",
                               page_num, char_count)

                    pages_content.append(page_text)

                total_chars = sum(len(p) for p in pages_content)
                logger.info("Azure OCR extracted %d characters from %d pages",
                           total_chars, len(pages_content))

                return pages_content

            except HttpResponseError as e:
                logger.error("Azure API HTTP error (attempt %d/%d): %s",
                           attempt, max_retries, e)

                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info("Retrying in %d seconds...", wait_time)
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries reached, giving up")
                    raise RuntimeError(f"Azure OCR failed after {max_retries} attempts: {e}")

            except Exception as e:
                logger.error("Unexpected error during Azure OCR: %s", e, exc_info=True)
                raise RuntimeError(f"Azure OCR failed: {e}")

        raise RuntimeError("Azure OCR failed: max retries exceeded")

    def _save_as_docx(self, pages_content: List[str], output_path: str) -> None:
        """
        Save extracted text as a DOCX file with page breaks.

        Args:
            pages_content: List of text content for each page
            output_path: Path to save DOCX file
        """
        logger.debug("Saving %d pages to DOCX: %s",
                    len(pages_content), os.path.basename(output_path))

        try:
            document = Document()

            for page_num, page_text in enumerate(pages_content, 1):
                logger.debug("Adding page %d to document (%d characters)",
                           page_num, len(page_text))

                # Add page content
                if page_text.strip():
                    paragraph = document.add_paragraph(page_text)
                    # Set font size
                    for run in paragraph.runs:
                        run.font.size = Pt(11)
                else:
                    logger.debug("Page %d is empty", page_num)
                    document.add_paragraph("")

                # Add page break (except after last page)
                if page_num < len(pages_content):
                    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
                    logger.debug("Added page break after page %d", page_num)

            logger.debug("Saving DOCX file to: %s", output_path)
            document.save(output_path)

            logger.info("DOCX file saved successfully: %s", os.path.basename(output_path))

        except Exception as e:
            logger.error("Error saving DOCX: %s", e, exc_info=True)
            raise
