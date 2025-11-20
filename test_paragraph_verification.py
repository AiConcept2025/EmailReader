#!/usr/bin/env python3
"""
Test script for paragraph count verification implementation.

This script tests the new ParagraphData dataclass and verification logic
without requiring actual OCR or translation API calls.
"""

import logging
from typing import List

from src.models.paragraph_data import ParagraphData
from src.utils import verify_paragraph_counts

# Configure logging to see verification messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('TestParagraphVerification')


def test_paragraph_data_creation():
    """Test ParagraphData dataclass creation and properties."""
    logger.info("=" * 80)
    logger.info("TEST 1: ParagraphData Creation and Properties")
    logger.info("=" * 80)

    # Create a simple ParagraphData
    para1 = ParagraphData(
        text="This is a test paragraph.",
        page=1,
        paragraph_index=0
    )
    logger.info(f"Simple paragraph: {para1}")

    # Create a ParagraphData with all metadata
    para2 = ParagraphData(
        text="This paragraph has full metadata including bounding box and confidence.",
        page=2,
        bounding_box={'x': 100.5, 'y': 200.3, 'width': 500.0, 'height': 50.0},
        confidence=0.987,
        paragraph_index=1
    )
    logger.info(f"Full metadata paragraph: {para2}")
    logger.info(f"Bounding box: {para2.bounding_box}")
    logger.info(f"Confidence: {para2.confidence}")

    # Test list of ParagraphData
    paragraphs: List[ParagraphData] = [para1, para2]
    total_chars = sum(len(p.text) for p in paragraphs)
    logger.info(f"Created list of {len(paragraphs)} paragraphs with {total_chars} total characters")

    logger.info("TEST 1: PASSED ✓\n")
    return True


def test_paragraph_count_verification_success():
    """Test verify_paragraph_counts with matching counts."""
    logger.info("=" * 80)
    logger.info("TEST 2: Paragraph Count Verification (Success Case)")
    logger.info("=" * 80)

    # Simulate successful pipeline with 25 paragraphs
    ocr_count = 25
    docx_count = 25
    translated_count = 25

    logger.info(f"Simulating OCR extraction: {ocr_count} paragraphs")
    logger.info(f"Simulating DOCX creation: {docx_count} paragraphs")
    logger.info(f"Simulating translation: {translated_count} paragraphs")

    result = verify_paragraph_counts(ocr_count, docx_count, translated_count)

    if result:
        logger.info("TEST 2: PASSED ✓\n")
    else:
        logger.error("TEST 2: FAILED ✗\n")

    return result


def test_paragraph_count_verification_failure():
    """Test verify_paragraph_counts with mismatched counts."""
    logger.info("=" * 80)
    logger.info("TEST 3: Paragraph Count Verification (Failure Case)")
    logger.info("=" * 80)

    # Simulate pipeline with mismatch
    ocr_count = 25
    docx_count = 23  # Missing 2 paragraphs
    translated_count = 23

    logger.info(f"Simulating OCR extraction: {ocr_count} paragraphs")
    logger.info(f"Simulating DOCX creation: {docx_count} paragraphs (MISMATCH)")
    logger.info(f"Simulating translation: {translated_count} paragraphs")

    result = verify_paragraph_counts(ocr_count, docx_count, translated_count)

    # For this test, we expect failure (result should be False)
    if not result:
        logger.info("TEST 3: PASSED ✓ (correctly detected mismatch)\n")
        return True
    else:
        logger.error("TEST 3: FAILED ✗ (should have detected mismatch)\n")
        return False


