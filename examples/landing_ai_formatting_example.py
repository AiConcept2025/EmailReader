#!/usr/bin/env python3
"""
Test script for LandingAI formatting preservation.

This script processes a PDF file using the LandingAI OCR provider
and demonstrates the enhanced formatting preservation features.

Usage:
    python test_landing_ai_formatting.py <pdf_file_path>

Example:
    python test_landing_ai_formatting.py test_docs/file-sample-pdf.pdf
"""

import sys
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger('LandingAI.Test')

def test_landing_ai_formatting(pdf_path: str):
    """Test LandingAI OCR with formatting preservation."""

    if not os.path.exists(pdf_path):
        logger.error(f"File not found: {pdf_path}")
        return False

    logger.info("=" * 80)
    logger.info("LandingAI Formatting Preservation Test")
    logger.info("=" * 80)
    logger.info(f"Input file: {pdf_path}")

    # Import after setting up logging
    from src.ocr import OCRProviderFactory
    from src.config import load_config

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()

        # Check if LandingAI is configured
        ocr_config = config.get('ocr', {})
        provider = ocr_config.get('provider', 'default')
        landing_ai_config = ocr_config.get('landing_ai', {})
        api_key = landing_ai_config.get('api_key')

        logger.info(f"Configured OCR provider: {provider}")

        if provider != 'landing_ai':
            logger.warning(f"OCR provider is '{provider}', not 'landing_ai'")
            logger.warning("To use LandingAI, update credentials/config.dev.json:")
            logger.warning('  "ocr": { "provider": "landing_ai", ... }')

        if not api_key:
            logger.error("LandingAI API key not found in configuration!")
            logger.error("Please add API key to credentials/config.dev.json")
            return False

        logger.info(f"LandingAI API key found: {api_key[:10]}...")

        # Create output path
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = f"test_output_{base_name}_landing_ai.docx"

        logger.info(f"Output file: {output_path}")
        logger.info("")
        logger.info("Starting OCR processing with LandingAI...")
        logger.info("=" * 80)

        # Get OCR provider
        ocr_provider = OCRProviderFactory.get_provider(config)
        provider_class = ocr_provider.__class__.__name__

        logger.info(f"Using provider: {provider_class}")
        logger.info("")

        # Process document
        ocr_provider.process_document(pdf_path, output_path)

        logger.info("")
        logger.info("=" * 80)
        logger.info("OCR processing completed successfully!")
        logger.info(f"Output saved to: {output_path}")

        # Check if file was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / 1024  # KB
            logger.info(f"Output file size: {file_size:.2f} KB")
            logger.info("")
            logger.info("✅ SUCCESS: Document processed with formatting preservation")
            logger.info("")
            logger.info("Check the log output above for:")
            logger.info("  - JSON structure logging (DEBUG level)")
            logger.info("  - Grounding data availability")
            logger.info("  - Structured vs basic conversion path")
            logger.info("  - Page/column/paragraph counts")
            return True
        else:
            logger.error(f"Output file was not created: {output_path}")
            return False

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_landing_ai_formatting.py <pdf_file_path>")
        print("")
        print("Example:")
        print("  python test_landing_ai_formatting.py test_docs/file-sample-pdf.pdf")
        print("  python test_landing_ai_formatting.py test_docs/PDF-scanned-rus-words.pdf")
        print("")
        print("Note: Make sure LandingAI is configured in credentials/config.dev.json")
        sys.exit(1)

    pdf_file = sys.argv[1]
    success = test_landing_ai_formatting(pdf_file)

    sys.exit(0 if success else 1)
