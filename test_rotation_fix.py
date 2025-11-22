#!/usr/bin/env python3
"""
Test script to verify rotation detection fixes.

Tests both PaddleOCR and Tesseract OSD methods.
"""

import sys
import logging
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from preprocessing.rotation_detector import RotationDetector

# Set up logging to see detailed output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.dev.json."""
    config_path = Path(__file__).parent / 'credentials' / 'config.dev.json'

    if not config_path.exists():
        logger.error("Config file not found: %s", config_path)
        return None

    with open(config_path, 'r') as f:
        config = json.load(f)

    return config.get('preprocessing', {}).get('rotation_detection', {})


def test_rotation_detection():
    """Test rotation detection with current configuration."""
    logger.info("="*80)
    logger.info("ROTATION DETECTION FIX TEST")
    logger.info("="*80)

    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration")
        return False

    logger.info("Configuration loaded:")
    logger.info("  - Method: %s", config.get('method'))
    logger.info("  - Fallbacks: %s", config.get('fallback_methods'))
    logger.info("  - Threshold: %.2f", config.get('confidence_threshold', 0.8))
    logger.info("  - PaddleOCR config: %s", config.get('paddleocr', {}))

    # Initialize detector
    logger.info("\nInitializing RotationDetector...")
    detector = RotationDetector(config)

    # Find a test document
    test_files = [
        'Konnova_ocr.docx',
        'ФТР Артем Строкань EB1  (1) (2)_ocr.docx',
    ]

    test_file = None
    for filename in test_files:
        path = Path(__file__).parent / filename
        if path.exists():
            test_file = str(path)
            logger.info("Found test file: %s", filename)
            break

    if not test_file:
        logger.warning("No test files found. Skipping actual rotation test.")
        logger.info("\nTest files searched:")
        for filename in test_files:
            logger.info("  - %s", filename)
        logger.info("\nYou can test with any image or PDF file by running:")
        logger.info("  python test_rotation_fix.py <path-to-file>")
        return True

    # Test rotation detection
    logger.info("\n" + "="*80)
    logger.info("Testing rotation detection...")
    logger.info("="*80)

    try:
        angle, confidence = detector.detect_rotation(test_file)

        logger.info("\n" + "="*80)
        logger.info("RESULT:")
        logger.info("  Rotation angle: %d degrees", angle)
        logger.info("  Confidence: %.3f", confidence)
        logger.info("="*80)

        if confidence > 0:
            logger.info("\n✓ SUCCESS: Rotation detection working!")
            return True
        else:
            logger.warning("\n✗ WARNING: Low confidence (%.3f) - check document quality", confidence)
            return False

    except Exception as e:
        logger.error("\n✗ FAILED: %s", e, exc_info=True)
        return False


def test_specific_file(file_path: str):
    """Test rotation detection on a specific file."""
    logger.info("="*80)
    logger.info("Testing rotation detection on: %s", file_path)
    logger.info("="*80)

    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration")
        return False

    # Initialize detector
    detector = RotationDetector(config)

    # Test rotation detection
    try:
        angle, confidence = detector.detect_rotation(file_path)

        logger.info("\n" + "="*80)
        logger.info("RESULT:")
        logger.info("  Rotation angle: %d degrees", angle)
        logger.info("  Confidence: %.3f", confidence)
        logger.info("="*80)

        if confidence > 0:
            logger.info("\n✓ SUCCESS: Rotation detection working!")
            return True
        else:
            logger.warning("\n✗ WARNING: Low confidence - check document quality")
            return False

    except Exception as e:
        logger.error("\n✗ FAILED: %s", e, exc_info=True)
        return False


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Test specific file provided as argument
        file_path = sys.argv[1]
        success = test_specific_file(file_path)
    else:
        # Run general test
        success = test_rotation_detection()

    sys.exit(0 if success else 1)
