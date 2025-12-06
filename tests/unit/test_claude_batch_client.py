"""Unit tests for Claude Batch API client.

Tests the ClaudeBatchClient class for batch validation requests and API interactions.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from dataclasses import asdict
from src.translation.claude_validator.batch_client import (
    ClaudeBatchClient,
    BatchRequest,
    BatchResult
)


class TestBatchRequestDataclass:
    """Tests for BatchRequest dataclass."""

    def test_batch_request_creation(self):
        """Verify BatchRequest can be created with required fields."""
        request = BatchRequest(
            custom_id='test_001',
            translated_text='Hello world',
            target_lang='en',
            role='paragraph',
            validation_rules={'avoid_characters': ['-']}
        )

        assert request.custom_id == 'test_001'
        assert request.translated_text == 'Hello world'
        assert request.target_lang == 'en'
        assert request.role == 'paragraph'
        assert request.validation_rules == {'avoid_characters': ['-']}

    def test_batch_request_no_source_text(self):
        """CRITICAL: Verify BatchRequest does NOT contain source_text."""
        request = BatchRequest(
            custom_id='test_001',
            translated_text='Hello',
            target_lang='en',
            role='paragraph',
            validation_rules={}
        )

        # Verify no source_text attribute exists
        assert not hasattr(request, 'source_text')
        assert not hasattr(request, 'source_lang')


class TestBatchResultDataclass:
    """Tests for BatchResult dataclass."""

    def test_batch_result_creation(self):
        """Verify BatchResult can be created."""
        result = BatchResult(
            custom_id='test_001',
            validated_text='Hello world',
            confidence_score=0.95,
            changes_made=False
        )

        assert result.custom_id == 'test_001'
        assert result.validated_text == 'Hello world'
        assert result.confidence_score == 0.95
        assert result.changes_made is False
        assert result.error is None

    def test_batch_result_with_error(self):
        """Verify BatchResult can include error message."""
        result = BatchResult(
            custom_id='test_001',
            validated_text='',
            confidence_score=0.0,
            changes_made=False,
            error='Rate limit exceeded'
        )

        assert result.error == 'Rate limit exceeded'


class TestClaudeBatchClientInitialization:
    """Tests for ClaudeBatchClient initialization."""

    @patch('src.translation.claude_validator.batch_client.load_config')
    @patch('src.translation.claude_validator.batch_client.anthropic.Anthropic')
    def test_initialization_loads_config(self, mock_anthropic, mock_load_config):
        """Verify client initializes with config values."""
        mock_load_config.return_value = {
            'claude': {'api_key': 'test-key-123'}
        }
        mock_anthropic.return_value = MagicMock()

        config = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 2048,
            'temperature': 0.0,
            'batch': {
                'custom_id_prefix': 'validation',
                'polling_interval_seconds': 60,
                'max_wait_hours': 24
            },
            'caching': {
                'enabled': True,
                'cache_control_type': 'ephemeral'
            },
            'system_prompt': 'You are a validator.',
            'user_prompt_template': 'Validate: {translated_text}',
            'validation_rules': {'avoid_characters': ['-']}
        }

        client = ClaudeBatchClient(config)

        assert client.model == 'claude-sonnet-4-5-20250929'
        assert client.max_tokens == 2048
        assert client.temperature == 0.0
        assert client.custom_id_prefix == 'validation'

    @patch('src.translation.claude_validator.batch_client.load_config')
    def test_initialization_raises_without_api_key(self, mock_load_config):
        """Verify ValueError when API key missing."""
        mock_load_config.return_value = {'claude': {}}

        config = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 2048,
            'batch': {'custom_id_prefix': 'validation'},
            'caching': {'enabled': True},
            'system_prompt': 'Test',
            'user_prompt_template': 'Test'
        }

        with pytest.raises(ValueError) as exc_info:
            ClaudeBatchClient(config)

        assert 'Claude API key not found' in str(exc_info.value)

    @patch('src.translation.claude_validator.batch_client.load_config')
    @patch('src.translation.claude_validator.batch_client.anthropic.Anthropic')
    def test_initialization_raises_without_config_section(self, mock_anthropic, mock_load_config):
        """Verify ValueError when config.claude section missing."""
        mock_load_config.return_value = {}

        config = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 2048,
            'batch': {'custom_id_prefix': 'validation'},
            'caching': {'enabled': True},
            'system_prompt': 'Test',
            'user_prompt_template': 'Test'
        }

        with pytest.raises(ValueError):
            ClaudeBatchClient(config)

    @patch('src.translation.claude_validator.batch_client.load_config')
    @patch('src.translation.claude_validator.batch_client.anthropic.Anthropic')
    def test_initialization_with_default_temperature(self, mock_anthropic, mock_load_config):
        """Verify default temperature is used when not specified."""
        mock_load_config.return_value = {
            'claude': {'api_key': 'test-key'}
        }
        mock_anthropic.return_value = MagicMock()

        config = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 2048,
            'batch': {'custom_id_prefix': 'validation'},
            'caching': {'enabled': True},
            'system_prompt': 'Test',
            'user_prompt_template': 'Test'
        }

        client = ClaudeBatchClient(config)

        assert client.temperature == 0.0  # Default


class TestCreateBatchJob:
    """Tests for create_batch_job method."""

    @patch('src.translation.claude_validator.batch_client.load_config')
    @patch('src.translation.claude_validator.batch_client.anthropic.Anthropic')
    def test_create_batch_job_formats_requests(self, mock_anthropic_class, mock_load_config):
        """Verify batch job creation with BatchRequest objects."""
        mock_load_config.return_value = {
            'claude': {'api_key': 'test-key'}
        }

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_batch_response = MagicMock()
        mock_batch_response.id = 'batch_123'
        mock_batch_response.processing_status = 'in_progress'
        mock_client.messages.batches.create.return_value = mock_batch_response

        config = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 2048,
            'batch': {'custom_id_prefix': 'validation'},
            'caching': {'enabled': False},
            'system_prompt': 'You are a validator.',
            'user_prompt_template': 'Text: {translated_text}'
        }

        client = ClaudeBatchClient(config)

        requests = [
            BatchRequest(
                custom_id='test_001',
                translated_text='Hello world',
                target_lang='en',
                role='paragraph',
                validation_rules={}
            )
        ]

        batch_id = client.create_batch_job(requests)

        assert batch_id == 'batch_123'
        assert mock_client.messages.batches.create.called

    @patch('src.translation.claude_validator.batch_client.load_config')
    @patch('src.translation.claude_validator.batch_client.anthropic.Anthropic')
    def test_create_batch_job_applies_caching(self, mock_anthropic_class, mock_load_config):
        """Verify cache directive in system prompt."""
        mock_load_config.return_value = {
            'claude': {'api_key': 'test-key'}
        }

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_batch_response = MagicMock()
        mock_batch_response.id = 'batch_123'
        mock_client.messages.batches.create.return_value = mock_batch_response

        config = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 2048,
            'batch': {'custom_id_prefix': 'validation'},
            'caching': {
                'enabled': True,
                'cache_control_type': 'ephemeral'
            },
            'system_prompt': 'You are a validator.',
            'user_prompt_template': 'Text: {translated_text}'
        }

        client = ClaudeBatchClient(config)

        requests = [
            BatchRequest(
                custom_id='test_001',
                translated_text='Hello',
                target_lang='en',
                role='paragraph',
                validation_rules={}
            )
        ]

        client.create_batch_job(requests)

        # Verify create was called
        call_args = mock_client.messages.batches.create.call_args
        assert call_args is not None

        # Verify system prompt has cache control
        batch_requests = call_args[1]['requests']
        system_prompt = batch_requests[0]['params']['system']

        # Should be a list with cache_control when enabled
        assert isinstance(system_prompt, list)
        assert system_prompt[0]['cache_control']['type'] == 'ephemeral'

    @patch('src.translation.claude_validator.batch_client.load_config')
    @patch('src.translation.claude_validator.batch_client.anthropic.Anthropic')
    def test_create_batch_job_includes_validation_rules(self, mock_anthropic_class, mock_load_config):
        """Verify validation rules are included in user prompt."""
        mock_load_config.return_value = {
            'claude': {'api_key': 'test-key'}
        }

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_batch_response = MagicMock()
        mock_batch_response.id = 'batch_123'
        mock_client.messages.batches.create.return_value = mock_batch_response

        config = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 2048,
            'batch': {'custom_id_prefix': 'validation'},
            'caching': {'enabled': False},
            'system_prompt': 'Validator',
            'user_prompt_template': 'Rules:\n{validation_rules_text}\n\nText: {translated_text}'
        }

        client = ClaudeBatchClient(config)

        requests = [
            BatchRequest(
                custom_id='test_001',
                translated_text='Hello',
                target_lang='en',
                role='paragraph',
                validation_rules={'avoid_characters': ['-']}
            )
        ]

        client.create_batch_job(requests)

        # Verify user prompt contains rules
        call_args = mock_client.messages.batches.create.call_args
        batch_requests = call_args[1]['requests']
        user_prompt = batch_requests[0]['params']['messages'][0]['content']

        assert "Avoid these characters: '-'" in user_prompt


class TestPollBatchStatus:
    """Tests for poll_batch_status method."""

    @patch('src.translation.claude_validator.batch_client.load_config')
    @patch('src.translation.claude_validator.batch_client.anthropic.Anthropic')
    def test_poll_batch_status_returns_status(self, mock_anthropic_class, mock_load_config):
        """Verify status polling."""
        mock_load_config.return_value = {
            'claude': {'api_key': 'test-key'}
        }

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_batch = MagicMock()
        mock_batch.processing_status = 'in_progress'
        mock_client.messages.batches.retrieve.return_value = mock_batch

        config = {
            'model': 'test-model',
            'max_tokens': 2048,
            'batch': {'custom_id_prefix': 'validation'},
            'caching': {'enabled': False},
            'system_prompt': 'Test',
            'user_prompt_template': 'Test'
        }

        client = ClaudeBatchClient(config)
        status = client.poll_batch_status('batch_123')

        assert status == 'in_progress'
        mock_client.messages.batches.retrieve.assert_called_once_with('batch_123')


class TestRetrieveBatchResults:
    """Tests for retrieve_batch_results method."""

    @patch('src.translation.claude_validator.batch_client.load_config')
    @patch('src.translation.claude_validator.batch_client.anthropic.Anthropic')
    def test_retrieve_batch_results_parses_responses(self, mock_anthropic_class, mock_load_config):
        """Verify result parsing from batch API."""
        mock_load_config.return_value = {
            'claude': {'api_key': 'test-key'}
        }

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock successful results
        mock_result = MagicMock()
        mock_result.custom_id = 'test_001'
        mock_result.result.type = 'message'
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = 'Validated text'
        mock_message.content = [mock_content]
        mock_result.result.message = mock_message

        mock_client.messages.batches.results.return_value = [mock_result]
        mock_batch = MagicMock()
        mock_client.messages.batches.retrieve.return_value = mock_batch

        config = {
            'model': 'test-model',
            'max_tokens': 2048,
            'batch': {'custom_id_prefix': 'validation'},
            'caching': {'enabled': False},
            'system_prompt': 'Test',
            'user_prompt_template': 'Test'
        }

        client = ClaudeBatchClient(config)
        results = client.retrieve_batch_results('batch_123')

        assert len(results) == 1
        assert results[0].custom_id == 'test_001'
        assert results[0].validated_text == 'Validated text'

    @patch('src.translation.claude_validator.batch_client.load_config')
    @patch('src.translation.claude_validator.batch_client.anthropic.Anthropic')
    def test_retrieve_batch_results_calculates_confidence(self, mock_anthropic_class, mock_load_config):
        """Verify confidence score calculation."""
        mock_load_config.return_value = {
            'claude': {'api_key': 'test-key'}
        }

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_result = MagicMock()
        mock_result.custom_id = 'test_001'
        mock_result.result.type = 'message'
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = 'Text'
        mock_message.content = [mock_content]
        mock_result.result.message = mock_message

        mock_client.messages.batches.results.return_value = [mock_result]
        mock_batch = MagicMock()
        mock_client.messages.batches.retrieve.return_value = mock_batch

        config = {
            'model': 'test-model',
            'max_tokens': 2048,
            'batch': {'custom_id_prefix': 'validation'},
            'caching': {'enabled': False},
            'system_prompt': 'Test',
            'user_prompt_template': 'Test'
        }

        client = ClaudeBatchClient(config)
        results = client.retrieve_batch_results('batch_123')

        # Confidence should be high by default
        assert results[0].confidence_score == 0.95

    @patch('src.translation.claude_validator.batch_client.load_config')
    @patch('src.translation.claude_validator.batch_client.anthropic.Anthropic')
    def test_retrieve_batch_results_handles_errors(self, mock_anthropic_class, mock_load_config):
        """Verify error handling in results."""
        mock_load_config.return_value = {
            'claude': {'api_key': 'test-key'}
        }

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_result = MagicMock()
        mock_result.custom_id = 'test_001'
        mock_result.result.type = 'error'
        mock_result.result.error = 'Rate limit exceeded'

        mock_client.messages.batches.results.return_value = [mock_result]
        mock_batch = MagicMock()
        mock_client.messages.batches.retrieve.return_value = mock_batch

        config = {
            'model': 'test-model',
            'max_tokens': 2048,
            'batch': {'custom_id_prefix': 'validation'},
            'caching': {'enabled': False},
            'system_prompt': 'Test',
            'user_prompt_template': 'Test'
        }

        client = ClaudeBatchClient(config)
        results = client.retrieve_batch_results('batch_123')

        assert len(results) == 1
        assert results[0].error == 'Rate limit exceeded'
        assert results[0].confidence_score == 0.0


class TestFormatUserPrompt:
    """Tests for _format_user_prompt method."""

    @patch('src.translation.claude_validator.batch_client.load_config')
    @patch('src.translation.claude_validator.batch_client.anthropic.Anthropic')
    def test_format_user_prompt_includes_validation_rules(self, mock_anthropic_class, mock_load_config):
        """Verify user prompt formatting with validation rules."""
        mock_load_config.return_value = {
            'claude': {'api_key': 'test-key'}
        }
        mock_anthropic_class.return_value = MagicMock()

        config = {
            'model': 'test-model',
            'max_tokens': 2048,
            'batch': {'custom_id_prefix': 'validation'},
            'caching': {'enabled': False},
            'system_prompt': 'Test',
            'user_prompt_template': 'Language: {target_lang}\nRole: {role}\nRules: {validation_rules_text}\nText: {translated_text}'
        }

        client = ClaudeBatchClient(config)

        request = BatchRequest(
            custom_id='test_001',
            translated_text='Hello world',
            target_lang='en',
            role='paragraph',
            validation_rules={'grammar_check': True}
        )

        prompt = client._format_user_prompt(request)

        assert 'Language: en' in prompt
        assert 'Role: paragraph' in prompt
        assert 'Text: Hello world' in prompt
        assert 'Fix grammar and spelling errors' in prompt

    @patch('src.translation.claude_validator.batch_client.load_config')
    @patch('src.translation.claude_validator.batch_client.anthropic.Anthropic')
    def test_format_user_prompt_formats_avoid_characters(self, mock_anthropic_class, mock_load_config):
        """Verify specific rule formatting."""
        mock_load_config.return_value = {
            'claude': {'api_key': 'test-key'}
        }
        mock_anthropic_class.return_value = MagicMock()

        config = {
            'model': 'test-model',
            'max_tokens': 2048,
            'batch': {'custom_id_prefix': 'validation'},
            'caching': {'enabled': False},
            'system_prompt': 'Test',
            'user_prompt_template': 'Rules: {validation_rules_text}\nText: {translated_text}'
        }

        client = ClaudeBatchClient(config)

        request = BatchRequest(
            custom_id='test_001',
            translated_text='Test',
            target_lang='en',
            role='paragraph',
            validation_rules={'avoid_characters': ['-', '~']}
        )

        prompt = client._format_user_prompt(request)

        assert "Avoid these characters: '-', '~'" in prompt

    @patch('src.translation.claude_validator.batch_client.load_config')
    @patch('src.translation.claude_validator.batch_client.anthropic.Anthropic')
    def test_format_user_prompt_multiple_rules(self, mock_anthropic_class, mock_load_config):
        """Verify formatting of multiple rules."""
        mock_load_config.return_value = {
            'claude': {'api_key': 'test-key'}
        }
        mock_anthropic_class.return_value = MagicMock()

        config = {
            'model': 'test-model',
            'max_tokens': 2048,
            'batch': {'custom_id_prefix': 'validation'},
            'caching': {'enabled': False},
            'system_prompt': 'Test',
            'user_prompt_template': 'Rules:\n{validation_rules_text}\nText: {translated_text}'
        }

        client = ClaudeBatchClient(config)

        request = BatchRequest(
            custom_id='test_001',
            translated_text='Test',
            target_lang='en',
            role='paragraph',
            validation_rules={
                'avoid_characters': ['-'],
                'preserve_formatting': True,
                'natural_phrasing': True
            }
        )

        prompt = client._format_user_prompt(request)

        assert "Avoid these characters: '-'" in prompt
        assert "Preserve ALL formatting" in prompt
        assert "Ensure natural, fluent phrasing" in prompt
