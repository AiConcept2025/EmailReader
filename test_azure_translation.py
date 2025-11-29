#!/usr/bin/env python3
"""
Test Azure OCR + Google Document Translation Integration

Usage:
    python test_azure_translation.py --input /path/to/test.pdf --target en
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ocr.ocr_factory import OCRProviderFactory
from src.translation.translator_factory import TranslatorFactory


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the test script."""
    log_level = logging.DEBUG if verbose else logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Also log to file
    log_file = f"test_azure_translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.info("Logging configured (level: %s, log file: %s)",
                logging.getLevelName(log_level), log_file)


def load_config() -> dict:
    """
    Load configuration from environment variables.

    Returns:
        Configuration dictionary
    """
    logger = logging.getLogger(__name__)

    logger.info("Loading configuration from environment variables")

    # Azure OCR configuration
    azure_endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
    azure_api_key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_API_KEY')

    if not azure_endpoint or not azure_api_key:
        logger.error("Missing Azure configuration in environment variables")
        logger.error("Required: AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT, AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
        raise ValueError("Azure configuration not found in environment")

    # Google Translation configuration
    google_project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    google_location = os.getenv('GOOGLE_TRANSLATION_LOCATION', 'us-central1')

    if not google_project_id:
        logger.warning("GOOGLE_CLOUD_PROJECT not set, will use subprocess translator")
        translation_provider = 'google_text'
    else:
        translation_provider = 'google_doc'

    config = {
        'ocr': {
            'provider': 'azure',
            'azure': {
                'endpoint': azure_endpoint,
                'api_key': azure_api_key
            }
        },
        'translation': {
            'provider': translation_provider,
            'google_doc': {
                'project_id': google_project_id,
                'location': google_location
            },
            'google_text': {
                'executable_path': os.path.join(os.getcwd(), 'translate_document')
            }
        }
    }

    logger.info("Configuration loaded successfully")
    logger.debug("OCR provider: %s", config['ocr']['provider'])
    logger.debug("Translation provider: %s", config['translation']['provider'])

    return config


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description='Test Azure OCR + Google Translation integration'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Path to input PDF file'
    )
    parser.add_argument(
        '--target',
        default='en',
        help='Target language code (default: en)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose debug logging'
    )
    parser.add_argument(
        '--ocr-only',
        action='store_true',
        help='Only perform OCR, skip translation'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("Azure OCR + Google Translation Integration Test")
    logger.info("=" * 80)

    try:
        # Validate input file
        input_path = Path(args.input).resolve()
        if not input_path.exists():
            logger.error("Input file not found: %s", input_path)
            sys.exit(1)

        logger.info("Input file: %s", input_path)
        logger.info("Target language: %s", args.target)

        # Determine output paths
        input_dir = input_path.parent
        input_stem = input_path.stem

        # OCR output path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ocr_output_path = input_dir / f"{input_stem}_ocr_test_{timestamp}.docx"

        # Translation output path
        translated_output_path = input_dir / f"{input_stem}_translated_test_{timestamp}.docx"

        logger.info("OCR output: %s", ocr_output_path)
        if not args.ocr_only:
            logger.info("Translation output: %s", translated_output_path)

        # Load configuration
        logger.info("-" * 80)
        logger.info("STEP 1: Loading configuration")
        logger.info("-" * 80)
        config = load_config()

        # Perform OCR
        logger.info("-" * 80)
        logger.info("STEP 2: Performing OCR with Azure Document Intelligence")
        logger.info("-" * 80)

        ocr_provider = OCRProviderFactory.get_provider(config)
        logger.info("Created OCR provider: %s", ocr_provider.__class__.__name__)

        logger.info("Starting OCR processing...")
        ocr_provider.process_document(str(input_path), str(ocr_output_path))

        if not ocr_output_path.exists():
            logger.error("OCR failed - output file not created")
            sys.exit(1)

        ocr_size = ocr_output_path.stat().st_size / 1024
        logger.info("OCR completed successfully!")
        logger.info("OCR output size: %.2f KB", ocr_size)

        if args.ocr_only:
            logger.info("=" * 80)
            logger.info("OCR-only mode - skipping translation")
            logger.info("Output file: %s", ocr_output_path)
            logger.info("=" * 80)
            return

        # Perform Translation
        logger.info("-" * 80)
        logger.info("STEP 3: Performing translation with Google Translation API")
        logger.info("-" * 80)

        translator = TranslatorFactory.get_translator(config)
        logger.info("Created translator: %s", translator.__class__.__name__)

        logger.info("Starting translation...")
        translator.translate_document(
            str(ocr_output_path),
            str(translated_output_path),
            target_lang=args.target
        )

        if not translated_output_path.exists():
            logger.error("Translation failed - output file not created")
            sys.exit(1)

        translation_size = translated_output_path.stat().st_size / 1024
        logger.info("Translation completed successfully!")
        logger.info("Translation output size: %.2f KB", translation_size)

        # Summary
        logger.info("=" * 80)
        logger.info("TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info("Input file: %s", input_path)
        logger.info("OCR output: %s (%.2f KB)", ocr_output_path, ocr_size)
        logger.info("Translated output: %s (%.2f KB)", translated_output_path, translation_size)
        logger.info("=" * 80)

    except KeyboardInterrupt:
        logger.warning("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error("Test failed with error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
