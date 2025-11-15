"""Layout reconstruction utilities using LandingAI grounding data."""

import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module name.

    Args:
        name: Logger name (e.g., 'EmailReader.LayoutReconstructor')

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


logger = get_logger('EmailReader.LayoutReconstructor')


@dataclass
class BoundingBox:
    """Bounding box coordinates (normalized 0-1)."""
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        """Calculate bounding box width."""
        return self.right - self.left

    @property
    def height(self) -> float:
        """Calculate bounding box height."""
        return self.bottom - self.top

    @property
    def center_x(self) -> float:
        """Calculate horizontal center coordinate."""
        return (self.left + self.right) / 2

    @property
    def center_y(self) -> float:
        """Calculate vertical center coordinate."""
        return (self.top + self.bottom) / 2


@dataclass
class TextChunk:
    """Represents a text chunk with spatial information."""
    text: str
    page: int
    box: BoundingBox


def reconstruct_layout(chunks: List[Dict[str, Any]]) -> str:
    """
    Reconstruct document layout using grounding data.

    Processes chunks to maintain spatial positioning, detect columns,
    and preserve document structure.

    Args:
        chunks: List of chunks from LandingAI API response

    Returns:
        Text with preserved layout structure
    """
    if not chunks:
        logger.warning("Empty chunks list provided to reconstruct_layout")
        return ""

    logger.info(f"Reconstructing layout from {len(chunks)} chunks")

    # Parse chunks into structured data
    text_chunks = _parse_chunks(chunks)

    if not text_chunks:
        logger.warning("No valid text chunks after parsing")
        return ""

    # Group by page
    pages = _group_by_page(text_chunks)

    # Reconstruct each page
    page_texts = []
    for page_num in sorted(pages.keys()):
        page_chunks = pages[page_num]
        logger.debug(f"Reconstructing page {page_num} with {len(page_chunks)} chunks")
        page_text = _reconstruct_page(page_chunks)
        page_texts.append(page_text)

    # Combine pages with page breaks
    result = '\n\n--- Page Break ---\n\n'.join(page_texts)

    logger.info(f"Layout reconstruction complete ({len(pages)} pages, {len(result)} characters)")
    return result


def _parse_chunks(chunks: List[Dict[str, Any]]) -> List[TextChunk]:
    """
    Parse API chunks into TextChunk objects.

    Args:
        chunks: Raw chunks from LandingAI API

    Returns:
        List of parsed TextChunk objects
    """
    text_chunks = []

    for idx, chunk in enumerate(chunks):
        text = chunk.get('text', '').strip()
        if not text:
            logger.debug(f"Skipping empty chunk at index {idx}")
            continue

        grounding = chunk.get('grounding', {})
        if not grounding:
            logger.warning(f"Chunk {idx} missing grounding data, using defaults")

        page = grounding.get('page', 0)
        box_data = grounding.get('box', {})

        # Create bounding box with safe defaults
        box = BoundingBox(
            left=box_data.get('left', 0.0),
            top=box_data.get('top', 0.0),
            right=box_data.get('right', 1.0),
            bottom=box_data.get('bottom', 1.0)
        )

        text_chunks.append(TextChunk(text=text, page=page, box=box))
        logger.debug(
            f"Parsed chunk {idx}: page={page}, "
            f"box=({box.left:.2f},{box.top:.2f},{box.right:.2f},{box.bottom:.2f})"
        )

    logger.info(f"Parsed {len(text_chunks)} valid chunks from {len(chunks)} total chunks")
    return text_chunks


def _group_by_page(chunks: List[TextChunk]) -> Dict[int, List[TextChunk]]:
    """
    Group chunks by page number.

    Args:
        chunks: List of TextChunk objects

    Returns:
        Dictionary mapping page numbers to chunk lists
    """
    pages = defaultdict(list)
    for chunk in chunks:
        pages[chunk.page].append(chunk)

    page_dict = dict(pages)
    logger.debug(f"Grouped chunks into {len(page_dict)} pages")
    return page_dict


def _reconstruct_page(chunks: List[TextChunk]) -> str:
    """
    Reconstruct a single page's layout.

    Sorts chunks by vertical position (top to bottom),
    then detects and handles multi-column layouts.

    Args:
        chunks: List of TextChunk objects for a single page

    Returns:
        Reconstructed text for the page
    """
    if not chunks:
        return ""

    # Sort by vertical position (top to bottom), then horizontal (left to right)
    sorted_chunks = sorted(chunks, key=lambda c: (c.box.top, c.box.left))

    # Detect columns
    columns = _detect_columns(sorted_chunks)

    if len(columns) > 1:
        logger.debug(f"Detected {len(columns)} columns on page")
        return _reconstruct_multi_column(columns)
    else:
        logger.debug("Single column layout detected")
        return _reconstruct_single_column(sorted_chunks)


