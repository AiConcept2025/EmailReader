"""Unit tests for OCR providers."""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ocr import OCRProviderFactory, BaseOCRProvider
from src.ocr.default_provider import DefaultOCRProvider
from src.ocr.landing_ai_provider import LandingAIOCRProvider


class TestOCRProviderFactory:
    """Test OCR provider factory."""

    def test_factory_creates_default_provider(self):
        """Test factory creates default provider when configured."""
        config = {'ocr': {'provider': 'default'}}
        provider = OCRProviderFactory.get_provider(config)
        assert isinstance(provider, DefaultOCRProvider)

    def test_factory_creates_landing_ai_provider(self):
        """Test factory creates LandingAI provider with API key."""
        config = {
            'ocr': {
                'provider': 'landing_ai',
                'landing_ai': {
                    'api_key': 'test_key',
                    'base_url': 'https://api.va.landing.ai/v1'
                }
            }
        }
        provider = OCRProviderFactory.get_provider(config)
        assert isinstance(provider, LandingAIOCRProvider)

    def test_factory_fallback_when_no_api_key(self):
        """Test factory falls back to default when API key missing."""
        config = {
            'ocr': {
                'provider': 'landing_ai',
                'landing_ai': {'api_key': ''}
            }
        }
        provider = OCRProviderFactory.get_provider(config)
        assert isinstance(provider, DefaultOCRProvider)

    def test_factory_raises_on_invalid_provider(self):
        """Test factory raises error for invalid provider."""
        config = {'ocr': {'provider': 'invalid_provider'}}
        with pytest.raises(ValueError, match="Unknown OCR provider"):
            OCRProviderFactory.get_provider(config)

    def test_factory_default_provider_type(self):
        """Test factory defaults to 'default' when provider not specified."""
        config = {'ocr': {}}
        provider = OCRProviderFactory.get_provider(config)
        assert isinstance(provider, DefaultOCRProvider)

    def test_factory_case_insensitive_provider_name(self):
        """Test factory handles case-insensitive provider names."""
        config = {'ocr': {'provider': 'LANDING_AI', 'landing_ai': {'api_key': 'test_key'}}}
        provider = OCRProviderFactory.get_provider(config)
        assert isinstance(provider, LandingAIOCRProvider)

    def test_validate_config_valid_default(self):
        """Test configuration validation for default provider."""
        config = {'ocr': {'provider': 'default'}}
        assert OCRProviderFactory.validate_config(config) is True

    def test_validate_config_valid_landing_ai(self):
        """Test configuration validation for LandingAI with API key."""
        config = {
            'ocr': {
                'provider': 'landing_ai',
                'landing_ai': {'api_key': 'test_key'}
            }
        }
        assert OCRProviderFactory.validate_config(config) is True

    def test_validate_config_missing_api_key(self):
        """Test configuration validation fails for LandingAI without API key."""
        config = {
            'ocr': {
                'provider': 'landing_ai',
                'landing_ai': {}
            }
        }
        assert OCRProviderFactory.validate_config(config) is False

    def test_validate_config_missing_ocr_section(self):
        """Test configuration validation fails when OCR section is missing."""
        config = {}
        assert OCRProviderFactory.validate_config(config) is False

    def test_validate_config_invalid_provider(self):
        """Test configuration validation fails for invalid provider."""
        config = {'ocr': {'provider': 'invalid'}}
        assert OCRProviderFactory.validate_config(config) is False


class TestDefaultOCRProvider:
    """Test default Tesseract OCR provider."""

    def test_default_provider_initialization(self):
        """Test default provider initializes correctly."""
        provider = DefaultOCRProvider({})
        assert provider is not None
        assert provider.config == {}

    def test_default_provider_initialization_with_config(self):
        """Test default provider initializes with configuration."""
        config = {'dpi': 300, 'languages': 'eng+rus'}
        provider = DefaultOCRProvider(config)
        assert provider.config == config

    @patch('src.ocr.default_provider.ocr_pdf_image_to_doc')
    def test_process_document_calls_tesseract(self, mock_ocr):
        """Test process_document delegates to Tesseract."""
        provider = DefaultOCRProvider({})
        provider.process_document('input.pdf', 'output.docx')
        mock_ocr.assert_called_once_with('input.pdf', 'output.docx')

    @patch('src.ocr.default_provider.ocr_pdf_image_to_doc')
    def test_process_document_propagates_exceptions(self, mock_ocr):
        """Test process_document propagates exceptions from Tesseract."""
        mock_ocr.side_effect = FileNotFoundError("File not found")
        provider = DefaultOCRProvider({})

        with pytest.raises(FileNotFoundError):
            provider.process_document('missing.pdf', 'output.docx')

    @patch('src.ocr.default_provider.is_pdf_searchable_pypdf')
    def test_is_pdf_searchable_delegates(self, mock_check):
        """Test is_pdf_searchable delegates to existing function."""
        mock_check.return_value = True
        provider = DefaultOCRProvider({})
        result = provider.is_pdf_searchable('test.pdf')
        assert result is True
        mock_check.assert_called_once_with('test.pdf')

    @patch('src.ocr.default_provider.is_pdf_searchable_pypdf')
    def test_is_pdf_searchable_returns_false(self, mock_check):
        """Test is_pdf_searchable returns False for scanned PDFs."""
        mock_check.return_value = False
        provider = DefaultOCRProvider({})
        result = provider.is_pdf_searchable('scanned.pdf')
        assert result is False

    @patch('src.ocr.default_provider.is_pdf_searchable_pypdf')
    def test_is_pdf_searchable_propagates_exceptions(self, mock_check):
        """Test is_pdf_searchable propagates exceptions."""
        mock_check.side_effect = ValueError("Invalid PDF")
        provider = DefaultOCRProvider({})

        with pytest.raises(ValueError):
            provider.is_pdf_searchable('invalid.pdf')


