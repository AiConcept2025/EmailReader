"""
Unit tests for AzureOCRProvider paragraph extraction flag.

Tests the use_paragraph_extraction attribute and its integration
with the process_document method.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ocr.azure_provider import AzureOCRProvider


class TestAzureProviderParagraphFlag:
    """Test Azure provider use_paragraph_extraction attribute."""

    def test_azure_provider_has_paragraph_flag_default_false(self):
        """Test Azure provider initializes with use_paragraph_extraction=False."""
        config = {
            'endpoint': 'https://test.cognitiveservices.azure.com/',
            'api_key': 'test_key'
        }

        with patch('src.ocr.azure_provider.DocumentAnalysisClient'):
            provider = AzureOCRProvider(config)
            assert hasattr(provider, 'use_paragraph_extraction')
            assert provider.use_paragraph_extraction is False

    def test_azure_provider_paragraph_flag_can_be_set(self):
        """Test use_paragraph_extraction flag can be set after initialization."""
        config = {
            'endpoint': 'https://test.cognitiveservices.azure.com/',
            'api_key': 'test_key'
        }

        with patch('src.ocr.azure_provider.DocumentAnalysisClient'):
            provider = AzureOCRProvider(config)
            provider.use_paragraph_extraction = True
            assert provider.use_paragraph_extraction is True

    @patch('src.ocr.azure_provider.os.path.getsize')
    @patch('src.ocr.azure_provider.AzureOCRProvider._extract_paragraphs_with_formatting')
    @patch('src.ocr.azure_provider.AzureOCRProvider._save_paragraphs_to_docx')
    @patch('src.ocr.azure_provider.AzureOCRProvider._detect_page_searchability')
    @patch('src.ocr.azure_provider.pdfplumber.open')
    @patch('src.ocr.azure_provider.os.path.exists')
    def test_process_document_uses_paragraph_extraction_when_flag_true(
        self, mock_exists, mock_pdfplumber, mock_detect, mock_save_para, mock_extract_para, mock_getsize
    ):
        """Test process_document uses paragraph extraction when flag is True."""
        # Setup
        config = {
            'endpoint': 'https://test.cognitiveservices.azure.com/',
            'api_key': 'test_key'
        }

        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        mock_detect.return_value = [False]  # Non-searchable page to trigger OCR

        # Mock PDF context
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        # Mock paragraph extraction
        mock_paragraph = Mock()
        mock_paragraph.content = "Test content"
        mock_extract_para.return_value = [mock_paragraph]

        with patch('src.ocr.azure_provider.DocumentAnalysisClient'):
            with patch('builtins.open', create=True) as mock_file:
                mock_file.return_value.__enter__.return_value.read.return_value = b'PDF bytes'

                provider = AzureOCRProvider(config)
                provider.use_paragraph_extraction = True

                # Execute
                provider.process_document('input.pdf', 'output.docx')

                # Verify paragraph extraction was called
                mock_extract_para.assert_called_once_with(b'PDF bytes')
                mock_save_para.assert_called_once()

    @patch('src.ocr.azure_provider.os.path.getsize')
    @patch('src.ocr.azure_provider.AzureOCRProvider._ocr_with_azure')
    @patch('src.ocr.azure_provider.AzureOCRProvider._save_as_docx')
    @patch('src.ocr.azure_provider.AzureOCRProvider._detect_page_searchability')
    @patch('src.ocr.azure_provider.pdfplumber.open')
    @patch('src.ocr.azure_provider.os.path.exists')
    def test_process_document_uses_line_extraction_when_flag_false(
        self, mock_exists, mock_pdfplumber, mock_detect, mock_save_docx, mock_ocr_azure, mock_getsize
    ):
        """Test process_document uses line-based extraction when flag is False."""
        # Setup
        config = {
            'endpoint': 'https://test.cognitiveservices.azure.com/',
            'api_key': 'test_key'
        }

        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        mock_detect.return_value = [False]  # Non-searchable page to trigger OCR

        # Mock PDF context
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        # Mock line extraction
        mock_ocr_azure.return_value = ["Line 1", "Line 2"]

        with patch('src.ocr.azure_provider.DocumentAnalysisClient'):
            with patch('builtins.open', create=True) as mock_file:
                mock_file.return_value.__enter__.return_value.read.return_value = b'PDF bytes'

                provider = AzureOCRProvider(config)
                # Don't set flag, should default to False

                # Execute
                provider.process_document('input.pdf', 'output.docx')

                # Verify line-based extraction was called
                mock_ocr_azure.assert_called_once_with(b'PDF bytes')
                mock_save_docx.assert_called_once()

    @patch('src.ocr.azure_provider.os.path.getsize')
    @patch('src.ocr.azure_provider.AzureOCRProvider._extract_paragraphs_with_formatting')
    @patch('src.ocr.azure_provider.AzureOCRProvider._save_paragraphs_to_docx')
    @patch('src.ocr.azure_provider.AzureOCRProvider._detect_page_searchability')
    @patch('src.ocr.azure_provider.pdfplumber.open')
    @patch('src.ocr.azure_provider.os.path.exists')
    def test_process_document_explicit_parameter_overrides_flag(
        self, mock_exists, mock_pdfplumber, mock_detect, mock_save_para, mock_extract_para, mock_getsize
    ):
        """Test process_document explicit parameter overrides instance flag."""
        # Setup
        config = {
            'endpoint': 'https://test.cognitiveservices.azure.com/',
            'api_key': 'test_key'
        }

        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        mock_detect.return_value = [False]  # Non-searchable page to trigger OCR

        # Mock PDF context
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        # Mock paragraph extraction
        mock_paragraph = Mock()
        mock_paragraph.content = "Test content"
        mock_extract_para.return_value = [mock_paragraph]

        with patch('src.ocr.azure_provider.DocumentAnalysisClient'):
            with patch('builtins.open', create=True) as mock_file:
                mock_file.return_value.__enter__.return_value.read.return_value = b'PDF bytes'

                provider = AzureOCRProvider(config)
                provider.use_paragraph_extraction = False  # Set to False

                # Execute with explicit True parameter
                provider.process_document('input.pdf', 'output.docx', use_paragraph_extraction=True)

                # Verify paragraph extraction was called (explicit param wins)
                mock_extract_para.assert_called_once_with(b'PDF bytes')
                mock_save_para.assert_called_once()
