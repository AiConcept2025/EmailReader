#!/usr/bin/env python3
"""
Test Google Cloud Translation API Permissions

This script verifies that the service account has the necessary permissions
to use the Google Cloud Translation API.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import load_config
from src.translation import get_translator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_translation_permissions():
    """Test if the service account has correct permissions for Translation API."""

    logger.info("=" * 80)
    logger.info("TESTING GOOGLE CLOUD TRANSLATION API PERMISSIONS")
    logger.info("=" * 80)

    # Step 1: Load configuration
    logger.info("\nStep 1: Loading configuration")
    config = load_config()

    translation_config = config.get('translation', {})
    google_doc_config = translation_config.get('google_doc', {})

    project_id = google_doc_config.get('project_id')
    location = google_doc_config.get('location')

    logger.info(f"  - Project ID: {project_id}")
    logger.info(f"  - Location: {location}")

    # Step 2: Create translator
    logger.info("\nStep 2: Creating translator instance")
    translator = get_translator(config)
    logger.info(f"  - Translator type: {type(translator).__name__}")

    # Step 3: Test with a simple text translation
    logger.info("\nStep 3: Testing Translation API with sample text")
    logger.info("  - Creating a simple test document (DOCX)")

    # Create a minimal test DOCX file
    test_file = project_root / "test_translation_sample.docx"
    output_file = project_root / "test_translation_output.docx"

    # Create a simple DOCX file using python-docx
    try:
        from docx import Document

        # Create test document
        doc = Document()
        doc.add_paragraph("Привет мир")  # "Hello world" in Russian
        doc.save(str(test_file))
        logger.info(f"  - Created test file: {test_file}")

        # Attempt translation
        logger.info("\nStep 4: Attempting translation...")
        logger.info("  - Input: Привет мир (Russian)")
        logger.info("  - Target language: English")
        logger.info(f"  - API endpoint: https://translate.googleapis.com/v3/projects/{project_id}/locations/{location}:translateDocument")

        translator.translate_document(
            input_path=str(test_file),
            output_path=str(output_file),
            target_lang='en'
        )

        logger.info("\n" + "=" * 80)
        logger.info("✅ TRANSLATION SUCCESSFUL - PERMISSIONS ARE CORRECT")
        logger.info("=" * 80)
        logger.info("\nThe service account has all required permissions:")
        logger.info("  ✓ Cloud Translation API is enabled")
        logger.info("  ✓ Service account has 'cloudtranslate.generalModels.docPredict' permission")
        logger.info("  ✓ Translation API calls are working correctly")

        # Clean up test files
        if test_file.exists():
            test_file.unlink()
            logger.info(f"\n  - Cleaned up test file: {test_file}")
        if output_file.exists():
            output_file.unlink()
            logger.info(f"  - Cleaned up output file: {output_file}")

        return True

    except ImportError as e:
        logger.error("\n" + "=" * 80)
        logger.error("❌ MISSING DEPENDENCY: python-docx")
        logger.error("=" * 80)
        logger.error(f"Error: {e}")
        logger.error("\nPlease install python-docx:")
        logger.error("  pip install python-docx")
        return False

    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error("❌ TRANSLATION FAILED - PERMISSION ERROR")
        logger.error("=" * 80)
        logger.error(f"Error: {e}")

        if "permission" in str(e).lower() or "403" in str(e):
            logger.error("\nPERMISSION ISSUES DETECTED:")
            logger.error(f"  - Service account: irissolutions-850@{project_id}.iam.gserviceaccount.com")
            logger.error(f"  - Project: {project_id}")
            logger.error("\nRequired IAM permissions:")
            logger.error("  1. Enable Cloud Translation API in the project")
            logger.error("  2. Grant the service account one of these roles:")
            logger.error("     - Cloud Translation API User (roles/cloudtranslate.user)")
            logger.error("     - Cloud Translation API Editor (roles/cloudtranslate.editor)")
            logger.error("\nHow to fix:")
            logger.error(f"  1. Go to: https://console.cloud.google.com/iam-admin/iam?project={project_id}")
            logger.error("  2. Find service account: irissolutions-850@{project_id}.iam.gserviceaccount.com")
            logger.error("  3. Click 'Edit' and add role: 'Cloud Translation API User'")
            logger.error("  4. Save changes")

        # Clean up test files on error
        if test_file.exists():
            test_file.unlink()
        if output_file.exists():
            output_file.unlink()

        return False


if __name__ == '__main__':
    success = test_translation_permissions()
    sys.exit(0 if success else 1)
