"""
Paragraph Data Model

Represents a paragraph extracted from OCR with associated metadata.
"""

from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class ParagraphData:
    """
    Data class representing a paragraph extracted from OCR.

    Attributes:
        text: The paragraph text content
        page: The page number (1-indexed) where the paragraph appears
        bounding_box: Optional bounding box coordinates from OCR
        confidence: Optional OCR confidence score (0.0 to 1.0)
        paragraph_index: Sequential index for tracking paragraphs across pages (0-indexed)
        role: Optional paragraph role from Azure Layout model (title, sectionHeading, pageHeader, etc.)

    Example:
        >>> para = ParagraphData(
        ...     text="Hello world",
        ...     page=1,
        ...     bounding_box={"x": 100, "y": 200, "width": 300, "height": 50},
        ...     confidence=0.95,
        ...     paragraph_index=0,
        ...     role="sectionHeading"
        ... )
        >>> print(para.text)
        Hello world
    """

    text: str
    page: int
    bounding_box: Optional[Dict[str, float]] = None
    confidence: Optional[float] = None
    paragraph_index: int = 0
    role: Optional[str] = None

    def __str__(self) -> str:
        """String representation for logging and debugging."""
        return f"ParagraphData(page={self.page}, index={self.paragraph_index}, text_len={len(self.text)}, confidence={self.confidence})"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"ParagraphData("
            f"text='{self.text[:50]}...', "
            f"page={self.page}, "
            f"bounding_box={self.bounding_box}, "
            f"confidence={self.confidence}, "
            f"paragraph_index={self.paragraph_index})"
        )
