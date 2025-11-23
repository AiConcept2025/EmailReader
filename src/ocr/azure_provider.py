"""
Azure OCR Provider

Implements Azure Document Intelligence Read API integration for OCR.
"""

import os
import time
import logging
from typing import Any
from pathlib import Path

import pdfplumber
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_BREAK, WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

from src.ocr.base_provider import BaseOCRProvider
from src.models.paragraph_data import ParagraphData
from src.processors.paragraph_processor import ParagraphProcessor

logger = logging.getLogger('EmailReader.OCR.Azure')


class AzureOCRProvider(BaseOCRProvider):
    """
    Azure Document Intelligence OCR provider.

    Uses Azure's Read API for intelligent document analysis with
    layout preservation and high accuracy OCR.
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize the Azure OCR provider.

        Args:
            config: Configuration dictionary with 'endpoint', 'api_key', and optional 'model'

        Raises:
            ValueError: If required config values are missing
        """
        super().__init__(config)

        self.endpoint = config.get('endpoint')
        self.api_key = config.get('api_key')
        # Get model from config, default to 'prebuilt-layout'
        self.model = config.get('model', 'prebuilt-layout')

        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Azure OCR provider requires 'endpoint' and 'api_key' in configuration"
            )

        logger.info("Initializing Azure Document Intelligence client")
        logger.debug("Azure endpoint: %s", self.endpoint)
        logger.info("Azure OCR model: %s", self.model)

        try:
            self.client = DocumentAnalysisClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.api_key)
            )
            logger.info("Azure OCR provider initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Azure client: %s", e)
            raise

        # Initialize paragraph processor
        self.paragraph_processor = ParagraphProcessor()

        # Get processor config from main config
        processor_config = config.get('paragraph_processor', {})
        self.processor_config = {
            'min_content_length': processor_config.get('min_content_length', 10),
            'max_consecutive_empty': processor_config.get('max_consecutive_empty', 1),
            'normalize_whitespace': processor_config.get('normalize_whitespace', True)
        }
        logger.info("Paragraph processor initialized with config: %s", self.processor_config)

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
            # Detect and correct rotation if enabled
            preprocessing_config = self.config.get('preprocessing', {})
            rotation_config = preprocessing_config.get('rotation_detection', {})
            rotated_path = None

            if rotation_config.get('enabled', False):
                logger.info("Rotation detection enabled, checking document orientation")
                from src.preprocessing.rotation_detector import RotationDetector

                detector = RotationDetector(rotation_config)
                angle, confidence = detector.detect_rotation(input_path)

                if angle != 0:
                    logger.info("Document rotation detected: %d° (confidence: %.2f)", angle, confidence)
                    # Create temporary rotated file
                    import tempfile
                    rotated_path = tempfile.mktemp(suffix='.pdf')
                    detector.correct_rotation(input_path, rotated_path, angle)
                    logger.info("Document rotated, using corrected version for OCR")
                    input_path = rotated_path  # Use rotated file for OCR
                else:
                    logger.info("No rotation detected, proceeding with original document")

            # Use Azure OCR for all documents to get proper paragraph detection
            logger.info("Reading PDF file for Azure OCR")
            with open(input_path, 'rb') as f:
                pdf_bytes = f.read()

            file_size_kb = len(pdf_bytes) / 1024
            logger.debug("PDF file size: %.2f KB", file_size_kb)

            # Perform OCR with Azure
            ocr_result = self._ocr_with_azure(pdf_bytes)

            # Process paragraphs to filter empty/invalid content
            logger.info("Processing paragraphs to remove empty content and layout artifacts")
            clean_paragraphs, verification_pages = self.paragraph_processor.process_ocr_result(
                ocr_result,
                self.processor_config
            )

            # Save verification document (complete OCR output for QA)
            verification_path = output_path.replace('.docx', '_ocr_verification.docx')
            self._save_verification_docx(verification_pages, verification_path)
            logger.info("Verification document saved: %s", os.path.basename(verification_path))

            # Save clean document for translation
            self._save_clean_docx(clean_paragraphs, output_path)
            logger.info("Clean document saved: %s", os.path.basename(output_path))

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
        finally:
            # Clean up temporary rotated file if it was created
            if rotated_path and os.path.exists(rotated_path):
                try:
                    os.remove(rotated_path)
                    logger.debug("Cleaned up temporary rotated file: %s", rotated_path)
                except Exception as e:
                    logger.warning("Failed to clean up temporary file %s: %s", rotated_path, e)

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

    def _detect_page_searchability(self, pdf_path: str) -> list[bool]:
        """
        Analyze each page individually to determine if it needs OCR.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of booleans indicating if each page is searchable
        """
        logger.debug("Detecting searchability for each page")

        try:
            page_searchability: list[bool] = []

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

    def _get_page_width_from_result(self, result) -> float:
        """
        Get page width from Azure OCR result.

        Args:
            result: Azure Document Intelligence result

        Returns:
            Page width in inches (defaults to 8.5 for US Letter)
        """
        try:
            if hasattr(result, 'pages') and result.pages:
                first_page = result.pages[0]
                if hasattr(first_page, 'width'):
                    # Azure returns width in inches directly
                    return first_page.width
        except Exception as e:
            logger.debug("Could not detect page width: %s", e)

        # Default to US Letter width
        return 8.5

    def _ocr_with_azure(self, pdf_bytes: bytes, max_retries: int = 3) -> list[list[ParagraphData]]:
        """
        Call Azure Read API to perform OCR.

        Args:
            pdf_bytes: PDF file content as bytes
            max_retries: Maximum number of retry attempts

        Returns:
            List of paragraph data lists for each page (List[List[ParagraphData]])

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
                logger.debug("Calling begin_analyze_document with %s model", self.model)
                poller = self.client.begin_analyze_document(
                    self.model,
                    document=pdf_bytes
                )

                logger.info("Azure analysis started, waiting for completion...")

                # Wait for completion
                result = poller.result()

                # Detect page width for alignment detection
                self._current_page_width = self._get_page_width_from_result(result)
                logger.debug("Detected page width: %.2f inches", self._current_page_width)

                duration = time.time() - start_time
                logger.info("Azure analysis completed in %.2f seconds", duration)
                logger.debug("Result contains %d pages", len(result.pages))

                # Extract text from each page using paragraphs (preserves logical structure)
                pages_content: list[list[ParagraphData]] = []

                # Global paragraph index for tracking across pages
                global_para_index = 0

                # Check if paragraphs are available
                if hasattr(result, 'paragraphs') and result.paragraphs:
                    logger.debug("Using paragraph-based extraction (%d paragraphs found)",
                               len(result.paragraphs))

                    # Group paragraphs by page number
                    for page_num in range(1, len(result.pages) + 1):
                        logger.debug("Extracting paragraphs from page %d/%d",
                                   page_num, len(result.pages))

                        # Get paragraphs that belong to this page with metadata
                        page_paragraphs: list[ParagraphData] = []

                        for para in result.paragraphs:
                            if (hasattr(para, 'bounding_regions') and
                                para.bounding_regions and
                                para.bounding_regions[0].page_number == page_num):

                                # Extract bounding box if available
                                bounding_box = None
                                if para.bounding_regions and hasattr(para.bounding_regions[0], 'polygon'):
                                    polygon = para.bounding_regions[0].polygon
                                    # Convert polygon to simple bounding box (min/max coordinates)
                                    if polygon:
                                        x_coords = [p.x for p in polygon]
                                        y_coords = [p.y for p in polygon]
                                        bounding_box = {
                                            'x': min(x_coords),
                                            'y': min(y_coords),
                                            'width': max(x_coords) - min(x_coords),
                                            'height': max(y_coords) - min(y_coords)
                                        }

                                # Extract confidence if available
                                confidence = getattr(para, 'confidence', None)

                                # Extract paragraph role if available (title, sectionHeading, etc.)
                                role = getattr(para, 'role', None)

                                # Create ParagraphData object
                                para_data = ParagraphData(
                                    text=para.content,
                                    page=page_num,
                                    bounding_box=bounding_box,
                                    confidence=confidence,
                                    paragraph_index=global_para_index,
                                    role=role
                                )
                                page_paragraphs.append(para_data)
                                global_para_index += 1

                        total_chars = sum(len(p.text) for p in page_paragraphs)
                        logger.debug("Page %d: extracted %d characters from %d paragraphs",
                                   page_num, total_chars, len(page_paragraphs))

                        pages_content.append(page_paragraphs)
                else:
                    # Fallback to line-based extraction if paragraphs not available
                    logger.warning("Paragraphs not available, falling back to line-based extraction")

                    for page_num, page in enumerate(result.pages, 1):
                        logger.debug("Extracting text from page %d/%d",
                                   page_num, len(result.pages))

                        # Get all lines on this page as ParagraphData
                        page_paragraphs: list[ParagraphData] = []
                        for line in result.pages[page_num - 1].lines:
                            para_data = ParagraphData(
                                text=line.content,
                                page=page_num,
                                bounding_box=None,
                                confidence=None,
                                paragraph_index=global_para_index
                            )
                            page_paragraphs.append(para_data)
                            global_para_index += 1

                        char_count = sum(len(p.text) for p in page_paragraphs)
                        logger.debug("Page %d: extracted %d characters from %d lines",
                                   page_num, char_count, len(page_paragraphs))

                        pages_content.append(page_paragraphs)

                total_paras = sum(len(page) for page in pages_content)
                total_chars = sum(len(p.text) for page in pages_content for p in page)

                # CRITICAL: Log total paragraph count after extraction
                logger.info("PARAGRAPH_COUNT_VERIFICATION: stage=OCR_EXTRACTION, count=%d", total_paras)
                logger.info("Azure OCR extracted %d paragraphs (%d characters) from %d pages",
                           total_paras, total_chars, len(pages_content))

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

    def _detect_alignment_from_bounding_box(
        self,
        bounding_box: dict[str, float] | None,
        page_width: float = 8.5,  # Standard US Letter width in inches
        role: str | None = None
    ) -> int | None:
        """
        Detect text alignment based on bounding box position.

        Uses the X-coordinate of the bounding box to determine if text is
        left-aligned, centered, or right-aligned on the page.

        Args:
            bounding_box: Dictionary with x, y, width, height in inches
            page_width: Page width in inches (default: 8.5 for US Letter)
            role: Optional paragraph role from Azure

        Returns:
            WD_PARAGRAPH_ALIGNMENT constant or None for default
        """
        # If no bounding box, use role-based defaults
        if not bounding_box or 'x' not in bounding_box or 'width' not in bounding_box:
            if role == 'title' or role == 'pageNumber':
                return WD_PARAGRAPH_ALIGNMENT.CENTER
            return None  # Default left

        # Extract position data
        x_start = bounding_box['x']
        text_width = bounding_box['width']
        x_center = x_start + (text_width / 2)

        # Define page regions (with margins)
        left_margin = 1.0    # 1 inch left margin
        right_margin = page_width - 1.0  # 1 inch right margin
        page_center = page_width / 2

        # Calculate tolerance zones (15% of usable width)
        usable_width = right_margin - left_margin
        center_tolerance = usable_width * 0.15  # 15% tolerance for center detection

        # Detect alignment based on text center position
        if abs(x_center - page_center) < center_tolerance:
            # Text is centered
            logger.debug(
                "Detected CENTER alignment: x_center=%.2f, page_center=%.2f, diff=%.2f",
                x_center, page_center, abs(x_center - page_center)
            )
            return WD_PARAGRAPH_ALIGNMENT.CENTER
        elif x_start < left_margin + 0.5:
            # Text starts near left margin
            logger.debug("Detected LEFT alignment: x_start=%.2f", x_start)
            return WD_PARAGRAPH_ALIGNMENT.LEFT
        elif x_start + text_width > right_margin - 0.5:
            # Text extends to right margin
            logger.debug("Detected RIGHT alignment: x_end=%.2f", x_start + text_width)
            return WD_PARAGRAPH_ALIGNMENT.RIGHT
        else:
            # Default to left
            return WD_PARAGRAPH_ALIGNMENT.LEFT

    def _set_paragraph_spacing(self, paragraph, before_pt: int = 6, after_pt: int = 6):
        """
        Set paragraph spacing in points.

        Args:
            paragraph: Document paragraph object
            before_pt: Spacing before paragraph in points
            after_pt: Spacing after paragraph in points
        """
        pPr = paragraph._element.get_or_add_pPr()
        spacing = OxmlElement('w:spacing')
        spacing.set(qn('w:before'), str(before_pt * 20))  # 20 twips = 1 point
        spacing.set(qn('w:after'), str(after_pt * 20))
        pPr.append(spacing)

    def _save_verification_docx(self, pages_content: list[list[ParagraphData]], output_path: str) -> None:
        """
        Save verification document with ALL paragraphs (even empty ones) for QA.

        This document preserves the complete OCR output including empty paragraphs
        and page structure for verification purposes.

        Args:
            pages_content: List of ParagraphData lists for each page
            output_path: Path to save verification DOCX file
        """
        logger.debug("Saving verification DOCX with %d pages: %s",
                    len(pages_content), os.path.basename(output_path))

        try:
            document = Document()
            total_paragraph_count = 0

            # Add metadata comment at top
            header_para = document.add_paragraph("OCR Verification Document - Complete Output")
            header_para.runs[0].bold = True
            header_para.runs[0].font.size = Pt(14)
            document.add_paragraph()  # Blank line after header

            for page_num, page_paragraphs in enumerate(pages_content, 1):
                num_chars = sum(len(p.text) for p in page_paragraphs)
                logger.debug("Adding verification page %d to document (%d paragraphs, %d characters)",
                           page_num, len(page_paragraphs), num_chars)

                # Add each paragraph (including empty ones)
                for para_data in page_paragraphs:
                    paragraph = document.add_paragraph(para_data.text)
                    # Set font size
                    for run in paragraph.runs:
                        run.font.size = Pt(11)
                    total_paragraph_count += 1

                # Add page break (except after last page)
                if page_num < len(pages_content):
                    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
                    logger.debug("Added page break after page %d", page_num)

            logger.debug("Saving verification DOCX file to: %s", output_path)
            document.save(output_path)

            logger.info("PARAGRAPH_COUNT_VERIFICATION: stage=VERIFICATION_DOCX, count=%d", total_paragraph_count)
            logger.info("Verification DOCX saved successfully: %s", os.path.basename(output_path))

        except Exception as e:
            logger.error("Error saving verification DOCX: %s", e, exc_info=True)
            raise

    def _save_clean_docx(self, paragraphs: list[ParagraphData], output_path: str) -> None:
        """
        Save clean document with filtered paragraphs for translation.

        This document contains only valid content paragraphs with proper formatting
        and spacing, ready for translation. Page breaks are inserted between pages
        to preserve original document pagination.

        Args:
            paragraphs: Flat list of filtered ParagraphData objects
            output_path: Path to save clean DOCX file

        Raises:
            RuntimeError: If paragraph count verification fails
        """
        logger.debug("Saving clean DOCX with %d paragraphs: %s",
                    len(paragraphs), os.path.basename(output_path))

        try:
            input_count = len(paragraphs)
            logger.info("PARAGRAPH_COUNT_VERIFICATION: stage=CLEAN_DOCX_INPUT, count=%d", input_count)

            # Count paragraphs by role for logging
            role_counts = {}
            for para in paragraphs:
                role = para.role if hasattr(para, 'role') and para.role else 'body'
                role_counts[role] = role_counts.get(role, 0) + 1
            logger.info("Paragraph roles detected: %s", role_counts)

            document = Document()
            output_paragraph_count = 0
            current_page = None  # Track current page number
            page_break_count = 0  # Track page breaks inserted

            for para_data in paragraphs:
                # Insert page break when transitioning to a new page
                if current_page is not None and para_data.page != current_page:
                    document.add_page_break()
                    page_break_count += 1
                    logger.debug("Inserted page break before page %d", para_data.page)

                # Add paragraph with text
                paragraph = document.add_paragraph(para_data.text)

                # Apply role-based formatting based on Azure Layout model
                role = para_data.role if hasattr(para_data, 'role') else None

                # Detect and apply alignment from bounding box
                detected_alignment = self._detect_alignment_from_bounding_box(
                    para_data.bounding_box,
                    page_width=getattr(self, '_current_page_width', 8.5),
                    role=role
                )
                if detected_alignment is not None:
                    paragraph.alignment = detected_alignment
                    logger.debug("Applied alignment %s to paragraph %d (role: %s)",
                               detected_alignment, para_data.paragraph_index, role)

                # Apply role-based font formatting
                if role == 'title':
                    # Large, bold (alignment detected from bounding box)
                    for run in paragraph.runs:
                        run.font.size = Pt(18)
                        run.font.bold = True
                    logger.debug("Applied title formatting to paragraph %d", para_data.paragraph_index)
                elif role == 'sectionHeading':
                    # Medium, bold for section headings
                    for run in paragraph.runs:
                        run.font.size = Pt(14)
                        run.font.bold = True
                    logger.debug("Applied section heading formatting to paragraph %d", para_data.paragraph_index)
                elif role == 'pageHeader' or role == 'pageFooter':
                    # Small, italic for headers/footers
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
                        run.font.italic = True
                    logger.debug("Applied %s formatting to paragraph %d", role, para_data.paragraph_index)
                elif role == 'pageNumber':
                    # Small (alignment detected from bounding box)
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
                    logger.debug("Applied page number formatting to paragraph %d", para_data.paragraph_index)
                elif role == 'footnote':
                    # Small for footnotes
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
                    logger.debug("Applied footnote formatting to paragraph %d", para_data.paragraph_index)
                else:
                    # Normal body text (default)
                    for run in paragraph.runs:
                        run.font.size = Pt(11)

                # Set paragraph spacing (6pt before, 6pt after)
                self._set_paragraph_spacing(paragraph, before_pt=6, after_pt=6)

                current_page = para_data.page
                output_paragraph_count += 1

            logger.debug("Saving clean DOCX file to: %s", output_path)
            logger.info("Inserted %d page breaks for multi-page document", page_break_count)
            document.save(output_path)

            # Verify counts match
            logger.info("PARAGRAPH_COUNT_VERIFICATION: stage=CLEAN_DOCX_OUTPUT, count=%d", output_paragraph_count)
            logger.info("Clean DOCX paragraph count verification: %d input, %d output",
                       input_count, output_paragraph_count)

            # Raise exception if counts don't match
            if input_count != output_paragraph_count:
                error_msg = (
                    f"Paragraph count mismatch in clean DOCX creation: "
                    f"input={input_count}, output={output_paragraph_count}"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            logger.info("Clean DOCX file saved successfully: %s", os.path.basename(output_path))

        except RuntimeError:
            raise
        except Exception as e:
            logger.error("Error saving clean DOCX: %s", e, exc_info=True)
            raise
