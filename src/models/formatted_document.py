"""
Structured data models for formatted document representation.

These models provide a structured way to represent documents with rich formatting
information extracted from OCR providers like LandingAI.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BoundingBox:
    """
    Represents a bounding box for text position on a page.

    Coordinates are normalized (0.0 to 1.0) relative to page dimensions.
    """
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        """Calculate width of bounding box."""
        return self.right - self.left

    @property
    def height(self) -> float:
        """Calculate height of bounding box."""
        return self.bottom - self.top

    @property
    def center_x(self) -> float:
        """Calculate horizontal center point."""
        return (self.left + self.right) / 2

    @property
    def center_y(self) -> float:
        """Calculate vertical center point."""
        return (self.top + self.bottom) / 2

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary format."""
        return {
            'left': self.left,
            'top': self.top,
            'right': self.right,
            'bottom': self.bottom
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'BoundingBox':
        """Create BoundingBox from dictionary."""
        return cls(
            left=data.get('left', 0.0),
            top=data.get('top', 0.0),
            right=data.get('right', 1.0),
            bottom=data.get('bottom', 1.0)
        )


@dataclass
class FormattedParagraph:
    """
    Represents a paragraph with formatting information.

    Attributes:
        text: The text content
        position: Bounding box position on the page
        font_size: Inferred font size (in points)
        is_bold: Whether text appears bold
        is_italic: Whether text appears italic
        column: Column number (0-based, 0 = leftmost column)
        vertical_gap_before: Vertical gap before this paragraph (normalized)
    """
    text: str
    position: BoundingBox
    font_size: Optional[float] = None
    is_bold: bool = False
    is_italic: bool = False
    column: int = 0
    vertical_gap_before: float = 0.0
    text_type: Optional[str] = None  # 'small', 'body', 'heading', 'subheading', 'title', 'large_title'

    def infer_font_size(
        self,
        base_size: float = 11.0,
        max_size: float = 48.0,
        calibration_factor: float = 400.0
    ) -> float:
        """
        Infer font size from bounding box height using calibrated scaling.

        This method uses empirical calibration from real document analysis:
        - Height 0.025 (2.5% of page) → ~10pt body text
        - Height 0.050 (5% of page) → ~20pt heading
        - Height 0.100 (10% of page) → ~40pt title

        Args:
            base_size: Default body text size in points (default: 11pt)
            max_size: Maximum font size in points (default: 48pt)
            calibration_factor: Multiplier to convert normalized height to points.
                              Default 400 is calibrated from Konnova.pdf analysis:
                              - Median height 0.0275 * 400 = 11pt (body text) ✓
                              - Large title 0.0730 * 400 = 29.2pt (appropriate) ✓

        Returns:
            Inferred font size in points, classified and clamped to realistic range
        """
        height = self.position.height

        # Calculate raw size using calibrated factor
        # Calibration: 400x gives realistic sizes for typical documents
        # - Small text (0.020-0.025): 8-10pt
        # - Body text (0.025-0.035): 10-14pt
        # - Headings (0.035-0.050): 14-20pt
        # - Titles (0.050-0.100): 20-40pt
        estimated_size = height * calibration_factor

        # Clamp to reasonable range
        min_size = base_size * 0.7  # Allow slightly smaller than base
        estimated_size = max(min_size, min(estimated_size, max_size))

        # Round to nearest 0.5pt for cleaner output
        # (e.g., 11.0, 11.5, 12.0 instead of 11.237)
        self.font_size = round(estimated_size * 2) / 2

        # Classify text type based on font size
        self._classify_text_type()

        return self.font_size

    def _classify_text_type(self) -> None:
        """
        Classify text type based on inferred font size.

        Sets self.text_type to one of:
        - 'small': 8-10pt (footnotes, captions)
        - 'body': 10-13pt (normal paragraph text)
        - 'heading': 13-18pt (section headings)
        - 'subheading': 18-24pt (subsection headings)
        - 'title': 24-36pt (document titles)
        - 'large_title': 36pt+ (large titles/headers)
        """
        if self.font_size is None:
            self.text_type = 'body'  # Default
            return

        if self.font_size < 10.0:
            self.text_type = 'small'
        elif self.font_size < 13.0:
            self.text_type = 'body'
        elif self.font_size < 18.0:
            self.text_type = 'heading'
        elif self.font_size < 24.0:
            self.text_type = 'subheading'
        elif self.font_size < 36.0:
            self.text_type = 'title'
        else:
            self.text_type = 'large_title'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'text': self.text,
            'position': self.position.to_dict(),
            'font_size': self.font_size,
            'text_type': self.text_type,
            'is_bold': self.is_bold,
            'is_italic': self.is_italic,
            'column': self.column,
            'vertical_gap_before': self.vertical_gap_before
        }


