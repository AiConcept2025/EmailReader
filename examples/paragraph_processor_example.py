"""
Example usage of ParagraphProcessor for filtering OCR output.

This demonstrates how to use the ParagraphProcessor to clean and filter
OCR results before translation.
"""

from src.processors.paragraph_processor import ParagraphProcessor
from src.models.paragraph_data import ParagraphData


def main():
    """Demonstrate ParagraphProcessor functionality."""

    # Initialize processor
    processor = ParagraphProcessor()

    # Configuration
    config = {
        'min_content_length': 10,
        'max_consecutive_empty': 1,
        'normalize_whitespace': True
    }

    # Simulate OCR output with multiple pages
    pages_content = [
        # Page 1
        [
            ParagraphData(
                text="   Chapter   1:   Introduction   ",
                page=1,
                paragraph_index=0,
                confidence=0.98
            ),
            ParagraphData(
                text="This is the first paragraph with\n\n\nmultiple newlines.",
                page=1,
                paragraph_index=1,
                confidence=0.95
            ),
            ParagraphData(
                text="",  # Empty paragraph (semantic break)
                page=1,
                paragraph_index=2,
                confidence=1.0
            ),
            ParagraphData(
                text="...",  # Invalid: only punctuation
                page=1,
                paragraph_index=3,
                confidence=0.50
            ),
        ],
        # Page 2
        [
            ParagraphData(
                text="123 456 789",  # Invalid: only numbers
                page=2,
                paragraph_index=4,
                confidence=0.60
            ),
            ParagraphData(
                text="This is a valid paragraph on page 2.",
                page=2,
                paragraph_index=5,
                confidence=0.97
            ),
            ParagraphData(
                text="",  # Empty
                page=2,
                paragraph_index=6,
                confidence=1.0
            ),
            ParagraphData(
                text="",  # Another empty (should be filtered)
                page=2,
                paragraph_index=7,
                confidence=1.0
            ),
            ParagraphData(
                text="Final paragraph with   extra    spaces.",
                page=2,
                paragraph_index=8,
                confidence=0.96
            ),
        ]
    ]

    print("=" * 70)
    print("PARAGRAPH PROCESSOR EXAMPLE")
    print("=" * 70)

    # Process OCR result
    clean_paragraphs, verification_pages = processor.process_ocr_result(
        pages_content,
        config
    )

    # Display results
    print("\nORIGINAL STRUCTURE:")
    print(f"Total pages: {len(pages_content)}")
    total_original = sum(len(page) for page in pages_content)
    print(f"Total paragraphs: {total_original}")

    print("\nCLEAN PARAGRAPHS (for translation):")
    print(f"Count: {len(clean_paragraphs)}")
    print("-" * 70)
    for i, para in enumerate(clean_paragraphs, 1):
        print(f"\n{i}. Page {para.page}, Index {para.paragraph_index}")
        print(f"   Confidence: {para.confidence}")
        print(f"   Text: '{para.text}'")

    print("\n" + "=" * 70)
    print("VERIFICATION PAGES (original structure with normalized whitespace):")
    print(f"Total pages: {len(verification_pages)}")
    for page_num, page_paragraphs in enumerate(verification_pages, 1):
        print(f"\nPage {page_num}: {len(page_paragraphs)} paragraphs")
        for para in page_paragraphs:
            status = "KEPT" if para in clean_paragraphs else "FILTERED"
            print(f"  [{status}] Index {para.paragraph_index}: '{para.text[:50]}'")

    print("\n" + "=" * 70)
    print("STATISTICS:")
    print(f"Original paragraphs: {total_original}")
    print(f"Clean paragraphs: {len(clean_paragraphs)}")
    print(f"Filtered out: {total_original - len(clean_paragraphs)}")
    print(f"Filter rate: {((total_original - len(clean_paragraphs)) / total_original * 100):.1f}%")
    print("=" * 70)

    # Demonstrate individual methods
    print("\nDEMONSTRATING INDIVIDUAL METHODS:")
    print("-" * 70)

    # Normalize whitespace
    test_text = "  Multiple    spaces\n\n\nand   newlines  "
    normalized = processor.normalize_whitespace(test_text)
    print(f"\nOriginal: '{test_text}'")
    print(f"Normalized: '{normalized}'")

    # Validate content
    valid_tests = [
        ("Valid paragraph here", 10, True),
        ("Short", 10, False),
        ("123 ...", 5, False),
        ("Привет мир", 10, True),
    ]

    print("\nCONTENT VALIDATION:")
    for text, min_len, expected in valid_tests:
        result = processor.is_valid_content(text, min_len)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' (min_length={min_len}): {result}")


if __name__ == "__main__":
    main()
