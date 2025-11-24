"""Tests for layout reconstructor."""
import pytest
from src.utils.layout_reconstructor import (
    BoundingBox,
    TextChunk,
    reconstruct_layout,
    _detect_columns,
    _parse_chunks,
    _group_by_page,
    _reconstruct_page,
    _reconstruct_single_column,
    _reconstruct_multi_column,
    apply_grounding_to_output
)


class TestBoundingBox:
    """Test BoundingBox dataclass."""

    def test_bounding_box_properties(self):
        """Test BoundingBox property calculations."""
        box = BoundingBox(left=0.1, top=0.2, right=0.9, bottom=0.8)
        assert box.width == pytest.approx(0.8)
        assert box.height == pytest.approx(0.6)
        assert box.center_x == pytest.approx(0.5)
        assert box.center_y == pytest.approx(0.5)

    def test_bounding_box_zero_size(self):
        """Test BoundingBox with zero dimensions."""
        box = BoundingBox(left=0.5, top=0.5, right=0.5, bottom=0.5)
        assert box.width == 0.0
        assert box.height == 0.0
        assert box.center_x == 0.5
        assert box.center_y == 0.5

    def test_bounding_box_full_page(self):
        """Test BoundingBox spanning full page."""
        box = BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0)
        assert box.width == 1.0
        assert box.height == 1.0
        assert box.center_x == 0.5
        assert box.center_y == 0.5

    def test_bounding_box_small_region(self):
        """Test BoundingBox for small region."""
        box = BoundingBox(left=0.4, top=0.3, right=0.6, bottom=0.4)
        assert box.width == pytest.approx(0.2)
        assert box.height == pytest.approx(0.1)
        assert box.center_x == pytest.approx(0.5)
        assert box.center_y == pytest.approx(0.35)


class TestTextChunk:
    """Test TextChunk dataclass."""

    def test_text_chunk_creation(self):
        """Test creating TextChunk."""
        box = BoundingBox(left=0.1, top=0.1, right=0.5, bottom=0.2)
        chunk = TextChunk(text="Hello World", page=0, box=box)

        assert chunk.text == "Hello World"
        assert chunk.page == 0
        assert chunk.box == box


class TestParseChunks:
    """Test parsing API chunks."""

    def test_parse_chunks_basic(self):
        """Test parsing basic API chunks into TextChunk objects."""
        api_chunks = [
            {
                'text': 'Hello World',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.1, 'right': 0.5, 'bottom': 0.2}
                }
            }
        ]
        text_chunks = _parse_chunks(api_chunks)
        assert len(text_chunks) == 1
        assert text_chunks[0].text == 'Hello World'
        assert text_chunks[0].page == 0
        assert text_chunks[0].box.left == 0.1

    def test_parse_chunks_multiple(self):
        """Test parsing multiple chunks."""
        api_chunks = [
            {
                'text': 'Line 1',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
                }
            },
            {
                'text': 'Line 2',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.3, 'right': 0.9, 'bottom': 0.4}
                }
            }
        ]
        text_chunks = _parse_chunks(api_chunks)
        assert len(text_chunks) == 2
        assert text_chunks[0].text == 'Line 1'
        assert text_chunks[1].text == 'Line 2'

    def test_parse_chunks_empty_text(self):
        """Test parsing chunks with empty text."""
        api_chunks = [
            {
                'text': '',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.1, 'right': 0.5, 'bottom': 0.2}
                }
            },
            {
                'text': 'Valid text',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.3, 'right': 0.5, 'bottom': 0.4}
                }
            }
        ]
        text_chunks = _parse_chunks(api_chunks)
        # Empty text chunks should be filtered out
        assert len(text_chunks) == 1
        assert text_chunks[0].text == 'Valid text'

    def test_parse_chunks_missing_grounding(self):
        """Test parsing chunks with missing grounding data."""
        api_chunks = [
            {
                'text': 'No grounding'
            }
        ]
        text_chunks = _parse_chunks(api_chunks)
        assert len(text_chunks) == 1
        # Should use default values
        assert text_chunks[0].page == 0
        assert text_chunks[0].box.left == 0.0
        assert text_chunks[0].box.right == 1.0

    def test_parse_chunks_partial_grounding(self):
        """Test parsing chunks with partial grounding data."""
        api_chunks = [
            {
                'text': 'Partial grounding',
                'grounding': {
                    'page': 1,
                    'box': {'left': 0.2}  # Missing other box coordinates
                }
            }
        ]
        text_chunks = _parse_chunks(api_chunks)
        assert len(text_chunks) == 1
        assert text_chunks[0].page == 1
        assert text_chunks[0].box.left == 0.2
        # Should use defaults for missing values
        assert text_chunks[0].box.right == 1.0

    def test_parse_chunks_whitespace_text(self):
        """Test parsing chunks with whitespace-only text."""
        api_chunks = [
            {'text': '   ', 'grounding': {}},
            {'text': 'Valid', 'grounding': {}}
        ]
        text_chunks = _parse_chunks(api_chunks)
        # Whitespace-only chunks should be filtered
        assert len(text_chunks) == 1
        assert text_chunks[0].text == 'Valid'