@dataclass
class FormattedPage:
    """
    Represents a page with multiple paragraphs.

    Attributes:
        page_number: Zero-based page number
        paragraphs: List of paragraphs on this page
        columns: Number of columns detected (1 = single column, 2+ = multi-column)
        width: Page width (if known)
        height: Page height (if known)
    """
    page_number: int
    paragraphs: List[FormattedParagraph] = field(default_factory=list)
    columns: int = 1
    width: Optional[float] = None
    height: Optional[float] = None

    def add_paragraph(self, paragraph: FormattedParagraph) -> None:
        """Add a paragraph to this page."""
        self.paragraphs.append(paragraph)

    def sort_paragraphs(self, reading_order: str = 'column-first') -> None:
        """
        Sort paragraphs in reading order.

        Args:
            reading_order: 'column-first' (top-to-bottom, then left-to-right)
                          or 'row-first' (left-to-right, then top-to-bottom)
        """
        if reading_order == 'column-first':
            # Sort by column, then by vertical position
            self.paragraphs.sort(key=lambda p: (p.column, p.position.top))
        else:
            # Sort by vertical position, then by column
            self.paragraphs.sort(key=lambda p: (p.position.top, p.column))

    def detect_columns(self, gap_threshold: float = 0.2) -> int:
        """
        Detect number of columns based on horizontal clustering.

        Args:
            gap_threshold: Minimum horizontal gap to consider a new column (normalized)

        Returns:
            Number of columns detected
        """
        if not self.paragraphs:
            return 1

        # Get unique horizontal positions (center x)
        x_positions = sorted(set(p.position.center_x for p in self.paragraphs))

        if len(x_positions) <= 1:
            self.columns = 1
            return 1

        # Find gaps between positions
        columns = 1
        for i in range(1, len(x_positions)):
            gap = x_positions[i] - x_positions[i-1]
            if gap > gap_threshold:
                columns += 1

        self.columns = columns

        # Assign column numbers to paragraphs
        for para in self.paragraphs:
            para.column = self._get_column_for_position(para.position.center_x, x_positions, gap_threshold)

        return columns

    def _get_column_for_position(self, x: float, x_positions: List[float], gap_threshold: float) -> int:
        """Get column number for a given x position."""
        column = 0
        for i in range(1, len(x_positions)):
            if x > x_positions[i-1]:
                gap = x_positions[i] - x_positions[i-1]
                if gap > gap_threshold:
                    column += 1
        return column

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'page_number': self.page_number,
            'paragraphs': [p.to_dict() for p in self.paragraphs],
            'columns': self.columns,
            'width': self.width,
            'height': self.height
        }


