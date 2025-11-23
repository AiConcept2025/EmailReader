#!/usr/bin/env python3
"""
Test script to verify the self-contained translation configuration.

This script tests:
1. Loading configuration from config.dev.json
2. Creating translator with embedded service account credentials
3. Verifying credentials are loaded correctly
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_config
from src.translation import get_translator

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Test the translation configuration."""
    logger.info("=" * 80)
    logger.info("TESTING SELF-CONTAINED TRANSLATION CONFIGURATION")
    logger.info("=" * 80)

    try:
        # Load config
        logger.info("Step 1: Loading configuration from config.dev.json")
        config = load_config()
        if not config:
            logger.error("Failed to load configuration")
            return False

        logger.info("Configuration loaded successfully")

        # Check translation config
        translation_config = config.get('translation', {})
        provider = translation_config.get('provider')
        logger.info("  - Translation provider: %s", provider)

        google_doc_config = translation_config.get('google_doc', {})
        logger.info("  - Project ID: %s", google_doc_config.get('project_id'))
        logger.info("  - Location: %s", google_doc_config.get('location'))
        logger.info("  - Endpoint: %s", google_doc_config.get('endpoint'))

        # Check service account
        service_account = config.get('google_drive', {}).get('service_account')
        if service_account:
            logger.info("  - Service account email: %s",
                       service_account.get('client_email'))
            logger.info("  - Service account project: %s",
                       service_account.get('project_id'))
        else:
            logger.error("  - No service account found in config!")
            return False

        # Create translator
        logger.info("\nStep 2: Creating translator instance")
        translator = get_translator(config)
        logger.info("Translator created successfully: %s", type(translator).__name__)

        # Verify translator configuration
        logger.info("\nStep 3: Verifying translator configuration")
        logger.info("  - Translator project ID: %s", translator.project_id)
        logger.info("  - Translator location: %s", translator.location)
        logger.info("  - Translator endpoint: %s", translator.endpoint)
        logger.info("  - Translator parent path: %s", translator.parent)

        if hasattr(translator, 'service_account_info') and translator.service_account_info:
            logger.info("  - Service account loaded: YES")
            logger.info("  - Service account email: %s",
                       translator.service_account_info.get('client_email'))
        else:
            logger.error("  - Service account loaded: NO")
            return False

        logger.info("\n" + "=" * 80)
        logger.info("CONFIGURATION TEST SUCCESSFUL")
        logger.info("=" * 80)
        logger.info("\nThe EmailReader project is now self-contained for Google Cloud Translation.")
        logger.info("It uses credentials from config.dev.json without relying on environment variables.")
        logger.info("\nConfiguration summary:")
        logger.info("  - Project: synologysafeaccess-320003")
        logger.info("  - Service Account: irissolutions-850@synologysafeaccess-320003.iam.gserviceaccount.com")
        logger.info("  - Location: global")
        logger.info("  - Endpoint: translate.googleapis.com")

        return True

    except Exception as e:
        logger.error("=" * 80)
        logger.error("CONFIGURATION TEST FAILED")
        logger.error("=" * 80)
        logger.error("Error: %s", e, exc_info=True)
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
