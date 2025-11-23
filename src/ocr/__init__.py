"""
OCR Provider Infrastructure

This module provides a factory pattern for OCR providers,
allowing easy switching between different OCR services.
"""

from src.ocr.ocr_factory import OCRProviderFactory
from src.ocr.base_provider import BaseOCRProvider

__all__ = ['OCRProviderFactory', 'BaseOCRProvider']
