"""
Example Usage of OCR Provider Architecture

This module demonstrates how to use the OCR provider factory to process
documents with different OCR engines.
"""

import logging
from pathlib import Path

from src.ocr import OCRProviderFactory, BaseOCRProvider

# Configure basic logging for examples
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)


def example_default_provider():
    """
    Example 1: Using the default Tesseract OCR provider.

    This is the simplest configuration and uses the existing Tesseract
    implementation that's already working in the EmailReader project.
    """
    print("\n" + "=" * 70)
    print("Example 1: Default Tesseract OCR Provider")
    print("=" * 70)

    # Minimal configuration - uses default provider
    config = {
        'ocr': {
            'provider': 'default'
        }
    }

    # Create provider
    provider = OCRProviderFactory.get_provider(config)
    print(f"Created provider: {type(provider).__name__}")

    # Example usage (uncomment when you have a real PDF file):
    # if provider.is_pdf_searchable('input.pdf'):
    #     print("PDF is searchable - no OCR needed")
    # else:
    #     print("PDF is image-based - running OCR...")
    #     provider.process_document('input.pdf', 'output.docx')


def example_landing_ai_provider():
    """
    Example 2: Using LandingAI OCR provider (implementation pending).

    This shows how to configure the LandingAI provider. Currently raises
    NotImplementedError - will be implemented in Phase 3.
    """
    print("\n" + "=" * 70)
    print("Example 2: LandingAI OCR Provider (Phase 3)")
    print("=" * 70)

    # Configuration with LandingAI API credentials
    config = {
        'ocr': {
            'provider': 'landing_ai',
            'landing_ai': {
                'api_key': 'land_sk_your_api_key_here',
                'base_url': 'https://api.va.landing.ai/v1',
                'model': 'dpt-2-latest',
                'timeout': 30,
                'max_retries': 3
            }
        }
    }

    # Create provider
    provider = OCRProviderFactory.get_provider(config)
    print(f"Created provider: {type(provider).__name__}")

    # Note: process_document() will raise NotImplementedError until Phase 3
    print("Note: LandingAI processing will be available in Phase 3")


def example_automatic_fallback():
    """
    Example 3: Automatic fallback to default provider.

    If LandingAI is configured but API key is missing, the factory
    automatically falls back to the default Tesseract provider.
    """
    print("\n" + "=" * 70)
    print("Example 3: Automatic Fallback to Default Provider")
    print("=" * 70)

    # LandingAI requested but no API key provided
    config = {
        'ocr': {
            'provider': 'landing_ai',
            'landing_ai': {
                # API key is missing!
                'base_url': 'https://api.va.landing.ai/v1'
            }
        }
    }

    # Factory detects missing API key and falls back
    provider = OCRProviderFactory.get_provider(config)
    print(f"Created provider: {type(provider).__name__}")
    print("Factory automatically fell back to DefaultOCRProvider")


def example_config_validation():
    """
    Example 4: Configuration validation.

    Use the validate_config() method to check configuration before
    creating providers.
    """
    print("\n" + "=" * 70)
    print("Example 4: Configuration Validation")
    print("=" * 70)

    # Valid configuration
    valid_config = {
        'ocr': {
            'provider': 'default'
        }
    }
    is_valid = OCRProviderFactory.validate_config(valid_config)
    print(f"Valid config check: {is_valid}")

    # Invalid provider type
    invalid_config = {
        'ocr': {
            'provider': 'some_invalid_provider'
        }
    }
    is_valid = OCRProviderFactory.validate_config(invalid_config)
    print(f"Invalid provider config check: {is_valid}")

    # Missing OCR section
    missing_config = {}
    is_valid = OCRProviderFactory.validate_config(missing_config)
    print(f"Missing OCR section check: {is_valid}")


def example_integration_with_existing_code():
    """
    Example 5: How to integrate with existing EmailReader code.

    This shows how to replace direct calls to pdf_image_ocr functions
    with the new provider pattern.
    """
    print("\n" + "=" * 70)
    print("Example 5: Integration Pattern")
    print("=" * 70)

    # Load config from your existing config system
    from src.config import load_config
    app_config = load_config()

    # Add OCR configuration if not present
    if 'ocr' not in app_config:
        app_config['ocr'] = {'provider': 'default'}

    # Create provider
    provider = OCRProviderFactory.get_provider(app_config)

    print(f"Provider type: {type(provider).__name__}")
    print("\nNow you can replace:")
    print("  OLD: from src.pdf_image_ocr import ocr_pdf_image_to_doc, is_pdf_searchable_pypdf")
    print("       ocr_pdf_image_to_doc(pdf_file, docx_file)")
    print("\n  NEW: from src.ocr import OCRProviderFactory")
    print("       provider = OCRProviderFactory.get_provider(config)")
    print("       provider.process_document(pdf_file, docx_file)")


def example_polymorphic_usage():
    """
    Example 6: Polymorphic usage with BaseOCRProvider.

    Shows how to write code that works with any OCR provider.
    """
    print("\n" + "=" * 70)
    print("Example 6: Polymorphic Usage")
    print("=" * 70)

    def process_with_any_provider(
        provider: BaseOCRProvider,
        input_file: str,
        output_file: str
    ):
        """
        This function works with ANY OCR provider that implements
        the BaseOCRProvider interface.
        """
        print(f"Using provider: {type(provider).__name__}")

        # Check if PDF is searchable (works for all providers)
        if input_file.lower().endswith('.pdf'):
            try:
                is_searchable = provider.is_pdf_searchable(input_file)
                if is_searchable:
                    print("PDF is searchable - OCR not required")
                    return
            except FileNotFoundError:
                print(f"File not found: {input_file}")
                return

        # Process document (works for all providers)
        print(f"Processing: {input_file} -> {output_file}")
        # provider.process_document(input_file, output_file)

    # Works with default provider
    default_provider = OCRProviderFactory.get_provider({'ocr': {'provider': 'default'}})
    print("\nWith default provider:")
    # process_with_any_provider(default_provider, 'test.pdf', 'output.docx')

    # Would also work with LandingAI provider (when implemented)
    print("\nSame function works with any provider that implements BaseOCRProvider!")


if __name__ == '__main__':
    """
    Run all examples to demonstrate the OCR provider architecture.
    """
    print("\n" + "=" * 70)
    print("OCR Provider Architecture Examples")
    print("=" * 70)

    # Run all examples
    example_default_provider()
    example_landing_ai_provider()
    example_automatic_fallback()
    example_config_validation()
    example_integration_with_existing_code()
    example_polymorphic_usage()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70 + "\n")
