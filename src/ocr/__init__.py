"""
OCR Provider Package

This package provides a pluggable architecture for OCR (Optical Character Recognition)
processing with support for multiple OCR engines.

Available Providers:
    - DefaultOCRProvider: Uses Tesseract OCR (default)
    - LandingAIOCRProvider: Uses LandingAI Vision API (implementation pending)

Usage:
    from src.ocr import OCRProviderFactory

    config = {
        'ocr': {
            'provider': 'default',  # or 'landing_ai'
            'landing_ai': {
                'api_key': 'your-api-key',
                'base_url': 'https://api.va.landing.ai/v1',
                'model': 'dpt-2-latest'
            }
        }
    }

    provider = OCRProviderFactory.get_provider(config)
    provider.process_document('input.pdf', 'output.docx')
"""

from .ocr_factory import OCRProviderFactory
from .base_provider import BaseOCRProvider

__all__ = ['OCRProviderFactory', 'BaseOCRProvider']
