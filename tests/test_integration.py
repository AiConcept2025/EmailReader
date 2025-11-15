"""Integration tests for OCR system."""
import os
import tempfile
import pytest
from pathlib import Path
from src.ocr import OCRProviderFactory
from src.document_analyzer import requires_ocr, get_document_type
from src.ocr.default_provider import DefaultOCRProvider
from src.ocr.landing_ai_provider import LandingAIOCRProvider


class TestOCRIntegration:
    """Integration tests using real files and providers."""

    @pytest.fixture
    def test_docs_path(self):
        """Get path to test documents."""
        return os.path.join(os.path.dirname(__file__), '..', 'test_docs')

    @pytest.fixture
    def output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_provider_switching_default(self):
        """Test switching to default provider."""
        config = {'ocr': {'provider': 'default'}}
        provider = OCRProviderFactory.get_provider(config)
        assert isinstance(provider, DefaultOCRProvider)

    def test_provider_switching_landing_ai_with_key(self):
        """Test switching to LandingAI provider with API key."""
        config = {
            'ocr': {
                'provider': 'landing_ai',
                'landing_ai': {'api_key': 'test_key_123'}
            }
        }
        provider = OCRProviderFactory.get_provider(config)
        assert isinstance(provider, LandingAIOCRProvider)

    def test_provider_switching_landing_ai_fallback(self):
        """Test fallback to default when LandingAI key is missing."""
        config = {
            'ocr': {
                'provider': 'landing_ai',
                'landing_ai': {}
            }
        }
        provider = OCRProviderFactory.get_provider(config)
        # Should fall back to default
        assert isinstance(provider, DefaultOCRProvider)

    def test_searchable_pdf_bypasses_ocr(self, test_docs_path):
        """Test searchable PDF is correctly identified."""
        pdf_path = os.path.join(test_docs_path, 'file-sample-pdf.pdf')
        if os.path.exists(pdf_path):
            assert requires_ocr(pdf_path) is False
            doc_type = get_document_type(pdf_path)
            assert doc_type == 'pdf_searchable'
        else:
            pytest.skip(f"Test file not found: {pdf_path}")

    def test_scanned_pdf_uses_ocr(self, test_docs_path):
        """Test scanned PDF requires OCR."""
        pdf_path = os.path.join(test_docs_path, 'PDF-scanned-rus-words.pdf')
        if os.path.exists(pdf_path):
            assert requires_ocr(pdf_path) is True
            doc_type = get_document_type(pdf_path)
            assert doc_type == 'pdf_scanned'
        else:
            pytest.skip(f"Test file not found: {pdf_path}")

    def test_image_pdf_detection(self, test_docs_path):
        """Test image-based PDF detection."""
        pdf_path = os.path.join(test_docs_path, 'file-sample-img.pdf')
        if os.path.exists(pdf_path):
            doc_type = get_document_type(pdf_path)
            assert doc_type in ['pdf_searchable', 'pdf_scanned']
        else:
            pytest.skip(f"Test file not found: {pdf_path}")

    def test_word_document_no_ocr(self, test_docs_path):
        """Test Word documents don't require OCR."""
        doc_path = os.path.join(test_docs_path, 'file-sample-doc.doc')
        if os.path.exists(doc_path):
            assert requires_ocr(doc_path) is False
            doc_type = get_document_type(doc_path)
            assert doc_type == 'word_document'
        else:
            pytest.skip(f"Test file not found: {doc_path}")

    def test_text_document_no_ocr(self, test_docs_path):
        """Test text documents don't require OCR."""
        txt_path = os.path.join(test_docs_path, 'file-sample-txt.txt')
        if os.path.exists(txt_path):
            assert requires_ocr(txt_path) is False
            doc_type = get_document_type(txt_path)
            assert doc_type == 'text_document'
        else:
            pytest.skip(f"Test file not found: {txt_path}")

    def test_provider_factory_with_full_config(self):
        """Test provider factory with complete configuration."""
        config = {
            'ocr': {
                'provider': 'landing_ai',
                'landing_ai': {
                    'api_key': 'test_key',
                    'base_url': 'https://api.va.landing.ai/v1',
                    'model': 'dpt-2-latest',
                    'split_mode': 'page',
                    'preserve_layout': True,
                    'chunk_processing': {
                        'use_grounding': True,
                        'maintain_positions': True
                    },
                    'retry': {
                        'max_attempts': 3,
                        'backoff_factor': 2,
                        'timeout': 30
                    }
                }
            }
        }

        provider = OCRProviderFactory.get_provider(config)
        assert isinstance(provider, LandingAIOCRProvider)
        assert provider.api_key == 'test_key'
        assert provider.model == 'dpt-2-latest'
        assert provider.preserve_layout is True
        assert provider.max_attempts == 3

    def test_provider_validation_workflow(self):
        """Test configuration validation before provider creation."""
        # Valid configuration
        valid_config = {
            'ocr': {
                'provider': 'default'
            }
        }
        assert OCRProviderFactory.validate_config(valid_config) is True
        provider = OCRProviderFactory.get_provider(valid_config)
        assert provider is not None

        # Invalid configuration
        invalid_config = {
            'ocr': {
                'provider': 'invalid'
            }
        }
        assert OCRProviderFactory.validate_config(invalid_config) is False
        with pytest.raises(ValueError):
            OCRProviderFactory.get_provider(invalid_config)

    def test_document_type_workflow(self, test_docs_path):
        """Test complete document type detection workflow."""
        test_files = {
            'file-sample-pdf.pdf': ('pdf_searchable', False),
            'PDF-scanned-rus-words.pdf': ('pdf_scanned', True),
            'file-sample-doc.doc': ('word_document', False),
            'file-sample-txt.txt': ('text_document', False),
            'file-sample-rtf.rtf': ('text_document', False)
        }

        for filename, (expected_type, expected_ocr) in test_files.items():
            file_path = os.path.join(test_docs_path, filename)
            if os.path.exists(file_path):
                doc_type = get_document_type(file_path)
                needs_ocr = requires_ocr(file_path)

                assert doc_type == expected_type, \
                    f"Expected {expected_type} for {filename}, got {doc_type}"
                assert needs_ocr == expected_ocr, \
                    f"Expected OCR={expected_ocr} for {filename}, got {needs_ocr}"

    def test_default_provider_with_real_searchable_pdf(self, test_docs_path):
        """Test default provider can check searchable PDF."""
        pdf_path = os.path.join(test_docs_path, 'file-sample-pdf.pdf')
        if not os.path.exists(pdf_path):
            pytest.skip(f"Test file not found: {pdf_path}")

        config = {'ocr': {'provider': 'default'}}
        provider = OCRProviderFactory.get_provider(config)

        # Should be able to check if PDF is searchable
        is_searchable = provider.is_pdf_searchable(pdf_path)
        assert is_searchable is True

    def test_default_provider_with_real_scanned_pdf(self, test_docs_path):
        """Test default provider can check scanned PDF."""
        pdf_path = os.path.join(test_docs_path, 'PDF-scanned-rus-words.pdf')
        if not os.path.exists(pdf_path):
            pytest.skip(f"Test file not found: {pdf_path}")

        config = {'ocr': {'provider': 'default'}}
        provider = OCRProviderFactory.get_provider(config)

        # Should detect that PDF is not searchable
        is_searchable = provider.is_pdf_searchable(pdf_path)
        assert is_searchable is False

    def test_landing_ai_provider_with_real_pdf(self, test_docs_path):
        """Test LandingAI provider can check PDF searchability."""
        pdf_path = os.path.join(test_docs_path, 'file-sample-pdf.pdf')
        if not os.path.exists(pdf_path):
            pytest.skip(f"Test file not found: {pdf_path}")

        config = {
            'ocr': {
                'provider': 'landing_ai',
                'landing_ai': {'api_key': 'test_key'}
            }
        }
        provider = OCRProviderFactory.get_provider(config)

        # Should be able to check searchability (delegates to same function)
        is_searchable = provider.is_pdf_searchable(pdf_path)
        assert is_searchable is True

    def test_provider_interface_consistency(self):
        """Test both providers implement same interface."""
        default_provider = DefaultOCRProvider({})
        landing_ai_provider = LandingAIOCRProvider({'api_key': 'test_key'})

        # Both should have same methods
        assert hasattr(default_provider, 'process_document')
        assert hasattr(default_provider, 'is_pdf_searchable')
        assert hasattr(landing_ai_provider, 'process_document')
        assert hasattr(landing_ai_provider, 'is_pdf_searchable')

        # Both should be callable
        assert callable(default_provider.process_document)
        assert callable(default_provider.is_pdf_searchable)
        assert callable(landing_ai_provider.process_document)
        assert callable(landing_ai_provider.is_pdf_searchable)

    def test_configuration_edge_cases(self):
        """Test edge cases in configuration handling."""
        # Empty config should default to 'default' provider
        empty_config = {}
        provider = OCRProviderFactory.get_provider(empty_config)
        assert isinstance(provider, DefaultOCRProvider)

        # Config without provider should default to 'default'
        no_provider_config = {'ocr': {}}
        provider = OCRProviderFactory.get_provider(no_provider_config)
        assert isinstance(provider, DefaultOCRProvider)

        # Case variations should work
        upper_config = {'ocr': {'provider': 'DEFAULT'}}
        provider = OCRProviderFactory.get_provider(upper_config)
        assert isinstance(provider, DefaultOCRProvider)

    def test_all_test_files_exist(self, test_docs_path):
        """Verify all expected test files are present."""
        expected_files = [
            'file-sample-pdf.pdf',
            'PDF-scanned-rus-words.pdf',
            'file-sample-img.pdf',
            'file-sample-doc.doc',
            'file-sample-txt.txt',
            'file-sample-rtf.rtf'
        ]

        missing_files = []
        for filename in expected_files:
            file_path = os.path.join(test_docs_path, filename)
            if not os.path.exists(file_path):
                missing_files.append(filename)

        if missing_files:
            pytest.skip(f"Missing test files: {', '.join(missing_files)}")
