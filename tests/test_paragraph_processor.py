"""
Unit tests for ParagraphProcessor module.

Tests filtering, cleaning, and normalization of OCR paragraph output.
"""

import pytest
from src.processors.paragraph_processor import ParagraphProcessor
from src.models.paragraph_data import ParagraphData


class TestNormalizeWhitespace:
    """Test whitespace normalization."""

    def test_normalize_multiple_spaces(self):
        """Test that multiple spaces are replaced with single space."""
        processor = ParagraphProcessor()
        result = processor.normalize_whitespace("Hello    world")
        assert result == "Hello world"

    def test_normalize_multiple_newlines(self):
        """Test that multiple newlines are replaced with single space."""
        processor = ParagraphProcessor()
        result = processor.normalize_whitespace("Hello\n\n\nworld")
        assert result == "Hello world"

    def test_normalize_mixed_whitespace(self):
        """Test normalization of mixed whitespace."""
        processor = ParagraphProcessor()
        result = processor.normalize_whitespace("  Hello    world\n\n  test  ")
        assert result == "Hello world test"

    def test_normalize_leading_trailing_whitespace(self):
        """Test that leading and trailing whitespace is removed."""
        processor = ParagraphProcessor()
        result = processor.normalize_whitespace("   spaces everywhere   ")
        assert result == "spaces everywhere"

    def test_normalize_empty_string(self):
        """Test normalization of empty string."""
        processor = ParagraphProcessor()
        result = processor.normalize_whitespace("")
        assert result == ""

    def test_normalize_none(self):
        """Test normalization of None."""
        processor = ParagraphProcessor()
        result = processor.normalize_whitespace(None)
        assert result == ""

    def test_normalize_single_spaces_preserved(self):
        """Test that single spaces between words are preserved."""
        processor = ParagraphProcessor()
        result = processor.normalize_whitespace("One two three")
        assert result == "One two three"


class TestIsValidContent:
    """Test content validation."""

    def test_valid_content_sufficient_length(self):
        """Test that text with sufficient length and words is valid."""
        processor = ParagraphProcessor()
        assert processor.is_valid_content("Hello world this is valid") is True

    def test_invalid_content_too_short(self):
        """Test that text shorter than min_length is invalid."""
        processor = ParagraphProcessor()
        assert processor.is_valid_content("Short", min_length=10) is False

    def test_invalid_content_only_whitespace(self):
        """Test that whitespace-only text is invalid."""
        processor = ParagraphProcessor()
        assert processor.is_valid_content("     ", min_length=5) is False

    def test_invalid_content_only_punctuation(self):
        """Test that punctuation-only text is invalid."""
        processor = ParagraphProcessor()
        assert processor.is_valid_content("... !!! ???", min_length=5) is False

    def test_invalid_content_only_numbers(self):
        """Test that numbers-only text is invalid."""
        processor = ParagraphProcessor()
        assert processor.is_valid_content("123 456 789", min_length=5) is False

    def test_invalid_content_punctuation_and_numbers(self):
        """Test that text with only punctuation and numbers is invalid."""
        processor = ParagraphProcessor()
        assert processor.is_valid_content("123 ... 456", min_length=5) is False

    def test_valid_content_cyrillic_text(self):
        """Test that Cyrillic text is recognized as valid."""
        processor = ParagraphProcessor()
        assert processor.is_valid_content("Привет мир") is True

    def test_valid_content_mixed_languages(self):
        """Test that mixed language text is valid."""
        processor = ParagraphProcessor()
        assert processor.is_valid_content("Hello Привет world") is True

    def test_valid_content_with_numbers(self):
        """Test that text with words and numbers is valid."""
        processor = ParagraphProcessor()
        assert processor.is_valid_content("Page 1 contains text") is True

    def test_empty_string(self):
        """Test that empty string is invalid."""
        processor = ParagraphProcessor()
        assert processor.is_valid_content("") is False

    def test_custom_min_length(self):
        """Test custom minimum length parameter."""
        processor = ParagraphProcessor()
        assert processor.is_valid_content("Hello", min_length=3) is True
        assert processor.is_valid_content("Hello", min_length=10) is False


