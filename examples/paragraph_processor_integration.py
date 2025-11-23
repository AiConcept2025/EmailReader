"""
Integration example showing how to use ParagraphProcessor in the OCR pipeline.

This demonstrates the typical workflow:
1. OCR extracts paragraphs from document
2. ParagraphProcessor filters and cleans the output
3. Clean paragraphs go to translation
4. Verification document includes all paragraphs
"""

from typing import List
from src.processors.paragraph_processor import ParagraphProcessor
from src.models.paragraph_data import ParagraphData


def simulate_ocr_extraction(file_path: str) -> List[List[ParagraphData]]:
    """
    Simulate OCR extraction from a document.

    In reality, this would call Azure Document Intelligence or similar service.
    """
    # This is mock data - replace with actual OCR service
    return [
        # Page 1
        [
            ParagraphData(text="Document Title", page=1, paragraph_index=0, confidence=0.99),
            ParagraphData(text="Subtitle here", page=1, paragraph_index=1, confidence=0.98),
            ParagraphData(text="", page=1, paragraph_index=2, confidence=1.0),
            ParagraphData(text="Introduction paragraph...", page=1, paragraph_index=3, confidence=0.95),
        ],
        # Page 2
        [
            ParagraphData(text="Chapter 1", page=2, paragraph_index=4, confidence=0.97),
            ParagraphData(text="Main content...", page=2, paragraph_index=5, confidence=0.96),
        ]
    ]


def send_to_translation(paragraphs: List[ParagraphData]) -> List[ParagraphData]:
    """
    Send clean paragraphs to translation service.

    In reality, this would call Google Cloud Translation or similar.
    """
    print(f"Sending {len(paragraphs)} paragraphs to translation service...")

    # Mock translation - replace with actual translation service
    translated = []
    for para in paragraphs:
        # Simulate translation
        translated_text = f"[TRANSLATED] {para.text}"
        translated.append(
            ParagraphData(
                text=translated_text,
                page=para.page,
                paragraph_index=para.paragraph_index,
                confidence=para.confidence,
                bounding_box=para.bounding_box
            )
        )

    return translated


def create_verification_document(pages: List[List[ParagraphData]], output_path: str):
    """
    Create verification document with all paragraphs (for OCR quality check).

    This helps verify OCR accuracy before translation.
    """
    print(f"Creating verification document at: {output_path}")

    # In reality, this would use python-docx to create actual Word document
    print("\nVERIFICATION DOCUMENT CONTENT:")
    print("=" * 70)
    for page_num, page_paragraphs in enumerate(pages, 1):
        print(f"\n--- Page {page_num} ---")
        for para in page_paragraphs:
            if para.text:
                print(f"{para.text}")
            else:
                print("[Empty paragraph - semantic break]")
    print("=" * 70)


def create_translated_document(paragraphs: List[ParagraphData], output_path: str):
    """
    Create final translated document with clean content.
    """
    print(f"\nCreating translated document at: {output_path}")

    # In reality, this would use python-docx to create actual Word document
    print("\nTRANSLATED DOCUMENT CONTENT:")
    print("=" * 70)
    for para in paragraphs:
        if para.text:
            print(f"{para.text}")
        else:
            print()  # Empty line for paragraph break
    print("=" * 70)


def main():
    """
    Main integration workflow demonstrating the complete pipeline.
    """

    print("PARAGRAPH PROCESSOR INTEGRATION EXAMPLE")
    print("=" * 70)

    # Step 1: OCR extraction
    print("\n1. OCR EXTRACTION")
    print("-" * 70)
    input_file = "sample_document.pdf"
    print(f"Extracting text from: {input_file}")

    ocr_result = simulate_ocr_extraction(input_file)
    total_paragraphs = sum(len(page) for page in ocr_result)
    print(f"Extracted {total_paragraphs} paragraphs from {len(ocr_result)} pages")

    # Step 2: Configure processor
    print("\n2. CONFIGURE PARAGRAPH PROCESSOR")
    print("-" * 70)

    config = {
        'min_content_length': 10,        # Skip very short paragraphs
        'max_consecutive_empty': 1,      # Keep max 1 empty for semantic breaks
        'normalize_whitespace': True     # Clean up whitespace
    }

    print(f"Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    # Step 3: Process OCR result
    print("\n3. PROCESS OCR RESULT")
    print("-" * 70)

    processor = ParagraphProcessor()
    clean_paragraphs, verification_pages = processor.process_ocr_result(
        ocr_result,
        config
    )

    print(f"Original paragraphs: {total_paragraphs}")
    print(f"Clean paragraphs: {len(clean_paragraphs)}")
    print(f"Filtered: {total_paragraphs - len(clean_paragraphs)}")

    # Step 4: Create verification document (optional but recommended)
    print("\n4. CREATE VERIFICATION DOCUMENT")
    print("-" * 70)

    verification_output = "sample_document_ocr_verification.docx"
    create_verification_document(verification_pages, verification_output)

    # Step 5: Translate clean content
    print("\n5. TRANSLATION")
    print("-" * 70)

    translated_paragraphs = send_to_translation(clean_paragraphs)
    print(f"Translated {len(translated_paragraphs)} paragraphs")

    # Step 6: Create final translated document
    print("\n6. CREATE TRANSLATED DOCUMENT")
    print("-" * 70)

    translated_output = "sample_document_translated.docx"
    create_translated_document(translated_paragraphs, translated_output)

    # Summary
    print("\n" + "=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)
    print(f"Input: {input_file}")
    print(f"OCR Verification: {verification_output}")
    print(f"Final Translation: {translated_output}")
    print(f"Processing efficiency: {(len(clean_paragraphs)/total_paragraphs*100):.1f}% content kept")
    print("=" * 70)

    # Benefits of this approach
    print("\nBENEFITS OF PARAGRAPH PROCESSING:")
    print("  ✓ Removes OCR noise and artifacts")
    print("  ✓ Reduces translation costs (fewer paragraphs to translate)")
    print("  ✓ Improves translation quality (cleaner input)")
    print("  ✓ Maintains document structure and readability")
    print("  ✓ Provides verification document for OCR quality check")
    print("  ✓ Preserves paragraph indices for tracking")


if __name__ == "__main__":
    main()