def test_simulated_ocr_extraction():
    """Simulate OCR extraction with ParagraphData objects."""
    logger.info("=" * 80)
    logger.info("TEST 4: Simulated OCR Extraction")
    logger.info("=" * 80)

    # Simulate extracting 3 pages with different paragraph counts
    pages_content: List[List[ParagraphData]] = []
    global_index = 0

    for page_num in range(1, 4):
        page_paragraphs: List[ParagraphData] = []
        num_paras = 5 + page_num  # Page 1: 6 paras, Page 2: 7 paras, Page 3: 8 paras

        for i in range(num_paras):
            para = ParagraphData(
                text=f"Page {page_num}, Paragraph {i+1}: Sample text content.",
                page=page_num,
                bounding_box={
                    'x': 50.0,
                    'y': 100.0 + (i * 60),
                    'width': 500.0,
                    'height': 50.0
                },
                confidence=0.95 + (i * 0.01),
                paragraph_index=global_index
            )
            page_paragraphs.append(para)
            global_index += 1

        pages_content.append(page_paragraphs)
        logger.info(f"Page {page_num}: extracted {len(page_paragraphs)} paragraphs")

    total_paras = sum(len(page) for page in pages_content)
    logger.info(f"PARAGRAPH_COUNT_VERIFICATION: stage=OCR_EXTRACTION, count={total_paras}")
    logger.info(f"Total paragraphs extracted: {total_paras}")

    expected_total = 6 + 7 + 8  # 21 paragraphs
    if total_paras == expected_total:
        logger.info(f"TEST 4: PASSED ✓ (expected {expected_total}, got {total_paras})\n")
        return True
    else:
        logger.error(f"TEST 4: FAILED ✗ (expected {expected_total}, got {total_paras})\n")
        return False


def test_simulated_translation_verification():
    """Simulate translation with count verification."""
    logger.info("=" * 80)
    logger.info("TEST 5: Simulated Translation Verification")
    logger.info("=" * 80)

    # Simulate input paragraphs
    input_paragraphs = [
        "First paragraph in Russian.",
        "Second paragraph in Russian.",
        "Third paragraph in Russian.",
        "",  # Empty paragraph (should be preserved)
        "Fifth paragraph in Russian."
    ]

    input_count = len(input_paragraphs)
    logger.info(f"PARAGRAPH_COUNT_VERIFICATION: stage=TRANSLATION_INPUT, count={input_count}")
    logger.info(f"Starting translation: {input_count} paragraphs")

    # Simulate translation (just convert to uppercase as mock translation)
    translated_paragraphs = []
    for para in input_paragraphs:
        if para:
            translated = para.upper()
        else:
            translated = ""  # Preserve empty paragraphs
        translated_paragraphs.append(translated)

    output_count = len(translated_paragraphs)
    logger.info(f"PARAGRAPH_COUNT_VERIFICATION: stage=TRANSLATION_OUTPUT, count={output_count}")
    logger.info(f"Translation complete: {input_count} paragraphs received, {output_count} paragraphs translated")

    # Verify counts match
    if input_count == output_count:
        logger.info(f"TEST 5: PASSED ✓ (counts match: {input_count} == {output_count})\n")
        return True
    else:
        logger.error(f"TEST 5: FAILED ✗ (counts mismatch: {input_count} != {output_count})\n")
        return False


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("*" * 80)
    logger.info("PARAGRAPH COUNT VERIFICATION - COMPREHENSIVE TEST SUITE")
    logger.info("*" * 80)
    logger.info("\n")

    results = []

    # Run all tests
    results.append(("ParagraphData Creation", test_paragraph_data_creation()))
    results.append(("Verification Success Case", test_paragraph_count_verification_success()))
    results.append(("Verification Failure Case", test_paragraph_count_verification_failure()))
    results.append(("Simulated OCR Extraction", test_simulated_ocr_extraction()))
    results.append(("Simulated Translation", test_simulated_translation_verification()))

    # Summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    logger.info("-" * 80)
    logger.info(f"Total: {len(results)} tests")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info("=" * 80)

    if failed == 0:
        logger.info("ALL TESTS PASSED! ✓✓✓")
        return 0
    else:
        logger.error(f"{failed} TEST(S) FAILED!")
        return 1


if __name__ == '__main__':
    exit(main())