@dataclass
class FormattedDocument:
    """
    Represents a complete document with multiple pages.

    Attributes:
        pages: List of formatted pages
        metadata: Additional document metadata
    """
    pages: List[FormattedPage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_page(self, page: FormattedPage) -> None:
        """Add a page to the document."""
        self.pages.append(page)

    @property
    def total_pages(self) -> int:
        """Get total number of pages."""
        return len(self.pages)

    @property
    def total_paragraphs(self) -> int:
        """Get total number of paragraphs across all pages."""
        return sum(len(page.paragraphs) for page in self.pages)

    def get_page(self, page_number: int) -> Optional[FormattedPage]:
        """Get a specific page by number (0-based)."""
        if 0 <= page_number < len(self.pages):
            return self.pages[page_number]
        return None

    def sort_all_pages(self, reading_order: str = 'column-first') -> None:
        """Sort paragraphs in all pages."""
        for page in self.pages:
            page.sort_paragraphs(reading_order)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'pages': [p.to_dict() for p in self.pages],
            'metadata': self.metadata,
            'total_pages': self.total_pages,
            'total_paragraphs': self.total_paragraphs
        }

    @classmethod
    def from_landing_ai_response(cls, response_data: Dict[str, Any]) -> 'FormattedDocument':
        """
        Create a FormattedDocument from LandingAI API response.

        Args:
            response_data: LandingAI API response with chunks

        Returns:
            FormattedDocument instance
        """
        import re
        from src.config import get_config_value

        # Get calibration factor from config
        calibration_factor = get_config_value('quality.calibration_factor', 400.0)

        document = cls()
        chunks = response_data.get('chunks', [])

        if not chunks:
            return document

        # Group chunks by page
        pages_dict: Dict[int, List[Dict[str, Any]]] = {}
        for chunk in chunks:
            grounding = chunk.get('grounding', {})
            page_num = grounding.get('page', 0)

            if page_num not in pages_dict:
                pages_dict[page_num] = []

            pages_dict[page_num].append(chunk)

        # Create formatted pages
        for page_num in sorted(pages_dict.keys()):
            page = FormattedPage(page_number=page_num)

            page_chunks = pages_dict[page_num]

            for chunk in page_chunks:
                # Filter out decorative elements by chunk type
                chunk_type = chunk.get('type', 'text')

                # Skip non-text chunks (logos, QR codes, signatures, figures, images, borders, etc.)
                # Note: LandingAI may return various chunk types for decorative elements
                if chunk_type in [
                    'logo', 'scan_code', 'attestation', 'figure', 'image', 'barcode',
                    'border', 'decorative', 'graphic', 'icon', 'signature',
                    'chunkLogo', 'chunkScanCode', 'chunkAttestation', 'chunkFigure',
                    'chunkImage', 'chunkBarcode', 'chunkBorder', 'chunkDecorative'
                ]:
                    continue

                # LandingAI uses 'markdown' field, not 'text'
                markdown = chunk.get('markdown', '')
                grounding = chunk.get('grounding', {})
                box_data = grounding.get('box', {})

                if not box_data:
                    continue

                # Extract clean text from markdown
                text = cls._extract_text_from_markdown(markdown)

                # Skip empty chunks
                if not text.strip():
                    continue

                # Filter out decorative descriptions even if type='text'
                if cls._is_decorative_description(text):
                    continue

                # Create bounding box
                bbox = BoundingBox.from_dict(box_data)

                # Create paragraph
                paragraph = FormattedParagraph(
                    text=text,
                    position=bbox
                )

                # Infer font size with config calibration factor
                paragraph.infer_font_size(calibration_factor=calibration_factor)

                page.add_paragraph(paragraph)

            # Detect columns
            page.detect_columns(gap_threshold=0.2)

            # Sort paragraphs in reading order
            page.sort_paragraphs(reading_order='column-first')

            # Add page to document
            document.add_page(page)

        # Add metadata
        document.metadata = {
            'source': 'LandingAI',
            'total_chunks': len(chunks)
        }

        return document

    @staticmethod
    def _extract_text_from_markdown(markdown: str) -> str:
        """
        Extract clean text from LandingAI markdown format.

        LandingAI markdown contains:
        - HTML anchor tags: <a id='...'></a>
        - Special markup: <::logo: description::>, <::table: ...::>, etc.
        - Special markup variations: <::description without type::>
        - Bracket comments: [Readable Text if any]
        - Regular text content

        Args:
            markdown: Raw markdown string from LandingAI

        Returns:
            Clean text content (excluding decorative descriptions and comments)
        """
        import re

        if not markdown:
            return ''

        text = markdown

        # Remove HTML anchor tags: <a id='...'></a>
        text = re.sub(r'<a\s+id=[\'"][^\'"]*[\'"]></a>', '', text)

        # Remove special markup tags in multiple formats:
        # Format 1: <::type: content::> - standard format with type label
        # Format 2: <::content::> - format without type label
        # Format 3: <::Any text with spaces: more content::> - type can contain spaces
        #
        # Strategy: Match everything between <:: and ::> regardless of content
        # This handles all variations including:
        # - <::logo: description::>
        # - <::A vertical decorative border with patterns::>
        # - <::scan_code: QR code info::>
        # - <::figure: image description::>
        #
        # Use DOTALL flag to match newlines within the markup
        text = re.sub(r'<::.*?::>', '', text, flags=re.DOTALL)

        # Remove bracket comments like [Readable Text if any]
        # These are LandingAI metadata annotations, not document content
        text = re.sub(r'\[([^\]]+)\]', '', text)

        # Clean up whitespace
        final_text = ' '.join(text.split())

        return final_text

    @staticmethod
    def _is_decorative_description(text: str) -> bool:
        """
        Detect if text is a decorative element description.

        LandingAI sometimes returns logo, signature, stamp, and other visual
        element descriptions as plain text chunks (type='text') without special
        markup. This method detects such descriptions by looking for common
        phrases used in visual element descriptions.

        Args:
            text: Text content to check

        Returns:
            True if text appears to be a decorative description, False otherwise
        """
        import re

        if not text or len(text.strip()) == 0:
            return False

        text_lower = text.lower()

        # Indicators of decorative/visual descriptions
        indicators = [
            # Logo descriptions
            'stylized', 'logo features', 'logo depicts', 'logo consists',
            # Signature descriptions
            'signature: illegible', 'handwritten signature', 'signature is present',
            '[signature]', '[signed]', 'illegible signature',
            # Stamp descriptions
            'official stamp', 'circular stamp', 'stamped', 'stamp/seal',
            # Decorative elements
            'decorative border', 'ornate', 'floral motifs', 'leaf-like motifs',
            'scalloped edge', 'intricate patterns',
            # Visual characteristics
            'teardrop shape', 'gradient', 'shadow effect', 'forward-moving shape',
            # QR/Barcode
            'qr code', 'barcode', 'scan code'
        ]

        # Count matching indicators
        matches = sum(1 for indicator in indicators if indicator in text_lower)

        # Filter if:
        # - Contains 2 or more indicators (high confidence), OR
        # - Contains 1 indicator AND text is short (<200 chars, likely a description)
        if matches >= 2 or (matches >= 1 and len(text) < 200):
            return True

        return False