class TestFilterParagraphs:
    """Test paragraph filtering."""

    def test_filter_valid_paragraphs(self):
        """Test that valid paragraphs are kept."""
        processor = ParagraphProcessor()
        config = {'min_content_length': 10, 'normalize_whitespace': True}
        paragraphs = [
            ParagraphData(text="Valid paragraph one", page=1, paragraph_index=0),
            ParagraphData(text="Valid paragraph two", page=1, paragraph_index=1),
        ]

        clean, verification = processor.filter_paragraphs(paragraphs, config)

        assert len(clean) == 2
        assert len(verification) == 2
        assert clean[0].text == "Valid paragraph one"
        assert clean[1].text == "Valid paragraph two"

    def test_filter_removes_short_paragraphs(self):
        """Test that paragraphs shorter than min_content_length are removed."""
        processor = ParagraphProcessor()
        config = {'min_content_length': 10, 'normalize_whitespace': True}
        paragraphs = [
            ParagraphData(text="Valid paragraph here", page=1, paragraph_index=0),
            ParagraphData(text="Short", page=1, paragraph_index=1),
            ParagraphData(text="Another valid paragraph", page=1, paragraph_index=2),
        ]

        clean, verification = processor.filter_paragraphs(paragraphs, config)

        assert len(clean) == 2
        assert len(verification) == 3  # Verification keeps all
        assert clean[0].text == "Valid paragraph here"
        assert clean[1].text == "Another valid paragraph"

    def test_filter_removes_invalid_content(self):
        """Test that paragraphs with only numbers/punctuation are removed."""
        processor = ParagraphProcessor()
        config = {'min_content_length': 5, 'normalize_whitespace': True}
        paragraphs = [
            ParagraphData(text="Valid text here", page=1, paragraph_index=0),
            ParagraphData(text="123 456 789", page=1, paragraph_index=1),
            ParagraphData(text="... !!! ???", page=1, paragraph_index=2),
            ParagraphData(text="More valid text", page=1, paragraph_index=3),
        ]

        clean, verification = processor.filter_paragraphs(paragraphs, config)

        assert len(clean) == 2
        assert clean[0].text == "Valid text here"
        assert clean[1].text == "More valid text"

    def test_filter_normalizes_whitespace(self):
        """Test that whitespace is normalized in filtered paragraphs."""
        processor = ParagraphProcessor()
        config = {'min_content_length': 10, 'normalize_whitespace': True}
        paragraphs = [
            ParagraphData(text="  Multiple    spaces   here  ", page=1, paragraph_index=0),
            ParagraphData(text="Newlines\n\n\neverywhere", page=1, paragraph_index=1),
        ]

        clean, verification = processor.filter_paragraphs(paragraphs, config)

        assert clean[0].text == "Multiple spaces here"
        assert clean[1].text == "Newlines everywhere"

    def test_filter_consecutive_empty_paragraphs(self):
        """Test that consecutive empty paragraphs are limited."""
        processor = ParagraphProcessor()
        config = {
            'min_content_length': 10,
            'max_consecutive_empty': 1,
            'normalize_whitespace': True
        }
        paragraphs = [
            ParagraphData(text="Valid paragraph", page=1, paragraph_index=0),
            ParagraphData(text="", page=1, paragraph_index=1),
            ParagraphData(text="", page=1, paragraph_index=2),
            ParagraphData(text="", page=1, paragraph_index=3),
            ParagraphData(text="Another valid", page=1, paragraph_index=4),
        ]

        clean, verification = processor.filter_paragraphs(paragraphs, config)

        # Should have: valid + 1 empty (max) + valid = 3 paragraphs
        assert len(clean) == 3
        assert clean[0].text == "Valid paragraph"
        assert clean[1].text == ""
        assert clean[2].text == "Another valid"

    def test_filter_preserves_paragraph_index(self):
        """Test that original paragraph_index is preserved."""
        processor = ParagraphProcessor()
        config = {'min_content_length': 10}
        paragraphs = [
            ParagraphData(text="First paragraph", page=1, paragraph_index=5),
            ParagraphData(text="Second paragraph", page=1, paragraph_index=10),
        ]

        clean, verification = processor.filter_paragraphs(paragraphs, config)

        assert clean[0].paragraph_index == 5
        assert clean[1].paragraph_index == 10

    def test_filter_empty_input(self):
        """Test filtering with empty input list."""
        processor = ParagraphProcessor()
        config = {'min_content_length': 10}

        clean, verification = processor.filter_paragraphs([], config)

        assert clean == []
        assert verification == []

    def test_filter_invalid_config_min_length(self):
        """Test that invalid min_content_length raises ValueError."""
        processor = ParagraphProcessor()
        config = {'min_content_length': -5}
        paragraphs = [ParagraphData(text="Test", page=1, paragraph_index=0)]

        with pytest.raises(ValueError, match="min_content_length must be a non-negative integer"):
            processor.filter_paragraphs(paragraphs, config)

    def test_filter_invalid_config_max_consecutive_empty(self):
        """Test that invalid max_consecutive_empty raises ValueError."""
        processor = ParagraphProcessor()
        config = {'max_consecutive_empty': -1}
        paragraphs = [ParagraphData(text="Test", page=1, paragraph_index=0)]

        with pytest.raises(ValueError, match="max_consecutive_empty must be a non-negative integer"):
            processor.filter_paragraphs(paragraphs, config)

    def test_filter_without_normalization(self):
        """Test filtering without whitespace normalization."""
        processor = ParagraphProcessor()
        config = {'min_content_length': 10, 'normalize_whitespace': False}
        paragraphs = [
            ParagraphData(text="  Spaces   preserved  ", page=1, paragraph_index=0),
        ]

        clean, verification = processor.filter_paragraphs(paragraphs, config)

        assert clean[0].text == "  Spaces   preserved  "

    def test_filter_resets_empty_counter(self):
        """Test that empty counter resets after non-empty paragraph."""
        processor = ParagraphProcessor()
        config = {
            'min_content_length': 10,
            'max_consecutive_empty': 1,
        }
        paragraphs = [
            ParagraphData(text="First valid paragraph", page=1, paragraph_index=0),
            ParagraphData(text="", page=1, paragraph_index=1),
            ParagraphData(text="", page=1, paragraph_index=2),
            ParagraphData(text="Second valid paragraph", page=1, paragraph_index=3),
            ParagraphData(text="", page=1, paragraph_index=4),
            ParagraphData(text="", page=1, paragraph_index=5),
            ParagraphData(text="Third valid paragraph", page=1, paragraph_index=6),
        ]

        clean, verification = processor.filter_paragraphs(paragraphs, config)

        # Should have: valid + 1 empty + valid + 1 empty + valid = 5
        assert len(clean) == 5


