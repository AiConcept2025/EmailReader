"""
Unit Tests for TranslatorFactory

Tests the factory pattern for creating translator instances based on configuration.
"""

import pytest
from src.translation.translator_factory import TranslatorFactory
from src.translation.google_text_translator import GoogleTextTranslator
from src.translation.google_doc_translator import GoogleDocTranslator
from src.translation.google_batch_translator import GoogleBatchTranslator


class TestTranslatorFactory:
    """Test cases for TranslatorFactory."""

    def test_valid_providers_includes_all_three(self):
        """Test that VALID_PROVIDERS contains all three provider types."""
        expected_providers = {'google_text', 'google_doc', 'google_batch'}
        assert TranslatorFactory.VALID_PROVIDERS == expected_providers

    def test_get_translator_returns_google_text_translator(self):
        """Test factory returns GoogleTextTranslator for 'google_text' provider."""
        config = {
            'translation': {
                'provider': 'google_text',
                'google_text': {
                    'api_key': 'test-key'
                }
            }
        }

        translator = TranslatorFactory.get_translator(config)

        assert isinstance(translator, GoogleTextTranslator)

    def test_get_translator_returns_google_doc_translator(self):
        """Test factory returns GoogleDocTranslator for 'google_doc' provider."""
        config = {
            'translation': {
                'provider': 'google_doc',
                'google_doc': {
                    'project_id': 'test-project-id',
                    'location': 'us-central1'
                }
            }
        }

        translator = TranslatorFactory.get_translator(config)

        assert isinstance(translator, GoogleDocTranslator)

    def test_get_translator_returns_google_batch_translator(self):
        """Test factory returns GoogleBatchTranslator for 'google_batch' provider."""
        config = {
            'translation': {
                'provider': 'google_batch',
                'google_doc': {  # Reuses google_doc config
                    'project_id': 'test-project-id',
                    'location': 'us-central1'
                }
            }
        }

        translator = TranslatorFactory.get_translator(config)

        assert isinstance(translator, GoogleBatchTranslator)

    def test_get_translator_raises_error_for_invalid_provider(self):
        """Test factory raises ValueError for invalid provider type."""
        config = {
            'translation': {
                'provider': 'invalid_provider'
            }
        }

        with pytest.raises(ValueError) as exc_info:
            TranslatorFactory.get_translator(config)

        assert "Invalid translation provider: invalid_provider" in str(exc_info.value)
        assert "Valid providers:" in str(exc_info.value)

    def test_get_translator_raises_error_for_google_doc_missing_project_id(self):
        """Test factory raises ValueError when google_doc provider lacks project_id."""
        config = {
            'translation': {
                'provider': 'google_doc',
                'google_doc': {
                    'location': 'us-central1'
                    # Missing project_id
                }
            }
        }

        with pytest.raises(ValueError) as exc_info:
            TranslatorFactory.get_translator(config)

        assert "Google Document Translation requires 'project_id'" in str(exc_info.value)

    def test_get_translator_raises_error_for_google_batch_missing_project_id(self):
        """Test factory raises ValueError when google_batch provider lacks project_id."""
        config = {
            'translation': {
                'provider': 'google_batch',
                'google_doc': {
                    'location': 'us-central1'
                    # Missing project_id
                }
            }
        }

        with pytest.raises(ValueError) as exc_info:
            TranslatorFactory.get_translator(config)

        assert "Google Batch Translation requires 'project_id'" in str(exc_info.value)

    def test_get_translator_uses_default_provider_when_not_specified(self):
        """Test factory uses 'google_text' as default provider when not specified."""
        config = {
            'translation': {
                'google_text': {
                    'api_key': 'test-key'
                }
                # No 'provider' key
            }
        }

        translator = TranslatorFactory.get_translator(config)

        assert isinstance(translator, GoogleTextTranslator)

    def test_get_translator_handles_empty_translation_config(self):
        """Test factory handles empty translation config with default provider."""
        config = {
            'translation': {}
        }

        translator = TranslatorFactory.get_translator(config)

        # Should default to google_text
        assert isinstance(translator, GoogleTextTranslator)

    def test_get_translator_google_batch_reuses_google_doc_config(self):
        """Test that google_batch provider correctly reuses google_doc configuration."""
        config = {
            'translation': {
                'provider': 'google_batch',
                'google_doc': {
                    'project_id': 'batch-test-project',
                    'location': 'eu-west1',
                    'service_account_path': '/path/to/credentials.json'
                }
            }
        }

        translator = TranslatorFactory.get_translator(config)

        assert isinstance(translator, GoogleBatchTranslator)
        # Verify the translator received the correct config
        assert translator.project_id == 'batch-test-project'
        assert translator.location == 'eu-west1'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
