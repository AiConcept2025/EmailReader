"""Unit tests for paragraph data models.

Tests for TextSpan and Paragraph dataclasses used in OCR processing
and translation workflows.
"""
import pytest
from dataclasses import asdict
from typing import Dict, List

from src.models.paragraph import TextSpan, Paragraph


class TestTextSpan:
    """Test suite for TextSpan dataclass."""

    def test_text_span_creation_plain_text(self):
        """Test creating a TextSpan with plain text (no formatting)."""
        span = TextSpan(text="Hello World")

        assert span.text == "Hello World"
        assert span.is_bold is False
        assert span.is_italic is False
        assert span.font_size is None

    def test_text_span_creation_with_bold(self):
        """Test creating a TextSpan with bold formatting."""
        span = TextSpan(text="Important", is_bold=True)

        assert span.text == "Important"
        assert span.is_bold is True
        assert span.is_italic is False
        assert span.font_size is None

    def test_text_span_creation_with_italic(self):
        """Test creating a TextSpan with italic formatting."""
        span = TextSpan(text="Emphasized", is_italic=True)

        assert span.text == "Emphasized"
        assert span.is_bold is False
        assert span.is_italic is True
        assert span.font_size is None

    def test_text_span_creation_with_font_size(self):
        """Test creating a TextSpan with font size."""
        span = TextSpan(text="Sized Text", font_size=14.5)

        assert span.text == "Sized Text"
        assert span.is_bold is False
        assert span.is_italic is False
        assert span.font_size == 14.5

    def test_text_span_creation_with_all_formatting(self):
        """Test creating a TextSpan with all formatting options."""
        span = TextSpan(
            text="Formatted Text",
            is_bold=True,
            is_italic=True,
            font_size=16.0
        )

        assert span.text == "Formatted Text"
        assert span.is_bold is True
        assert span.is_italic is True
        assert span.font_size == 16.0

    def test_text_span_serializable_to_dict(self):
        """Test that TextSpan can be converted to a dictionary."""
        span = TextSpan(
            text="Test",
            is_bold=True,
            is_italic=False,
            font_size=12.0
        )

        span_dict = asdict(span)

        assert isinstance(span_dict, dict)
        assert span_dict["text"] == "Test"
        assert span_dict["is_bold"] is True
        assert span_dict["is_italic"] is False
        assert span_dict["font_size"] == 12.0


