"""Unit tests for Claude translation validator.

Tests the ClaudeTranslationValidator class for batch validation orchestration.
"""

import pytest
import yaml
import tempfile
import time
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from src.models.paragraph import Paragraph, TextSpan
from src.translation.claude_validator.validator import (
    ClaudeTranslationValidator,
    ValidationResult
)
from src.translation.claude_validator.batch_client import BatchRequest, BatchResult


class TestValidationResultDataclass:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Verify ValidationResult can be created."""
        result = ValidationResult(
            validated_texts=['Hello', 'World'],
            confidence_scores=[0.95, 0.92],
            changes_made=1,
            quality_metrics={'total': 2},
            cache_stats={'hits': 10}
        )

        assert result.validated_texts == ['Hello', 'World']
        assert result.confidence_scores == [0.95, 0.92]
        assert result.changes_made == 1
        assert result.quality_metrics == {'total': 2}
        assert result.cache_stats == {'hits': 10}


class TestClaudeTranslationValidatorInitialization:
    """Tests for validator initialization."""

    def test_initialization_loads_config(self, tmp_path):
        """Verify validator initializes with YAML config."""
        config = {
            'claude': {
                'model': 'claude-sonnet-4-5-20250929',
                'max_tokens': 2048,
                'temperature': 0.0,
                'batch': {
                    'enabled': True,
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
                'validation': {
                    'mode': 'post_translation',
                    'confidence_threshold': 0.85
                }
            }
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        with patch('src.translation.claude_validator.validator.ClaudeBatchClient'):
            with patch('src.translation.claude_validator.validator.CacheManager'):
                validator = ClaudeTranslationValidator(str(config_path))

                assert validator.config == config
                assert validator.validation_mode == 'post_translation'
                assert validator.confidence_threshold == 0.85

    def test_initialization_raises_on_missing_config_file(self):
        """Verify FileNotFoundError when config not found."""
        with pytest.raises(FileNotFoundError) as exc_info:
            ClaudeTranslationValidator('/nonexistent/path/config.yaml')

        assert 'Config file not found' in str(exc_info.value)

    def test_initialization_raises_on_invalid_yaml(self, tmp_path):
        """Verify error on invalid YAML."""
        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            f.write("invalid: yaml: content:")

        with pytest.raises(yaml.YAMLError):
            ClaudeTranslationValidator(str(config_path))


class TestValidateTranslations:
    """Tests for validate_translations method."""

    @patch('src.translation.claude_validator.validator.ClaudeBatchClient')
    @patch('src.translation.claude_validator.validator.CacheManager')
    def test_validate_translations_calls_batch_mode(self, mock_cache_manager_class, mock_batch_client_class, tmp_path):
        """Verify batch mode is called by default."""
        config = {
            'claude': {
                'model': 'test-model',
                'max_tokens': 2048,
                'batch': {
                    'enabled': True,
                    'custom_id_prefix': 'validation',
                    'polling_interval_seconds': 1,
                    'max_wait_hours': 1
                },
                'caching': {'enabled': True},
                'system_prompt': 'Test',
                'user_prompt_template': 'Test: {translated_text}',
                'validation': {
                    'mode': 'post_translation',
                    'confidence_threshold': 0.85
                }
            }
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        with patch('src.translation.claude_validator.validator.ClaudeTranslationValidator._validate_batch') as mock_batch:
            mock_batch.return_value = ValidationResult(
                validated_texts=['Test'],
                confidence_scores=[0.95],
                changes_made=0,
                quality_metrics={},
                cache_stats={}
            )

            validator = ClaudeTranslationValidator(str(config_path))
            paragraphs = [Paragraph(content='Test', page=1, role='paragraph')]

            validator.validate_translations(paragraphs, 'en', use_batch=True)

            mock_batch.assert_called_once()

    @patch('src.translation.claude_validator.validator.ClaudeBatchClient')
    @patch('src.translation.claude_validator.validator.CacheManager')
    def test_validate_translations_raises_on_individual_mode(self, mock_cache_manager_class, mock_batch_client_class, tmp_path):
        """Verify NotImplementedError for individual validation mode."""
        config = {
            'claude': {
                'model': 'test-model',
                'max_tokens': 2048,
                'batch': {
                    'enabled': False,
                    'custom_id_prefix': 'validation',
                    'polling_interval_seconds': 1,
                    'max_wait_hours': 1
                },
                'caching': {'enabled': True},
                'system_prompt': 'Test',
                'user_prompt_template': 'Test: {translated_text}',
                'validation': {
                    'mode': 'post_translation',
                    'confidence_threshold': 0.85
                }
            }
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        validator = ClaudeTranslationValidator(str(config_path))
        paragraphs = [Paragraph(content='Test', page=1, role='paragraph')]

        with pytest.raises(NotImplementedError):
            validator.validate_translations(paragraphs, 'en', use_batch=False)


class TestValidateBatch:
    """Tests for _validate_batch method."""

    @patch('src.translation.claude_validator.validator.ClaudeBatchClient')
    @patch('src.translation.claude_validator.validator.CacheManager')
    def test_validate_batch_creates_batch_requests(self, mock_cache_manager_class, mock_batch_client_class, tmp_path):
        """Verify BatchRequest creation from paragraphs."""
        config = {
            'claude': {
                'model': 'test-model',
                'max_tokens': 2048,
                'batch': {
                    'enabled': True,
                    'custom_id_prefix': 'validation',
                    'polling_interval_seconds': 1,
                    'max_wait_hours': 1
                },
                'caching': {'enabled': True},
                'system_prompt': 'Test',
                'user_prompt_template': 'Test: {translated_text}',
                'validation': {
                    'mode': 'post_translation',
                    'confidence_threshold': 0.85
                },
                'validation_rules': {'avoid_characters': ['-']}
            }
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        # Mock batch client
        mock_batch_client = MagicMock()
        mock_batch_client.custom_id_prefix = 'validation'
        mock_batch_client.create_batch_job.return_value = 'batch_123'
        mock_batch_client.poll_batch_status.return_value = 'ended'
        mock_batch_client.retrieve_batch_results.return_value = [
            BatchResult(
                custom_id='validation_0000',
                validated_text='Test text',
                confidence_score=0.95,
                changes_made=False
            )
        ]
        mock_batch_client_class.return_value = mock_batch_client

        # Mock cache manager
        mock_cache_manager = MagicMock()
        mock_cache_manager.get_cache_stats.return_value = {'hits': 0}
        mock_cache_manager_class.return_value = mock_cache_manager

        validator = ClaudeTranslationValidator(str(config_path))
        paragraphs = [Paragraph(content='Test text', page=1, role='paragraph')]

        result = validator.validate_translations(paragraphs, 'en')

        # Verify create_batch_job was called
        assert mock_batch_client.create_batch_job.called
        call_args = mock_batch_client.create_batch_job.call_args
        batch_requests = call_args[0][0]

        assert len(batch_requests) == 1
        assert batch_requests[0].translated_text == 'Test text'
        assert batch_requests[0].target_lang == 'en'

    @patch('src.translation.claude_validator.validator.ClaudeBatchClient')
    @patch('src.translation.claude_validator.validator.CacheManager')
    def test_validate_batch_no_source_text(self, mock_cache_manager_class, mock_batch_client_class, tmp_path):
        """CRITICAL: Verify NO source text in requests."""
        config = {
            'claude': {
                'model': 'test-model',
                'max_tokens': 2048,
                'batch': {
                    'enabled': True,
                    'custom_id_prefix': 'validation',
                    'polling_interval_seconds': 1,
                    'max_wait_hours': 1
                },
                'caching': {'enabled': True},
                'system_prompt': 'Test',
                'user_prompt_template': 'Test: {translated_text}',
                'validation': {
                    'mode': 'post_translation',
                    'confidence_threshold': 0.85
                }
            }
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        # Mock batch client
        mock_batch_client = MagicMock()
        mock_batch_client.custom_id_prefix = 'validation'
        mock_batch_client.create_batch_job.return_value = 'batch_123'
        mock_batch_client.poll_batch_status.return_value = 'ended'
        mock_batch_client.retrieve_batch_results.return_value = [
            BatchResult(
                custom_id='validation_0000',
                validated_text='Test',
                confidence_score=0.95,
                changes_made=False
            )
        ]
        mock_batch_client_class.return_value = mock_batch_client

        # Mock cache manager
        mock_cache_manager = MagicMock()
        mock_cache_manager.get_cache_stats.return_value = {}
        mock_cache_manager_class.return_value = mock_cache_manager

        validator = ClaudeTranslationValidator(str(config_path))
        paragraphs = [Paragraph(content='Test', page=1, role='paragraph')]

        validator.validate_translations(paragraphs, 'en')

        # Verify no source_text in batch requests
        call_args = mock_batch_client.create_batch_job.call_args
        batch_requests = call_args[0][0]

        for request in batch_requests:
            assert not hasattr(request, 'source_text')
            assert not hasattr(request, 'source_lang')


class TestPollUntilComplete:
    """Tests for _poll_until_complete method."""

    @patch('src.translation.claude_validator.validator.ClaudeBatchClient')
    @patch('src.translation.claude_validator.validator.CacheManager')
    @patch('src.translation.claude_validator.validator.time.sleep')
    def test_poll_until_complete_waits_for_completion(self, mock_sleep, mock_cache_manager_class, mock_batch_client_class, tmp_path):
        """Verify polling behavior."""
        config = {
            'claude': {
                'model': 'test-model',
                'max_tokens': 2048,
                'batch': {
                    'enabled': True,
                    'custom_id_prefix': 'validation',
                    'polling_interval_seconds': 1,
                    'max_wait_hours': 1
                },
                'caching': {'enabled': True},
                'system_prompt': 'Test',
                'user_prompt_template': 'Test',
                'validation': {
                    'mode': 'post_translation',
                    'confidence_threshold': 0.85
                }
            }
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        # Mock batch client with status changes
        mock_batch_client = MagicMock()
        mock_batch_client.poll_batch_status.side_effect = ['in_progress', 'in_progress', 'ended']
        mock_batch_client_class.return_value = mock_batch_client

        # Mock cache manager
        mock_cache_manager = MagicMock()
        mock_cache_manager_class.return_value = mock_cache_manager

        validator = ClaudeTranslationValidator(str(config_path))
        status = validator._poll_until_complete('batch_123')

        assert status == 'ended'
        assert mock_batch_client.poll_batch_status.call_count == 3
        assert mock_sleep.call_count == 2

    @patch('src.translation.claude_validator.validator.ClaudeBatchClient')
    @patch('src.translation.claude_validator.validator.CacheManager')
    def test_poll_until_complete_raises_on_timeout(self, mock_cache_manager_class, mock_batch_client_class, tmp_path):
        """Verify timeout handling."""
        config = {
            'claude': {
                'model': 'test-model',
                'max_tokens': 2048,
                'batch': {
                    'enabled': True,
                    'custom_id_prefix': 'validation',
                    'polling_interval_seconds': 0.1,
                    'max_wait_hours': 0.00001  # Very short timeout
                },
                'caching': {'enabled': True},
                'system_prompt': 'Test',
                'user_prompt_template': 'Test',
                'validation': {
                    'mode': 'post_translation',
                    'confidence_threshold': 0.85
                }
            }
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        # Mock batch client that always returns in_progress
        mock_batch_client = MagicMock()
        mock_batch_client.poll_batch_status.return_value = 'in_progress'
        mock_batch_client_class.return_value = mock_batch_client

        # Mock cache manager
        mock_cache_manager = MagicMock()
        mock_cache_manager_class.return_value = mock_cache_manager

        validator = ClaudeTranslationValidator(str(config_path))

        with pytest.raises(TimeoutError):
            validator._poll_until_complete('batch_123')


class TestMapResultsToOrder:
    """Tests for _map_results_to_order method."""

    @patch('src.translation.claude_validator.validator.ClaudeBatchClient')
    @patch('src.translation.claude_validator.validator.CacheManager')
    def test_map_results_to_order_sorts_by_custom_id(self, mock_cache_manager_class, mock_batch_client_class, tmp_path):
        """Verify result ordering by custom_id suffix."""
        config = {
            'claude': {
                'model': 'test-model',
                'max_tokens': 2048,
                'batch': {
                    'enabled': True,
                    'custom_id_prefix': 'validation',
                    'polling_interval_seconds': 1,
                    'max_wait_hours': 1
                },
                'caching': {'enabled': True},
                'system_prompt': 'Test',
                'user_prompt_template': 'Test',
                'validation': {
                    'mode': 'post_translation',
                    'confidence_threshold': 0.85
                }
            }
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        mock_batch_client = MagicMock()
        mock_batch_client_class.return_value = mock_batch_client
        mock_cache_manager = MagicMock()
        mock_cache_manager_class.return_value = mock_cache_manager

        validator = ClaudeTranslationValidator(str(config_path))

        # Create results in reverse order
        results = [
            BatchResult(custom_id='validation_0002', validated_text='Third', confidence_score=0.9, changes_made=False),
            BatchResult(custom_id='validation_0000', validated_text='First', confidence_score=0.9, changes_made=False),
            BatchResult(custom_id='validation_0001', validated_text='Second', confidence_score=0.9, changes_made=False)
        ]

        mapped = validator._map_results_to_order(results, 3)

        assert mapped == ['First', 'Second', 'Third']

    @patch('src.translation.claude_validator.validator.ClaudeBatchClient')
    @patch('src.translation.claude_validator.validator.CacheManager')
    def test_map_results_to_order_raises_on_count_mismatch(self, mock_cache_manager_class, mock_batch_client_class, tmp_path):
        """Verify error on result count mismatch."""
        config = {
            'claude': {
                'model': 'test-model',
                'max_tokens': 2048,
                'batch': {
                    'enabled': True,
                    'custom_id_prefix': 'validation',
                    'polling_interval_seconds': 1,
                    'max_wait_hours': 1
                },
                'caching': {'enabled': True},
                'system_prompt': 'Test',
                'user_prompt_template': 'Test',
                'validation': {
                    'mode': 'post_translation',
                    'confidence_threshold': 0.85
                }
            }
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        mock_batch_client = MagicMock()
        mock_batch_client_class.return_value = mock_batch_client
        mock_cache_manager = MagicMock()
        mock_cache_manager_class.return_value = mock_cache_manager

        validator = ClaudeTranslationValidator(str(config_path))

        results = [
            BatchResult(custom_id='validation_0000', validated_text='Text', confidence_score=0.9, changes_made=False)
        ]

        with pytest.raises(ValueError) as exc_info:
            validator._map_results_to_order(results, 3)

        assert 'Result count mismatch' in str(exc_info.value)


class TestCalculateValidationMetrics:
    """Tests for _calculate_validation_metrics method."""

    @patch('src.translation.claude_validator.validator.ClaudeBatchClient')
    @patch('src.translation.claude_validator.validator.CacheManager')
    def test_calculate_validation_metrics_counts_changes(self, mock_cache_manager_class, mock_batch_client_class, tmp_path):
        """Verify metrics calculation."""
        config = {
            'claude': {
                'model': 'test-model',
                'max_tokens': 2048,
                'batch': {
                    'enabled': True,
                    'custom_id_prefix': 'validation',
                    'polling_interval_seconds': 1,
                    'max_wait_hours': 1
                },
                'caching': {'enabled': True},
                'system_prompt': 'Test',
                'user_prompt_template': 'Test',
                'validation': {
                    'mode': 'post_translation',
                    'confidence_threshold': 0.85
                }
            }
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        mock_batch_client = MagicMock()
        mock_batch_client_class.return_value = mock_batch_client
        mock_cache_manager = MagicMock()
        mock_cache_manager_class.return_value = mock_cache_manager

        validator = ClaudeTranslationValidator(str(config_path))

        original = ['Hello', 'World', 'Test']
        validated = ['Hello', 'World Changed', 'Test']
        results = [
            BatchResult(custom_id='v_0000', validated_text='Hello', confidence_score=0.95, changes_made=False),
            BatchResult(custom_id='v_0001', validated_text='World Changed', confidence_score=0.92, changes_made=True),
            BatchResult(custom_id='v_0002', validated_text='Test', confidence_score=0.95, changes_made=False)
        ]

        metrics = validator._calculate_validation_metrics(original, validated, results)

        assert metrics['total_paragraphs'] == 3
        assert metrics['paragraphs_changed'] == 1
        assert metrics['change_rate_percent'] == 33.33
        assert metrics['avg_confidence'] == round((0.95 + 0.92 + 0.95) / 3, 3)
        assert metrics['errors'] == 0
        assert metrics['success_rate_percent'] == 100.0

    @patch('src.translation.claude_validator.validator.ClaudeBatchClient')
    @patch('src.translation.claude_validator.validator.CacheManager')
    def test_calculate_validation_metrics_with_errors(self, mock_cache_manager_class, mock_batch_client_class, tmp_path):
        """Verify error tracking in metrics."""
        config = {
            'claude': {
                'model': 'test-model',
                'max_tokens': 2048,
                'batch': {
                    'enabled': True,
                    'custom_id_prefix': 'validation',
                    'polling_interval_seconds': 1,
                    'max_wait_hours': 1
                },
                'caching': {'enabled': True},
                'system_prompt': 'Test',
                'user_prompt_template': 'Test',
                'validation': {
                    'mode': 'post_translation',
                    'confidence_threshold': 0.85
                }
            }
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        mock_batch_client = MagicMock()
        mock_batch_client_class.return_value = mock_batch_client
        mock_cache_manager = MagicMock()
        mock_cache_manager_class.return_value = mock_cache_manager

        validator = ClaudeTranslationValidator(str(config_path))

        original = ['Text1', 'Text2']
        validated = ['Text1', '']
        results = [
            BatchResult(custom_id='v_0000', validated_text='Text1', confidence_score=0.95, changes_made=False),
            BatchResult(custom_id='v_0001', validated_text='', confidence_score=0.0, changes_made=False, error='Rate limit')
        ]

        metrics = validator._calculate_validation_metrics(original, validated, results)

        assert metrics['errors'] == 1
        assert metrics['success_rate_percent'] == 50.0


class TestValidationResultIntegration:
    """Tests for complete ValidationResult."""

    @patch('src.translation.claude_validator.validator.ClaudeBatchClient')
    @patch('src.translation.claude_validator.validator.CacheManager')
    def test_validation_result_contains_cache_stats(self, mock_cache_manager_class, mock_batch_client_class, tmp_path):
        """Verify cache stats included in result."""
        config = {
            'claude': {
                'model': 'test-model',
                'max_tokens': 2048,
                'batch': {
                    'enabled': True,
                    'custom_id_prefix': 'validation',
                    'polling_interval_seconds': 1,
                    'max_wait_hours': 1
                },
                'caching': {'enabled': True},
                'system_prompt': 'Test',
                'user_prompt_template': 'Test',
                'validation': {
                    'mode': 'post_translation',
                    'confidence_threshold': 0.85
                }
            }
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        # Mock batch client
        mock_batch_client = MagicMock()
        mock_batch_client.custom_id_prefix = 'validation'
        mock_batch_client.create_batch_job.return_value = 'batch_123'
        mock_batch_client.poll_batch_status.return_value = 'ended'
        mock_batch_client.retrieve_batch_results.return_value = [
            BatchResult(
                custom_id='validation_0000',
                validated_text='Test',
                confidence_score=0.95,
                changes_made=False
            )
        ]
        mock_batch_client_class.return_value = mock_batch_client

        # Mock cache manager with stats
        mock_cache_manager = MagicMock()
        mock_cache_manager.get_cache_stats.return_value = {
            'cache_hits': 10,
            'cache_misses': 1,
            'hit_rate_percent': 90.9,
            'tokens_saved': 5000,
            'cost_saved_usd': 6.75
        }
        mock_cache_manager_class.return_value = mock_cache_manager

        validator = ClaudeTranslationValidator(str(config_path))
        paragraphs = [Paragraph(content='Test', page=1, role='paragraph')]

        result = validator.validate_translations(paragraphs, 'en')

        assert result.cache_stats['cache_hits'] == 10
        assert result.cache_stats['tokens_saved'] == 5000
        assert result.cache_stats['cost_saved_usd'] == 6.75