class TestLandingAIProvider:
    """Test LandingAI OCR provider."""

    def test_landing_ai_initialization(self):
        """Test LandingAI provider initializes with config."""
        config = {
            'api_key': 'test_key',
            'base_url': 'https://api.va.landing.ai/v1',
            'model': 'dpt-2-latest'
        }
        provider = LandingAIOCRProvider(config)
        assert provider.api_key == 'test_key'
        assert provider.model == 'dpt-2-latest'
        assert provider.base_url == 'https://api.va.landing.ai/v1'

    def test_landing_ai_initialization_defaults(self):
        """Test LandingAI provider uses default values."""
        config = {'api_key': 'test_key'}
        provider = LandingAIOCRProvider(config)
        assert provider.model == 'dpt-2-latest'
        assert provider.base_url == 'https://api.va.landing.ai/v1'
        assert provider.split_mode == 'page'
        assert provider.preserve_layout is True

    def test_landing_ai_raises_without_api_key(self):
        """Test LandingAI provider requires API key."""
        with pytest.raises(ValueError, match="API key is required"):
            LandingAIOCRProvider({'api_key': ''})

    def test_landing_ai_raises_with_none_api_key(self):
        """Test LandingAI provider raises error when API key is None."""
        with pytest.raises(ValueError, match="API key is required"):
            LandingAIOCRProvider({})

    def test_landing_ai_custom_retry_config(self):
        """Test LandingAI provider accepts custom retry configuration."""
        config = {
            'api_key': 'test_key',
            'retry': {
                'max_attempts': 5,
                'backoff_factor': 3,
                'timeout': 60
            }
        }
        provider = LandingAIOCRProvider(config)
        assert provider.max_attempts == 5
        assert provider.backoff_factor == 3
        assert provider.timeout == 60

    def test_landing_ai_custom_chunk_processing_config(self):
        """Test LandingAI provider accepts custom chunk processing config."""
        config = {
            'api_key': 'test_key',
            'chunk_processing': {
                'use_grounding': False,
                'maintain_positions': False
            }
        }
        provider = LandingAIOCRProvider(config)
        assert provider.use_grounding is False
        assert provider.maintain_positions is False

    @patch('src.ocr.landing_ai_provider.requests.post')
    def test_api_call_with_retry_success(self, mock_post):
        """Test API call succeeds on first attempt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'chunks': [{'text': 'Test', 'grounding': {}}]}
        mock_post.return_value = mock_response

        config = {'api_key': 'test_key'}
        provider = LandingAIOCRProvider(config)

        # Create a temporary test file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'PDF content')
            temp_path = f.name

        try:
            response = provider._call_api_with_retry(temp_path)
            assert response == {'chunks': [{'text': 'Test', 'grounding': {}}]}
            assert mock_post.call_count == 1
        finally:
            os.remove(temp_path)

    @patch('src.ocr.landing_ai_provider.requests.post')
    @patch('src.ocr.landing_ai_provider.time.sleep')
    def test_api_call_retries_on_server_error(self, mock_sleep, mock_post):
        """Test API call retries on 5xx errors."""
        # First two attempts fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = 'Server error'

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {'chunks': []}

        mock_post.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]

        config = {'api_key': 'test_key', 'retry': {'max_attempts': 3}}
        provider = LandingAIOCRProvider(config)

        # Create a temporary test file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'PDF content')
            temp_path = f.name

        try:
            response = provider._call_api_with_retry(temp_path)
            assert response == {'chunks': []}
            assert mock_post.call_count == 3
            assert mock_sleep.call_count == 2  # Sleep between retries
        finally:
            os.remove(temp_path)

    @patch('src.ocr.landing_ai_provider.requests.post')
    def test_api_call_fails_on_client_error(self, mock_post):
        """Test API call doesn't retry on 4xx errors."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad request'
        mock_post.return_value = mock_response

        config = {'api_key': 'test_key'}
        provider = LandingAIOCRProvider(config)

        # Create a temporary test file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'PDF content')
            temp_path = f.name

        try:
            with pytest.raises(RuntimeError, match="client error"):
                provider._call_api_with_retry(temp_path)
            assert mock_post.call_count == 1  # No retries on 4xx
        finally:
            os.remove(temp_path)

    @patch('src.ocr.landing_ai_provider.requests.post')
    @patch('src.ocr.landing_ai_provider.time.sleep')
    def test_api_call_fails_after_max_retries(self, mock_sleep, mock_post):
        """Test API call fails after exhausting retries."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.text = 'Service unavailable'
        mock_post.return_value = mock_response

        config = {'api_key': 'test_key', 'retry': {'max_attempts': 3}}
        provider = LandingAIOCRProvider(config)

        # Create a temporary test file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'PDF content')
            temp_path = f.name

        try:
            with pytest.raises(RuntimeError, match="failed after 3 attempts"):
                provider._call_api_with_retry(temp_path)
            assert mock_post.call_count == 3
        finally:
            os.remove(temp_path)

    @patch('src.ocr.landing_ai_provider.is_pdf_searchable_pypdf')
    def test_is_pdf_searchable_delegates(self, mock_check):
        """Test is_pdf_searchable delegates to existing function."""
        mock_check.return_value = True
        config = {'api_key': 'test_key'}
        provider = LandingAIOCRProvider(config)

        result = provider.is_pdf_searchable('test.pdf')
        assert result is True
        mock_check.assert_called_once_with('test.pdf')

    def test_extract_with_positions_empty_chunks(self):
        """Test extracting text from empty chunks list."""
        config = {'api_key': 'test_key'}
        provider = LandingAIOCRProvider(config)

        result = provider._extract_with_positions({'chunks': []})
        assert result == ""

    def test_extract_with_positions_simple_concatenation(self):
        """Test simple text extraction without grounding."""
        config = {
            'api_key': 'test_key',
            'chunk_processing': {
                'use_grounding': False,
                'maintain_positions': False
            }
        }
        provider = LandingAIOCRProvider(config)

        chunks = [
            {'text': 'Line 1', 'grounding': {}},
            {'text': 'Line 2', 'grounding': {}},
            {'text': 'Line 3', 'grounding': {}}
        ]

        result = provider._extract_with_positions({'chunks': chunks})
        assert result == 'Line 1\nLine 2\nLine 3'

    @patch('src.ocr.landing_ai_provider.convert_txt_to_docx')
    def test_save_as_docx_creates_file(self, mock_convert):
        """Test saving text as DOCX file."""
        config = {'api_key': 'test_key'}
        provider = LandingAIOCRProvider(config)

        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            output_path = f.name

        try:
            # Mock the convert function to create the output file
            def create_output(*args):
                with open(output_path, 'wb') as f:
                    f.write(b'Fake DOCX content')

            mock_convert.side_effect = create_output

            provider._save_as_docx('Test content', output_path)

            mock_convert.assert_called_once()
            assert os.path.exists(output_path)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    @patch('src.ocr.landing_ai_provider.LandingAIOCRProvider._call_api_with_retry')
    @patch('src.ocr.landing_ai_provider.LandingAIOCRProvider._extract_with_positions')
    @patch('src.ocr.landing_ai_provider.LandingAIOCRProvider._save_as_docx')
    def test_process_document_integration(self, mock_save, mock_extract, mock_api):
        """Test full document processing flow."""
        mock_api.return_value = {'chunks': [{'text': 'Test', 'grounding': {}}]}
        mock_extract.return_value = 'Extracted text'

        config = {'api_key': 'test_key'}
        provider = LandingAIOCRProvider(config)

        # Create a temporary test file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'PDF content')
            temp_path = f.name

        try:
            provider.process_document(temp_path, 'output.docx')

            mock_api.assert_called_once_with(temp_path)
            mock_extract.assert_called_once()
            mock_save.assert_called_once_with('Extracted text', 'output.docx')
        finally:
            os.remove(temp_path)

    def test_process_document_file_not_found(self):
        """Test process_document raises error for missing file."""
        config = {'api_key': 'test_key'}
        provider = LandingAIOCRProvider(config)

        with pytest.raises(FileNotFoundError):
            provider.process_document('/nonexistent/file.pdf', 'output.docx')

    @patch('src.ocr.landing_ai_provider.LandingAIOCRProvider._call_api_with_retry')
    def test_process_document_handles_empty_text(self, mock_api):
        """Test process_document handles empty extracted text."""
        mock_api.return_value = {'chunks': []}

        config = {'api_key': 'test_key'}
        provider = LandingAIOCRProvider(config)

        # Create a temporary test file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'PDF content')
            temp_path = f.name

        output_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
                output_path = f.name

            # Mock convert_txt_to_docx to create the file
            with patch('src.ocr.landing_ai_provider.convert_txt_to_docx') as mock_convert:
                def create_file(*args):
                    with open(output_path, 'wb') as f:
                        f.write(b'Empty DOCX')

                mock_convert.side_effect = create_file
                provider.process_document(temp_path, output_path)

                # Verify it used the "no content" message
                call_args = mock_convert.call_args[0]
                assert '[No text content extracted from document]' in call_args[0]
        finally:
            os.remove(temp_path)
            if output_path and os.path.exists(output_path):
                os.remove(output_path)