def _detect_columns(chunks: List[TextChunk]) -> List[List[TextChunk]]:
    """
    Detect column structure based on horizontal positioning.

    Uses clustering of center_x positions to identify columns.

    Args:
        chunks: List of TextChunk objects

    Returns:
        List of column lists, each containing chunks for that column
    """
    if not chunks:
        return []

    # Simple heuristic: chunks with similar horizontal positions are in same column
    # Sort by horizontal position
    h_sorted = sorted(chunks, key=lambda c: c.box.center_x)

    columns = []
    current_column = [h_sorted[0]]

    # Column separation threshold (20% of page width)
    COLUMN_GAP_THRESHOLD = 0.2

    for chunk in h_sorted[1:]:
        prev_x = current_column[0].box.center_x
        curr_x = chunk.box.center_x

        # If horizontal gap is large, start new column
        if abs(curr_x - prev_x) > COLUMN_GAP_THRESHOLD:
            logger.debug(
                f"Column break detected: prev_x={prev_x:.2f}, curr_x={curr_x:.2f}, "
                f"gap={abs(curr_x - prev_x):.2f}"
            )
            columns.append(current_column)
            current_column = [chunk]
        else:
            current_column.append(chunk)

    if current_column:
        columns.append(current_column)

    logger.debug(f"Column detection complete: {len(columns)} columns identified")
    return columns


def _reconstruct_single_column(chunks: List[TextChunk]) -> str:
    """
    Reconstruct text from single column layout.

    Args:
        chunks: List of TextChunk objects in reading order

    Returns:
        Reconstructed text with appropriate spacing
    """
    if not chunks:
        return ""

    lines = []
    prev_bottom = 0

    # Threshold for paragraph break (5% of page height)
    PARAGRAPH_GAP_THRESHOLD = 0.05

    for chunk in chunks:
        # Add vertical spacing if there's a gap
        vertical_gap = chunk.box.top - prev_bottom

        if vertical_gap > PARAGRAPH_GAP_THRESHOLD:
            # Add blank line for paragraph break
            lines.append("")
            logger.debug(f"Paragraph break detected: gap={vertical_gap:.2f}")

        lines.append(chunk.text)
        prev_bottom = chunk.box.bottom

    result = '\n'.join(lines)
    logger.debug(f"Single column reconstruction: {len(lines)} lines")
    return result


def _reconstruct_multi_column(columns: List[List[TextChunk]]) -> str:
    """
    Reconstruct text from multi-column layout.

    Processes each column top-to-bottom, combining at the end.

    Args:
        columns: List of column chunk lists

    Returns:
        Reconstructed text with column separators
    """
    column_texts = []

    for col_idx, col_chunks in enumerate(columns):
        logger.debug(f"Reconstructing column {col_idx + 1}/{len(columns)}")
        # Sort each column vertically
        sorted_chunks = sorted(col_chunks, key=lambda c: c.box.top)
        col_text = _reconstruct_single_column(sorted_chunks)
        column_texts.append(col_text)

    # Combine columns with separator
    result = '\n\n[Column Break]\n\n'.join(column_texts)
    logger.debug(f"Multi-column reconstruction: {len(columns)} columns combined")
    return result


def apply_grounding_to_output(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply grounding data to enhance output structure.

    Returns metadata about document structure for advanced processing.

    Args:
        chunks: API response chunks

    Returns:
        Dictionary with structure metadata
    """
    logger.debug("Applying grounding data to extract structure metadata")

    text_chunks = _parse_chunks(chunks)
    pages = _group_by_page(text_chunks)

    structure = {
        'total_pages': len(pages),
        'total_chunks': len(text_chunks),
        'pages': {}
    }

    for page_num, page_chunks in pages.items():
        columns = _detect_columns(page_chunks)
        structure['pages'][page_num] = {
            'chunks': len(page_chunks),
            'columns': len(columns),
            'has_multi_column': len(columns) > 1
        }

    logger.info(
        f"Structure metadata: {structure['total_pages']} pages, "
        f"{structure['total_chunks']} total chunks"
    )

    return structure
