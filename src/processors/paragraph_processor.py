"""
Paragraph Processor Module

Filters and cleans OCR paragraph output by removing noise, normalizing whitespace,
and filtering invalid content while preserving document structure.
"""

import re
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, replace

from src.models.paragraph_data import ParagraphData


logger = logging.getLogger('EmailReader.Processors.Paragraph')


class ParagraphProcessor:
    """
    Processes and filters OCR paragraph output.

    This class provides methods to clean, normalize, and filter paragraph data
    extracted from OCR results. It removes invalid content, normalizes whitespace,
    and manages empty paragraphs while preserving the original structure for
    verification purposes.

    Example:
        >>> processor = ParagraphProcessor()
        >>> config = {'min_content_length': 10, 'normalize_whitespace': True}
        >>> paragraphs = [
        ...     ParagraphData(text="Hello world", page=1, paragraph_index=0),
        ...     ParagraphData(text="   ", page=1, paragraph_index=1),
        ...     ParagraphData(text="Valid content here", page=1, paragraph_index=2)
        ... ]
        >>> clean, all_para = processor.filter_paragraphs(paragraphs, config)
        >>> len(clean)
        2
    """

    # Regex patterns compiled for performance
    MULTIPLE_SPACES_PATTERN = re.compile(r' +')
    MULTIPLE_NEWLINES_PATTERN = re.compile(r'\n+')
    WORD_CHARS_PATTERN = re.compile(r'[a-zA-Z\u0400-\u04FF\u0100-\u017F]')  # Latin, Cyrillic, Extended Latin
    PUNCTUATION_ONLY_PATTERN = re.compile(r'^[\s\d\W]*$')

    def __init__(self):
        """Initialize the ParagraphProcessor."""
        logger.debug("ParagraphProcessor initialized")

    @classmethod
    def normalize_whitespace(cls, text: str) -> str:
        """
        Normalize whitespace in text.

        Replaces multiple spaces with single space, multiple newlines with single space,
        and strips leading/trailing whitespace while preserving single spaces between words.

        Args:
            text: The input text to normalize

        Returns:
            Normalized text with cleaned whitespace

        Example:
            >>> ParagraphProcessor.normalize_whitespace("Hello    world\\n\\n  test")
            'Hello world test'
            >>> ParagraphProcessor.normalize_whitespace("  spaces  everywhere  ")
            'spaces everywhere'
        """
        if not text:
            return ""

        # Replace multiple newlines with single space
        text = cls.MULTIPLE_NEWLINES_PATTERN.sub(' ', text)

        # Replace multiple spaces with single space
        text = cls.MULTIPLE_SPACES_PATTERN.sub(' ', text)

        # Strip leading and trailing whitespace
        text = text.strip()

        return text

    @classmethod
    def is_valid_content(cls, text: str, min_length: int = 10) -> bool:
        """
        Check if text contains valid content.

        Validates that text has sufficient length and contains actual words
        (letter characters) rather than just whitespace, punctuation, or numbers.

        Args:
            text: The text to validate
            min_length: Minimum character length required (default: 10)

        Returns:
            True if text contains valid content, False otherwise

        Example:
            >>> ParagraphProcessor.is_valid_content("Hello world")
            True
            >>> ParagraphProcessor.is_valid_content("123 ...")
            False
            >>> ParagraphProcessor.is_valid_content("Short")
            False
            >>> ParagraphProcessor.is_valid_content("   ")
            False
        """
        if not text or len(text) < min_length:
            return False

        # Check if text contains only punctuation, whitespace, and numbers
        if cls.PUNCTUATION_ONLY_PATTERN.match(text):
            return False

        # Check if text contains at least some word characters (letters)
        if not cls.WORD_CHARS_PATTERN.search(text):
            return False

        return True

    def filter_paragraphs(
        self,
        paragraphs: List[ParagraphData],
        config: Dict[str, Any]
    ) -> Tuple[List[ParagraphData], List[ParagraphData]]:
        """
        Filter and clean a list of paragraphs.

        Processes paragraphs by normalizing whitespace, filtering invalid content,
        and managing consecutive empty paragraphs. Returns both a cleaned list
        for translation and a complete list for verification.

        Args:
            paragraphs: List of ParagraphData objects to filter
            config: Configuration dictionary with keys:
                - min_content_length: Minimum chars to keep paragraph (default: 10)
                - max_consecutive_empty: Max empty paragraphs to keep (default: 1)
                - normalize_whitespace: Whether to normalize whitespace (default: True)

        Returns:
            Tuple of (clean_paragraphs, all_paragraphs_for_verification)
            - clean_paragraphs: Filtered list ready for translation
            - all_paragraphs_for_verification: All paragraphs with normalized whitespace

        Raises:
            ValueError: If config parameters are invalid

        Example:
            >>> processor = ParagraphProcessor()
            >>> config = {'min_content_length': 10, 'max_consecutive_empty': 1}
            >>> paragraphs = [
            ...     ParagraphData(text="Valid paragraph", page=1, paragraph_index=0),
            ...     ParagraphData(text="", page=1, paragraph_index=1),
            ...     ParagraphData(text="", page=1, paragraph_index=2),
            ...     ParagraphData(text="Another valid one", page=1, paragraph_index=3)
            ... ]
            >>> clean, verification = processor.filter_paragraphs(paragraphs, config)
            >>> len(clean)  # Two valid paragraphs + one empty for semantic break
            3
        """
        # Validate config parameters
        min_content_length = config.get('min_content_length', 10)
        max_consecutive_empty = config.get('max_consecutive_empty', 1)
        should_normalize = config.get('normalize_whitespace', True)

        if not isinstance(min_content_length, int) or min_content_length < 0:
            raise ValueError(f"min_content_length must be a non-negative integer, got {min_content_length}")

        if not isinstance(max_consecutive_empty, int) or max_consecutive_empty < 0:
            raise ValueError(f"max_consecutive_empty must be a non-negative integer, got {max_consecutive_empty}")

        if not paragraphs:
            logger.warning("PARAGRAPH_FILTER: Empty input paragraphs list")
            return [], []

        original_count = len(paragraphs)
        clean_paragraphs: List[ParagraphData] = []
        all_paragraphs: List[ParagraphData] = []
        consecutive_empty_count = 0

        for para in paragraphs:
            # Normalize whitespace in paragraph text
            normalized_text = self.normalize_whitespace(para.text) if should_normalize else para.text

            # Create new paragraph with normalized text (don't modify original)
            normalized_para = replace(para, text=normalized_text)

            # Add to verification list (all paragraphs with normalized whitespace)
            all_paragraphs.append(normalized_para)

            # Check if paragraph is empty or whitespace-only
            is_empty = not normalized_text or normalized_text.isspace()

            if is_empty:
                consecutive_empty_count += 1
                # Keep empty paragraph only if under the limit
                if consecutive_empty_count <= max_consecutive_empty:
                    clean_paragraphs.append(normalized_para)
            else:
                # Reset empty counter when we hit non-empty content
                consecutive_empty_count = 0

                # Check if content is valid
                if self.is_valid_content(normalized_text, min_content_length):
                    clean_paragraphs.append(normalized_para)
                else:
                    logger.debug(
                        f"Filtered out paragraph {para.paragraph_index} on page {para.page}: "
                        f"invalid content (length={len(normalized_text)})"
                    )

        clean_count = len(clean_paragraphs)
        removed_count = original_count - clean_count

        logger.info(
            f"PARAGRAPH_FILTER: original={original_count}, clean={clean_count}, removed={removed_count}"
        )

        return clean_paragraphs, all_paragraphs

    def process_ocr_result(
        self,
        pages_content: List[List[ParagraphData]],
        config: Dict[str, Any]
    ) -> Tuple[List[ParagraphData], List[List[ParagraphData]]]:
        """
        Process complete OCR result with multiple pages.

        Main entry point for processing OCR results. Flattens page structure,
        applies filtering, and returns both cleaned paragraphs for translation
        and original page structure for verification.

        Args:
            pages_content: List of pages, where each page is a list of ParagraphData
            config: Configuration dictionary (see filter_paragraphs for details)

        Returns:
            Tuple of (clean_flat_list, original_pages_structure_for_verification)
            - clean_flat_list: Flattened list of filtered paragraphs
            - original_pages_structure_for_verification: Original page structure preserved

        Raises:
            ValueError: If config parameters are invalid

        Example:
            >>> processor = ParagraphProcessor()
            >>> config = {'min_content_length': 10}
            >>> pages = [
            ...     [ParagraphData(text="Page 1 content", page=1, paragraph_index=0)],
            ...     [ParagraphData(text="Page 2 content", page=2, paragraph_index=1)]
            ... ]
            >>> clean_list, verification_pages = processor.process_ocr_result(pages, config)
            >>> len(clean_list)
            2
            >>> len(verification_pages)
            2
        """
        if not pages_content:
            logger.warning("PARAGRAPH_FILTER: Empty pages_content input")
            return [], []

        # Flatten pages into single list
        all_paragraphs_flat: List[ParagraphData] = []
        for page_paragraphs in pages_content:
            all_paragraphs_flat.extend(page_paragraphs)

        logger.info(
            f"Processing OCR result: {len(pages_content)} pages, "
            f"{len(all_paragraphs_flat)} total paragraphs"
        )

        # Filter paragraphs
        clean_paragraphs, verification_paragraphs = self.filter_paragraphs(
            all_paragraphs_flat,
            config
        )

        # Reconstruct original page structure for verification
        # (using the verification paragraphs which have normalized whitespace)
        verification_pages: List[List[ParagraphData]] = []
        verification_index = 0

        for page_paragraphs in pages_content:
            page_count = len(page_paragraphs)
            if verification_index + page_count <= len(verification_paragraphs):
                verification_pages.append(
                    verification_paragraphs[verification_index:verification_index + page_count]
                )
                verification_index += page_count
            else:
                # Handle edge case where counts don't match (shouldn't happen normally)
                logger.warning(
                    f"Page structure mismatch at index {verification_index}: "
                    f"expected {page_count} paragraphs"
                )
                verification_pages.append(page_paragraphs)

        return clean_paragraphs, verification_pages