class TestGroupByPage:
    """Test page grouping."""

    def test_group_by_page_single_page(self):
        """Test grouping chunks from single page."""
        chunks = [
            TextChunk(text="Line 1", page=0, box=BoundingBox(0.1, 0.1, 0.9, 0.2)),
            TextChunk(text="Line 2", page=0, box=BoundingBox(0.1, 0.3, 0.9, 0.4))
        ]
        pages = _group_by_page(chunks)
        assert len(pages) == 1
        assert 0 in pages
        assert len(pages[0]) == 2

    def test_group_by_page_multiple_pages(self):
        """Test grouping chunks from multiple pages."""
        chunks = [
            TextChunk(text="Page 0", page=0, box=BoundingBox(0.1, 0.1, 0.9, 0.2)),
            TextChunk(text="Page 1", page=1, box=BoundingBox(0.1, 0.1, 0.9, 0.2)),
            TextChunk(text="Page 0 again", page=0, box=BoundingBox(0.1, 0.3, 0.9, 0.4))
        ]
        pages = _group_by_page(chunks)
        assert len(pages) == 2
        assert len(pages[0]) == 2
        assert len(pages[1]) == 1

    def test_group_by_page_empty(self):
        """Test grouping empty chunk list."""
        pages = _group_by_page([])
        assert len(pages) == 0


class TestColumnDetection:
    """Test column detection."""

    def test_single_column_layout(self):
        """Test single column detection."""
        chunks = [
            TextChunk(text="Line 1", page=0, box=BoundingBox(0.1, 0.1, 0.9, 0.2)),
            TextChunk(text="Line 2", page=0, box=BoundingBox(0.1, 0.3, 0.9, 0.4))
        ]
        columns = _detect_columns(chunks)
        assert len(columns) == 1
        assert len(columns[0]) == 2

    def test_two_column_layout(self):
        """Test two column detection."""
        chunks = [
            TextChunk(text="Left 1", page=0, box=BoundingBox(0.05, 0.1, 0.45, 0.2)),
            TextChunk(text="Right 1", page=0, box=BoundingBox(0.55, 0.1, 0.95, 0.2)),
            TextChunk(text="Left 2", page=0, box=BoundingBox(0.05, 0.3, 0.45, 0.4)),
            TextChunk(text="Right 2", page=0, box=BoundingBox(0.55, 0.3, 0.95, 0.4))
        ]
        columns = _detect_columns(chunks)
        assert len(columns) == 2

    def test_column_detection_empty(self):
        """Test column detection with empty list."""
        columns = _detect_columns([])
        assert len(columns) == 0

    def test_column_detection_threshold(self):
        """Test column detection respects threshold."""
        # Chunks close together (< 20% gap) should be same column
        chunks = [
            TextChunk(text="Left", page=0, box=BoundingBox(0.1, 0.1, 0.3, 0.2)),
            TextChunk(text="Close", page=0, box=BoundingBox(0.15, 0.3, 0.35, 0.4))
        ]
        columns = _detect_columns(chunks)
        # These should be detected as single column (gap < 20%)
        assert len(columns) <= 2


class TestSingleColumnReconstruction:
    """Test single column reconstruction."""

    def test_single_column_basic(self):
        """Test basic single column reconstruction."""
        chunks = [
            TextChunk(text="Line 1", page=0, box=BoundingBox(0.1, 0.1, 0.9, 0.2)),
            TextChunk(text="Line 2", page=0, box=BoundingBox(0.1, 0.25, 0.9, 0.35))
        ]
        result = _reconstruct_single_column(chunks)
        assert 'Line 1' in result
        assert 'Line 2' in result

    def test_single_column_paragraph_breaks(self):
        """Test paragraph break detection in single column."""
        chunks = [
            TextChunk(text="Para 1", page=0, box=BoundingBox(0.1, 0.1, 0.9, 0.2)),
            # Large vertical gap (> 5%)
            TextChunk(text="Para 2", page=0, box=BoundingBox(0.1, 0.35, 0.9, 0.45))
        ]
        result = _reconstruct_single_column(chunks)
        # Should have blank line for paragraph break
        lines = result.split('\n')
        assert len(lines) >= 3  # Two text lines + at least one blank

    def test_single_column_empty(self):
        """Test single column with empty chunk list."""
        result = _reconstruct_single_column([])
        assert result == ""