class TestParagraph:
    """Test suite for Paragraph dataclass."""

    def test_paragraph_creation_minimal(self):
        """Test creating a Paragraph with minimal required fields."""
        para = Paragraph(
            content="This is a paragraph.",
            page=1,
            role="paragraph"
        )

        assert para.content == "This is a paragraph."
        assert para.page == 1
        assert para.role == "paragraph"
        assert para.spans == []
        assert para.bounding_box is None
        assert para.is_list_item is False
        assert para.list_marker is None

    def test_paragraph_creation_with_title_role(self):
        """Test creating a Paragraph with title role."""
        para = Paragraph(
            content="Document Title",
            page=1,
            role="title"
        )

        assert para.content == "Document Title"
        assert para.role == "title"

    def test_paragraph_creation_with_heading_role(self):
        """Test creating a Paragraph with heading role."""
        para = Paragraph(
            content="Section Heading",
            page=2,
            role="heading"
        )

        assert para.content == "Section Heading"
        assert para.page == 2
        assert para.role == "heading"

    def test_paragraph_creation_with_spans(self):
        """Test creating a Paragraph with formatted text spans."""
        spans = [
            TextSpan(text="Normal text "),
            TextSpan(text="bold text", is_bold=True),
            TextSpan(text=" more normal")
        ]

        para = Paragraph(
            content="Normal text bold text more normal",
            page=1,
            role="paragraph",
            spans=spans
        )

        assert len(para.spans) == 3
        assert para.spans[0].text == "Normal text "
        assert para.spans[0].is_bold is False
        assert para.spans[1].text == "bold text"
        assert para.spans[1].is_bold is True
        assert para.spans[2].text == " more normal"

    def test_paragraph_creation_with_bounding_box(self):
        """Test creating a Paragraph with bounding box coordinates."""
        bbox = {
            "x": 100.0,
            "y": 200.0,
            "width": 400.0,
            "height": 50.0
        }

        para = Paragraph(
            content="Positioned text",
            page=1,
            role="paragraph",
            bounding_box=bbox
        )

        assert para.bounding_box is not None
        assert para.bounding_box["x"] == 100.0
        assert para.bounding_box["y"] == 200.0
        assert para.bounding_box["width"] == 400.0
        assert para.bounding_box["height"] == 50.0

    def test_paragraph_creation_as_list_item(self):
        """Test creating a Paragraph as a list item."""
        para = Paragraph(
            content="First item",
            page=1,
            role="listItem",
            is_list_item=True,
            list_marker="1."
        )

        assert para.is_list_item is True
        assert para.list_marker == "1."
        assert para.role == "listItem"

    def test_paragraph_creation_as_bullet_list_item(self):
        """Test creating a Paragraph as a bullet list item."""
        para = Paragraph(
            content="Bullet point",
            page=1,
            role="listItem",
            is_list_item=True,
            list_marker="•"
        )

        assert para.is_list_item is True
        assert para.list_marker == "•"

    def test_paragraph_creation_with_all_fields(self):
        """Test creating a Paragraph with all fields populated."""
        spans = [
            TextSpan(text="Complete ", is_bold=True, font_size=14.0),
            TextSpan(text="paragraph", is_italic=True, font_size=14.0)
        ]
        bbox = {"x": 50.0, "y": 100.0, "width": 500.0, "height": 30.0}

        para = Paragraph(
            content="Complete paragraph",
            page=3,
            role="heading",
            spans=spans,
            bounding_box=bbox,
            is_list_item=False,
            list_marker=None
        )

        assert para.content == "Complete paragraph"
        assert para.page == 3
        assert para.role == "heading"
        assert len(para.spans) == 2
        assert para.bounding_box == bbox
        assert para.is_list_item is False
        assert para.list_marker is None

    def test_paragraph_serializable_to_dict(self):
        """Test that Paragraph can be converted to a dictionary."""
        spans = [TextSpan(text="Test", is_bold=True)]
        bbox = {"x": 0.0, "y": 0.0, "width": 100.0, "height": 20.0}

        para = Paragraph(
            content="Test paragraph",
            page=1,
            role="paragraph",
            spans=spans,
            bounding_box=bbox,
            is_list_item=True,
            list_marker="•"
        )

        para_dict = asdict(para)

        assert isinstance(para_dict, dict)
        assert para_dict["content"] == "Test paragraph"
        assert para_dict["page"] == 1
        assert para_dict["role"] == "paragraph"
        assert isinstance(para_dict["spans"], list)
        assert len(para_dict["spans"]) == 1
        assert para_dict["spans"][0]["text"] == "Test"
        assert para_dict["bounding_box"] == bbox
        assert para_dict["is_list_item"] is True
        assert para_dict["list_marker"] == "•"

    def test_paragraph_default_empty_spans_list(self):
        """Test that spans defaults to an empty list, not shared between instances."""
        para1 = Paragraph(content="First", page=1, role="paragraph")
        para2 = Paragraph(content="Second", page=1, role="paragraph")

        # Add span to first paragraph
        para1.spans.append(TextSpan(text="Test"))

        # Verify second paragraph still has empty list (no shared mutable default)
        assert len(para1.spans) == 1
        assert len(para2.spans) == 0

    def test_paragraph_multiple_roles(self):
        """Test creating paragraphs with different role types."""
        roles = ["title", "heading", "paragraph", "listItem", "caption"]

        for idx, role in enumerate(roles):
            para = Paragraph(
                content=f"Content for {role}",
                page=idx + 1,
                role=role
            )
            assert para.role == role
            assert para.content == f"Content for {role}"
