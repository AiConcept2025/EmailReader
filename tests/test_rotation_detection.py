"""
Test script for rotation detection functionality.

This script tests the RotationDetector class independently.
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.preprocessing.rotation_detector import RotationDetector

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_rotation_detection(image_path: str):
    """
    Test rotation detection on a sample document.

    Args:
        image_path: Path to test PDF or image
    """
    logger.info("Testing rotation detection on: %s", image_path)

    # Configuration for rotation detection
    config = {
        'method': 'paddleocr',
        'fallback_methods': ['tesseract'],
        'confidence_threshold': 0.8,
        'paddleocr': {
            'lang': 'ru',
            'use_gpu': False
        }
    }

    # Initialize detector
    detector = RotationDetector(config)

    # Detect rotation
    try:
        angle, confidence = detector.detect_rotation(image_path)
        logger.info("=" * 60)
        logger.info("ROTATION DETECTION RESULT:")
        logger.info("  Detected angle: %d degrees", angle)
        logger.info("  Confidence: %.2f", confidence)
        logger.info("=" * 60)

        if angle != 0:
            # Test rotation correction
            output_path = image_path.replace('.pdf', '_corrected.pdf')
            logger.info("Correcting rotation and saving to: %s", output_path)
            corrected_path = detector.correct_rotation(image_path, output_path, angle)
            logger.info("Rotation correction completed: %s", corrected_path)
        else:
            logger.info("No rotation needed")

    except Exception as e:
        logger.error("Error during rotation detection: %s", e, exc_info=True)
        raise


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_rotation_detection.py <path_to_pdf_or_image>")
        print("\nExample:")
        print("  python test_rotation_detection.py document.pdf")
        sys.exit(1)

    test_file = sys.argv[1]

    if not Path(test_file).exists():
        print(f"Error: File not found: {test_file}")
        sys.exit(1)

    test_rotation_detection(test_file)