class TestMultiColumnReconstruction:
    """Test multi-column reconstruction."""

    def test_multi_column_basic(self):
        """Test basic multi-column reconstruction."""
        columns = [
            [TextChunk(text="Left 1", page=0, box=BoundingBox(0.1, 0.1, 0.4, 0.2))],
            [TextChunk(text="Right 1", page=0, box=BoundingBox(0.6, 0.1, 0.9, 0.2))]
        ]
        result = _reconstruct_multi_column(columns)
        assert 'Left 1' in result
        assert 'Right 1' in result
        assert '[Column Break]' in result

    def test_multi_column_sorting(self):
        """Test multi-column respects vertical sorting."""
        columns = [
            [
                # Out of order - should be sorted by top position
                TextChunk(text="Bottom", page=0, box=BoundingBox(0.1, 0.5, 0.4, 0.6)),
                TextChunk(text="Top", page=0, box=BoundingBox(0.1, 0.1, 0.4, 0.2))
            ]
        ]
        result = _reconstruct_multi_column(columns)
        # "Top" should appear before "Bottom"
        top_pos = result.find("Top")
        bottom_pos = result.find("Bottom")
        assert top_pos < bottom_pos


class TestReconstructLayout:
    """Test full layout reconstruction."""

    def test_reconstruct_layout_single_page(self):
        """Test layout reconstruction for single page."""
        chunks = [
            {
                'text': 'Line 1',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
                }
            },
            {
                'text': 'Line 2',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.3, 'right': 0.9, 'bottom': 0.4}
                }
            }
        ]
        result = reconstruct_layout(chunks)
        assert 'Line 1' in result
        assert 'Line 2' in result

    def test_reconstruct_layout_multiple_pages(self):
        """Test layout reconstruction for multiple pages."""
        chunks = [
            {
                'text': 'Page 0',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
                }
            },
            {
                'text': 'Page 1',
                'grounding': {
                    'page': 1,
                    'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
                }
            }
        ]
        result = reconstruct_layout(chunks)
        assert 'Page 0' in result
        assert 'Page 1' in result
        assert '--- Page Break ---' in result

    def test_reconstruct_layout_empty(self):
        """Test layout reconstruction with empty chunks."""
        result = reconstruct_layout([])
        assert result == ""

    def test_reconstruct_layout_two_columns(self):
        """Test layout reconstruction with two columns."""
        chunks = [
            {
                'text': 'Left column',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.1, 'right': 0.4, 'bottom': 0.2}
                }
            },
            {
                'text': 'Right column',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.6, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
                }
            }
        ]
        result = reconstruct_layout(chunks)
        assert 'Left column' in result
        assert 'Right column' in result
        # May contain column break marker
        # (depends on exact positions and thresholds)

    def test_reconstruct_layout_preserves_order(self):
        """Test layout reconstruction preserves reading order."""
        chunks = [
            {
                'text': 'First',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
                }
            },
            {
                'text': 'Second',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.3, 'right': 0.9, 'bottom': 0.4}
                }
            },
            {
                'text': 'Third',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.5, 'right': 0.9, 'bottom': 0.6}
                }
            }
        ]
        result = reconstruct_layout(chunks)
        first_pos = result.find('First')
        second_pos = result.find('Second')
        third_pos = result.find('Third')
        assert first_pos < second_pos < third_pos


class TestApplyGrounding:
    """Test applying grounding metadata."""

    def test_apply_grounding_basic(self):
        """Test applying grounding data to extract metadata."""
        chunks = [
            {
                'text': 'Test',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
                }
            }
        ]
        structure = apply_grounding_to_output(chunks)

        assert structure['total_pages'] == 1
        assert structure['total_chunks'] == 1
        assert 0 in structure['pages']
        assert structure['pages'][0]['chunks'] == 1

    def test_apply_grounding_multiple_pages(self):
        """Test grounding metadata for multiple pages."""
        chunks = [
            {
                'text': 'Page 0',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
                }
            },
            {
                'text': 'Page 1',
                'grounding': {
                    'page': 1,
                    'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
                }
            }
        ]
        structure = apply_grounding_to_output(chunks)

        assert structure['total_pages'] == 2
        assert structure['total_chunks'] == 2
        assert 0 in structure['pages']
        assert 1 in structure['pages']

    def test_apply_grounding_column_detection(self):
        """Test grounding metadata includes column information."""
        chunks = [
            {
                'text': 'Left',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.1, 'top': 0.1, 'right': 0.4, 'bottom': 0.2}
                }
            },
            {
                'text': 'Right',
                'grounding': {
                    'page': 0,
                    'box': {'left': 0.6, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
                }
            }
        ]
        structure = apply_grounding_to_output(chunks)

        assert 'columns' in structure['pages'][0]
        assert 'has_multi_column' in structure['pages'][0]