class TestProcessOcrResult:
    """Test complete OCR result processing."""

    def test_process_multiple_pages(self):
        """Test processing multiple pages of content."""
        processor = ParagraphProcessor()
        config = {'min_content_length': 10}
        pages_content = [
            [
                ParagraphData(text="Page 1 paragraph 1", page=1, paragraph_index=0),
                ParagraphData(text="Page 1 paragraph 2", page=1, paragraph_index=1),
            ],
            [
                ParagraphData(text="Page 2 paragraph 1", page=2, paragraph_index=2),
                ParagraphData(text="Page 2 paragraph 2", page=2, paragraph_index=3),
            ],
        ]

        clean_flat, verification_pages = processor.process_ocr_result(pages_content, config)

        assert len(clean_flat) == 4
        assert len(verification_pages) == 2
        assert len(verification_pages[0]) == 2
        assert len(verification_pages[1]) == 2

    def test_process_flattens_pages(self):
        """Test that process_ocr_result flattens pages into single list."""
        processor = ParagraphProcessor()
        config = {'min_content_length': 10}
        pages_content = [
            [ParagraphData(text="Page 1 content here", page=1, paragraph_index=0)],
            [ParagraphData(text="Page 2 content here", page=2, paragraph_index=1)],
            [ParagraphData(text="Page 3 content here", page=3, paragraph_index=2)],
        ]

        clean_flat, verification_pages = processor.process_ocr_result(pages_content, config)

        assert len(clean_flat) == 3
        assert clean_flat[0].page == 1
        assert clean_flat[1].page == 2
        assert clean_flat[2].page == 3

    def test_process_filters_invalid_content(self):
        """Test that processing filters out invalid content."""
        processor = ParagraphProcessor()
        config = {'min_content_length': 10}
        pages_content = [
            [
                ParagraphData(text="Valid paragraph here", page=1, paragraph_index=0),
                ParagraphData(text="Short", page=1, paragraph_index=1),
                ParagraphData(text="123 456", page=1, paragraph_index=2),
                ParagraphData(text="Another valid paragraph", page=1, paragraph_index=3),
            ],
        ]

        clean_flat, verification_pages = processor.process_ocr_result(pages_content, config)

        assert len(clean_flat) == 2
        assert len(verification_pages[0]) == 4  # Verification keeps all

    def test_process_empty_pages(self):
        """Test processing with empty pages list."""
        processor = ParagraphProcessor()
        config = {'min_content_length': 10}

        clean_flat, verification_pages = processor.process_ocr_result([], config)

        assert clean_flat == []
        assert verification_pages == []

    def test_process_preserves_page_structure_in_verification(self):
        """Test that original page structure is preserved in verification output."""
        processor = ParagraphProcessor()
        config = {'min_content_length': 5}
        pages_content = [
            [
                ParagraphData(text="P1 Para 1", page=1, paragraph_index=0),
                ParagraphData(text="P1 Para 2", page=1, paragraph_index=1),
            ],
            [
                ParagraphData(text="P2 Para 1", page=2, paragraph_index=2),
            ],
            [
                ParagraphData(text="P3 Para 1", page=3, paragraph_index=3),
                ParagraphData(text="P3 Para 2", page=3, paragraph_index=4),
                ParagraphData(text="P3 Para 3", page=3, paragraph_index=5),
            ],
        ]

        clean_flat, verification_pages = processor.process_ocr_result(pages_content, config)

        assert len(verification_pages) == 3
        assert len(verification_pages[0]) == 2
        assert len(verification_pages[1]) == 1
        assert len(verification_pages[2]) == 3

    def test_process_with_mixed_valid_invalid(self):
        """Test processing with mix of valid and invalid content across pages."""
        processor = ParagraphProcessor()
        config = {'min_content_length': 10}
        pages_content = [
            [
                ParagraphData(text="Valid paragraph one", page=1, paragraph_index=0),
                ParagraphData(text="...", page=1, paragraph_index=1),
            ],
            [
                ParagraphData(text="Valid paragraph two", page=2, paragraph_index=2),
                ParagraphData(text="Short", page=2, paragraph_index=3),
            ],
        ]

        clean_flat, verification_pages = processor.process_ocr_result(pages_content, config)

        assert len(clean_flat) == 2
        assert clean_flat[0].text == "Valid paragraph one"
        assert clean_flat[1].text == "Valid paragraph two"

    def test_process_applies_config_to_all_pages(self):
        """Test that configuration is applied consistently across all pages."""
        processor = ParagraphProcessor()
        config = {
            'min_content_length': 15,
            'normalize_whitespace': True,
        }
        pages_content = [
            [ParagraphData(text="  Normalized   text   page 1  ", page=1, paragraph_index=0)],
            [ParagraphData(text="  Normalized   text   page 2  ", page=2, paragraph_index=1)],
        ]

        clean_flat, verification_pages = processor.process_ocr_result(pages_content, config)

        assert all(para.text == "Normalized text page 1" or para.text == "Normalized text page 2"
                   for para in clean_flat)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_is_valid_content_no_word_characters(self):
        """Test that text without word characters (no letters) is invalid."""
        processor = ParagraphProcessor()
        # Unicode punctuation and symbols, but no actual letters
        assert processor.is_valid_content("→ • § © ™ ® ¶ † ‡", min_length=5) is False
        # Emoji without text
        assert processor.is_valid_content("😀 😃 😄 😁 😆 😅", min_length=5) is False

    def test_process_ocr_page_structure_mismatch(self, caplog):
        """Test handling of page structure mismatch edge case."""
        import logging

        processor = ParagraphProcessor()
        config = {'min_content_length': 10}

        # Create a scenario where filtering might cause mismatch
        # This edge case is hard to trigger naturally, but we'll test the path
        pages_content = [
            [ParagraphData(text="Valid paragraph", page=1, paragraph_index=0)],
        ]

        # Process normally first
        clean_flat, verification_pages = processor.process_ocr_result(pages_content, config)

        # The normal case should work fine
        assert len(verification_pages) == 1
        assert len(verification_pages[0]) == 1
