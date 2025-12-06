"""Data models for paragraph representation with formatting metadata.

This module provides dataclasses for representing text paragraphs with rich
formatting information extracted from OCR providers (Azure, LandingAI) and
used in translation workflows.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class TextSpan:
    """Represents a text segment with formatting attributes.

    TextSpan captures individual text segments within a paragraph along with
    their formatting properties. This allows preservation of formatting like
    bold, italic, and font size during OCR processing and translation.

    Attributes:
        text: The text content of this span
        is_bold: Whether the text is bold formatted (default: False)
        is_italic: Whether the text is italic formatted (default: False)
        font_size: Font size in points, if available (default: None)

    Example:
        >>> span = TextSpan(text="Important", is_bold=True, font_size=14.0)
        >>> span.text
        'Important'
        >>> span.is_bold
        True
    """

    text: str
    is_bold: bool = False
    is_italic: bool = False
    font_size: Optional[float] = None


@dataclass
class Paragraph:
    """Represents a paragraph with formatting metadata and structural information.

    Paragraph encapsulates the full text content along with formatting spans,
    spatial information (bounding box), page location, and semantic role.
    This model supports both Azure OCR paragraph extraction and Google
    Translation batch processing workflows.

    Attributes:
        content: The full paragraph text content
        page: The page number where this paragraph appears (1-indexed)
        role: The semantic role of this paragraph (e.g., 'title', 'heading',
              'paragraph', 'listItem', 'caption')
        spans: List of formatted text spans within the paragraph. Each span
               represents a segment with specific formatting. Defaults to
               empty list if no formatting information available.
        bounding_box: Optional dictionary containing spatial coordinates:
                     {'x': float, 'y': float, 'width': float, 'height': float}
        is_list_item: Whether this paragraph is part of a list (default: False)
        list_marker: The list marker if this is a list item (e.g., '•', '1.', 'a)')
                     (default: None)

    Example:
        >>> para = Paragraph(
        ...     content="Section heading",
        ...     page=1,
        ...     role="heading",
        ...     spans=[TextSpan(text="Section heading", is_bold=True, font_size=16.0)]
        ... )
        >>> para.role
        'heading'
        >>> len(para.spans)
        1
    """

    content: str
    page: int
    role: str
    spans: List[TextSpan] = field(default_factory=list)
    bounding_box: Optional[Dict[str, float]] = None
    is_list_item: bool = False
    list_marker: Optional[str] = None
