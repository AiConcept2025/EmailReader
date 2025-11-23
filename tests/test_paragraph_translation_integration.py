#!/usr/bin/env python3
"""
Test script for the new translate_paragraphs method.

This script demonstrates how to use the batch paragraph translation
feature without breaking existing document translation functionality.
"""

import os
import sys
import logging
from typing import List

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.translation.google_doc_translator import GoogleDocTranslator
from src.utils import load_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_paragraph_translation():
    """Test basic paragraph translation functionality."""
    logger.info("=" * 80)
    logger.info("TEST 1: Basic Paragraph Translation")
    logger.info("=" * 80)

    # Load configuration
    config = load_config()

    # Get Google Doc translation config
    translation_config = config.get('translation', {}).get('google_doc', {})

    # Add service account credentials
    service_account = config.get('google_drive', {}).get('service_account')
    if service_account:
        translation_config['service_account'] = service_account

    # Initialize translator
    translator = GoogleDocTranslator(translation_config)

    # Test paragraphs (Russian to English)
    russian_paragraphs = [
        "Привет, как дела?",
        "Это тестовый документ для проверки перевода.",
        "Мы тестируем пакетный перевод абзацев.",
        "",  # Empty paragraph - should be preserved
        "Последний абзац в списке."
    ]

    logger.info("Translating %d paragraphs from Russian to English", len(russian_paragraphs))

    try:
        translated = translator.translate_paragraphs(
            paragraphs=russian_paragraphs,
            target_lang='en',
            batch_size=3  # Small batch for testing
        )

        logger.info("\nTranslation Results:")
        logger.info("-" * 80)
        for i, (original, translated_text) in enumerate(zip(russian_paragraphs, translated)):
            logger.info("Paragraph %d:", i + 1)
            logger.info("  Original:   %s", original or "(empty)")
            logger.info("  Translated: %s", translated_text or "(empty)")
            logger.info("")

        # Verify length preservation
        assert len(translated) == len(russian_paragraphs), \
            f"Length mismatch: {len(translated)} != {len(russian_paragraphs)}"

        # Verify empty paragraph preservation
        assert translated[3] == "", "Empty paragraph not preserved"

        logger.info("✓ Test 1 PASSED: Basic translation works correctly")
        return True

    except Exception as e:
        logger.error("✗ Test 1 FAILED: %s", str(e), exc_info=True)
        return False


def test_large_batch_translation():
    """Test translation with larger batches."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Large Batch Translation")
    logger.info("=" * 80)

    # Load configuration
    config = load_config()
    translation_config = config.get('translation', {}).get('google_doc', {})
    service_account = config.get('google_drive', {}).get('service_account')
    if service_account:
        translation_config['service_account'] = service_account

    translator = GoogleDocTranslator(translation_config)

    # Create a large list of paragraphs
    paragraphs = [
        f"This is paragraph number {i}. It contains some test text."
        for i in range(1, 51)  # 50 paragraphs
    ]

    logger.info("Translating %d paragraphs from English to Spanish", len(paragraphs))

    try:
        translated = translator.translate_paragraphs(
            paragraphs=paragraphs,
            target_lang='es',
            batch_size=15  # Default batch size
        )

        # Verify results
        assert len(translated) == len(paragraphs), "Length mismatch"
        assert all(t for t in translated), "Some translations are empty"

        logger.info("Sample results (first 3 paragraphs):")
        for i in range(3):
            logger.info("  %d. %s -> %s", i + 1, paragraphs[i], translated[i])

        logger.info("✓ Test 2 PASSED: Large batch translation works correctly")
        return True

    except Exception as e:
        logger.error("✗ Test 2 FAILED: %s", str(e), exc_info=True)
        return False


def test_backward_compatibility():
    """Verify that existing translate_document still works."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Backward Compatibility")
    logger.info("=" * 80)

    # Load configuration
    config = load_config()
    translation_config = config.get('translation', {}).get('google_doc', {})
    service_account = config.get('google_drive', {}).get('service_account')
    if service_account:
        translation_config['service_account'] = service_account

    translator = GoogleDocTranslator(translation_config)

    # Check that translate_document method still exists
    assert hasattr(translator, 'translate_document'), \
        "translate_document method missing"

    # Check method signature
    import inspect
    sig = inspect.signature(translator.translate_document)
    params = list(sig.parameters.keys())

    assert 'input_path' in params, "input_path parameter missing"
    assert 'output_path' in params, "output_path parameter missing"
    assert 'target_lang' in params, "target_lang parameter missing"

    logger.info("✓ Test 3 PASSED: Backward compatibility maintained")
    return True


def test_empty_input():
    """Test handling of empty input."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Empty Input Handling")
    logger.info("=" * 80)

    config = load_config()
    translation_config = config.get('translation', {}).get('google_doc', {})
    service_account = config.get('google_drive', {}).get('service_account')
    if service_account:
        translation_config['service_account'] = service_account

    translator = GoogleDocTranslator(translation_config)

    # Test empty list
    result = translator.translate_paragraphs([], 'en')
    assert result == [], "Empty list should return empty list"

    # Test all empty strings
    result = translator.translate_paragraphs(['', '', ''], 'en')
    assert result == ['', '', ''], "All empty strings should be preserved"

    logger.info("✓ Test 4 PASSED: Empty input handled correctly")
    return True


def main():
    """Run all tests."""
    logger.info("\n" + "#" * 80)
    logger.info("# PARAGRAPH TRANSLATION METHOD TEST SUITE")
    logger.info("#" * 80 + "\n")

    results = []

    # Run tests
    results.append(("Empty Input Handling", test_empty_input()))
    results.append(("Backward Compatibility", test_backward_compatibility()))

    # These tests require valid API credentials
    # Uncomment to run actual API tests
    # results.append(("Basic Paragraph Translation", test_basic_paragraph_translation()))
    # results.append(("Large Batch Translation", test_large_batch_translation()))

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    total = len(results)
    passed = sum(1 for _, result in results if result)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info("%s: %s", test_name, status)

    logger.info("-" * 80)
    logger.info("Total: %d/%d tests passed", passed, total)
    logger.info("=" * 80)

    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
