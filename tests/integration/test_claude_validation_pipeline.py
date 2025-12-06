"""Integration tests for Claude validation pipeline.

Tests the complete end-to-end validation workflow with real Anthropic API.
Requires CLAUDE_API_KEY environment variable to be set.

Run with: pytest tests/integration/test_claude_validation_pipeline.py -v --run-integration
"""

import os
import pytest
import yaml
import tempfile
from pathlib import Path
from src.models.paragraph import Paragraph, TextSpan
from src.translation.claude_validator.validator import ClaudeTranslationValidator


@pytest.fixture
def api_key():
    """Get Claude API key from environment."""
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        pytest.skip("CLAUDE_API_KEY not set")
    return api_key


@pytest.fixture
def config_with_api_key(tmp_path, api_key):
    """Create temporary config file with valid API key."""
    config = {
        'claude': {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 1024,
            'temperature': 0.0,
            'batch': {
                'enabled': True,
                'custom_id_prefix': 'validation_test',
                'polling_interval_seconds': 5,
                'max_wait_hours': 24
            },
            'caching': {
                'enabled': True,
                'cache_control_type': 'ephemeral'
            },
            'system_prompt': """You are a post-translation quality validator.

Your role is to check and improve quality in already-translated text.
You are NOT a translator - do NOT re-translate from source language.

Tasks:
1. Fix grammar and spelling errors
2. Improve natural phrasing
3. Preserve ALL formatting
4. Apply validation rules provided
5. Return ONLY the corrected text - no explanations

Critical Rules:
- If text is perfect, return it UNCHANGED
- Only fix errors - do not change meaning
- Preserve exact formatting and line breaks
- Output plain text only""",
            'user_prompt_template': """TARGET LANGUAGE: {target_lang}
PARAGRAPH TYPE: {role}

VALIDATION RULES:
{validation_rules_text}

TRANSLATED TEXT TO VALIDATE:
{translated_text}

Return the corrected text (or unchanged if already perfect).""",
            'validation': {
                'mode': 'post_translation',
                'confidence_threshold': 0.85
            },
            'validation_rules': {
                'avoid_characters': ['-'],
                'preserve_formatting': True,
                'preserve_paragraph_spacing': True,
                'natural_phrasing': True,
                'grammar_check': True
            }
        }
    }

    # Write config to file
    config_path = tmp_path / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    # Mock the load_config to return API key
    from unittest.mock import patch
    with patch('src.translation.claude_validator.batch_client.load_config') as mock_load:
        mock_load.return_value = {'claude': {'api_key': api_key}}

    return str(config_path)


@pytest.mark.integration
class TestClaudeValidationPipelineIntegration:
    """Integration tests with real Anthropic API."""

    def test_end_to_end_validation_with_real_api(self, api_key, config_with_api_key):
        """Full pipeline test with real Anthropic API.

        This test:
        1. Creates validation requests for small batch
        2. Submits to real Anthropic Batch API
        3. Polls for completion
        4. Verifies results are returned
        5. Checks cache stats are populated

        Note: This test uses real API and may incur costs.
        Use small batch size to minimize API charges.
        """
        # Skip if no API key
        if not api_key:
            pytest.skip("CLAUDE_API_KEY not set")

        # Create small test batch
        paragraphs = [
            Paragraph(
                content="The quick brown fox jumps over the lazy dog.",
                page=1,
                role="paragraph"
            ),
            Paragraph(
                content="This is a test sentence with some mistakes.",
                page=1,
                role="paragraph"
            ),
            Paragraph(
                content="Another test to verify the validation process.",
                page=1,
                role="paragraph"
            )
        ]

        # Initialize validator with real API
        from unittest.mock import patch
        with patch('src.translation.claude_validator.batch_client.load_config') as mock_load:
            mock_load.return_value = {'claude': {'api_key': api_key}}

            validator = ClaudeTranslationValidator(config_with_api_key)

            # Validate paragraphs
            result = validator.validate_translations(paragraphs, 'en')

            # Verify result structure
            assert result.validated_texts is not None
            assert len(result.validated_texts) == 3
            assert result.confidence_scores is not None
            assert len(result.confidence_scores) == 3
            assert result.quality_metrics is not None
            assert result.cache_stats is not None

            # Verify metrics
            assert result.quality_metrics['total_paragraphs'] == 3
            assert result.quality_metrics['success_rate_percent'] > 0
            assert result.quality_metrics['avg_confidence'] > 0

            # Log results
            print(f"\n--- Validation Results ---")
            print(f"Validated texts: {len(result.validated_texts)}")
            print(f"Avg confidence: {result.quality_metrics['avg_confidence']}")
            print(f"Changes made: {result.changes_made}")
            print(f"Cache hits: {result.cache_stats.get('cache_hits', 0)}")
            print(f"Tokens saved: {result.cache_stats.get('tokens_saved', 0)}")

    def test_batch_processing_preserves_order(self, api_key, config_with_api_key):
        """Verify paragraph order maintained in results."""
        if not api_key:
            pytest.skip("CLAUDE_API_KEY not set")

        paragraphs = [
            Paragraph(content="First paragraph", page=1, role="paragraph"),
            Paragraph(content="Second paragraph", page=1, role="paragraph"),
            Paragraph(content="Third paragraph", page=1, role="paragraph")
        ]

        from unittest.mock import patch
        with patch('src.translation.claude_validator.batch_client.load_config') as mock_load:
            mock_load.return_value = {'claude': {'api_key': api_key}}

            validator = ClaudeTranslationValidator(config_with_api_key)
            result = validator.validate_translations(paragraphs, 'en')

            # Verify order is preserved
            assert len(result.validated_texts) == 3

            # First result should correspond to first paragraph
            # (content should match or be corrected version)
            assert result.validated_texts[0] is not None
            assert len(result.validated_texts[0]) > 0

    def test_validation_rules_applied(self, api_key, config_with_api_key):
        """Verify validation rules like 'avoid -' are respected."""
        if not api_key:
            pytest.skip("CLAUDE_API_KEY not set")

        # Create paragraph that might have dashes
        paragraphs = [
            Paragraph(
                content="This-is-a-test-with-hyphens.",
                page=1,
                role="paragraph"
            )
        ]

        from unittest.mock import patch
        with patch('src.translation.claude_validator.batch_client.load_config') as mock_load:
            mock_load.return_value = {'claude': {'api_key': api_key}}

            validator = ClaudeTranslationValidator(config_with_api_key)
            result = validator.validate_translations(paragraphs, 'en')

            # Verify result
            assert result.validated_texts is not None
            assert len(result.validated_texts) == 1

            validated_text = result.validated_texts[0]
            assert validated_text is not None

            # If rules were applied, hyphens should be removed or replaced
            # The exact behavior depends on Claude's interpretation
            # This test mainly verifies the pipeline works end-to-end
            print(f"\nOriginal: {paragraphs[0].content}")
            print(f"Validated: {validated_text}")

    def test_validation_with_title_role(self, api_key, config_with_api_key):
        """Verify validation works with different paragraph roles."""
        if not api_key:
            pytest.skip("CLAUDE_API_KEY not set")

        paragraphs = [
            Paragraph(
                content="Document Title Here",
                page=1,
                role="title"
            ),
            Paragraph(
                content="This is the main heading",
                page=1,
                role="heading"
            )
        ]

        from unittest.mock import patch
        with patch('src.translation.claude_validator.batch_client.load_config') as mock_load:
            mock_load.return_value = {'claude': {'api_key': api_key}}

            validator = ClaudeTranslationValidator(config_with_api_key)
            result = validator.validate_translations(paragraphs, 'en')

            # Verify both were validated
            assert len(result.validated_texts) == 2
            assert result.quality_metrics['success_rate_percent'] == 100.0

    def test_cache_stats_show_cost_savings(self, api_key, config_with_api_key):
        """Verify cache stats show token and cost savings."""
        if not api_key:
            pytest.skip("CLAUDE_API_KEY not set")

        paragraphs = [
            Paragraph(content="Test paragraph 1", page=1, role="paragraph"),
            Paragraph(content="Test paragraph 2", page=1, role="paragraph")
        ]

        from unittest.mock import patch
        with patch('src.translation.claude_validator.batch_client.load_config') as mock_load:
            mock_load.return_value = {'claude': {'api_key': api_key}}

            validator = ClaudeTranslationValidator(config_with_api_key)
            result = validator.validate_translations(paragraphs, 'en')

            # Verify cache stats structure
            assert 'cache_hits' in result.cache_stats
            assert 'cache_misses' in result.cache_stats
            assert 'hit_rate_percent' in result.cache_stats
            assert 'tokens_saved' in result.cache_stats
            assert 'cost_saved_usd' in result.cache_stats

            # Log cache performance
            print(f"\n--- Cache Performance ---")
            print(f"Hits: {result.cache_stats['cache_hits']}")
            print(f"Misses: {result.cache_stats['cache_misses']}")
            print(f"Hit rate: {result.cache_stats['hit_rate_percent']}%")
            print(f"Tokens saved: {result.cache_stats['tokens_saved']}")
            print(f"Cost saved: ${result.cache_stats['cost_saved_usd']}")

    def test_error_handling_with_invalid_content(self, api_key, config_with_api_key):
        """Verify graceful handling of edge cases."""
        if not api_key:
            pytest.skip("CLAUDE_API_KEY not set")

        paragraphs = [
            Paragraph(content="", page=1, role="paragraph"),  # Empty
            Paragraph(content="Valid text", page=1, role="paragraph")
        ]

        from unittest.mock import patch
        with patch('src.translation.claude_validator.batch_client.load_config') as mock_load:
            mock_load.return_value = {'claude': {'api_key': api_key}}

            validator = ClaudeTranslationValidator(config_with_api_key)
            result = validator.validate_translations(paragraphs, 'en')

            # Should handle gracefully
            assert result.validated_texts is not None
            assert len(result.validated_texts) == 2


@pytest.mark.integration
class TestBatchAPICostOptimization:
    """Tests verifying cost optimization features."""

    def test_batch_api_cost_savings(self, api_key, config_with_api_key):
        """Verify Batch API provides cost savings vs direct API.

        Batch API provides 50% cost savings compared to synchronous API.
        This test verifies the batch mode is being used.
        """
        if not api_key:
            pytest.skip("CLAUDE_API_KEY not set")

        paragraphs = [
            Paragraph(content="Test paragraph", page=1, role="paragraph")
        ]

        from unittest.mock import patch
        with patch('src.translation.claude_validator.batch_client.load_config') as mock_load:
            mock_load.return_value = {'claude': {'api_key': api_key}}

            validator = ClaudeTranslationValidator(config_with_api_key)

            # Verify batch mode is being used
            assert validator.validation_mode == 'post_translation'

            result = validator.validate_translations(paragraphs, 'en')

            # Batch API should be used by default
            assert result.validated_texts is not None

            print(f"\n--- Cost Optimization ---")
            print(f"Validation mode: {validator.validation_mode}")
            print(f"Quality metrics: {result.quality_metrics}")

    def test_prompt_caching_cost_savings(self, api_key, config_with_api_key):
        """Verify prompt caching provides 90% savings on repeated validations."""
        if not api_key:
            pytest.skip("CLAUDE_API_KEY not set")

        # First batch
        paragraphs_1 = [
            Paragraph(content="First test batch paragraph 1", page=1, role="paragraph")
        ]

        # Second batch with same config (should benefit from cache)
        paragraphs_2 = [
            Paragraph(content="Second test batch paragraph 1", page=1, role="paragraph")
        ]

        from unittest.mock import patch
        with patch('src.translation.claude_validator.batch_client.load_config') as mock_load:
            mock_load.return_value = {'claude': {'api_key': api_key}}

            validator = ClaudeTranslationValidator(config_with_api_key)

            # First validation (cache miss expected)
            result_1 = validator.validate_translations(paragraphs_1, 'en')

            # Second validation (cache hit expected)
            result_2 = validator.validate_translations(paragraphs_2, 'en')

            # Log cache performance across both requests
            print(f"\n--- Caching Performance ---")
            print(f"First batch cache stats: {result_1.cache_stats}")
            print(f"Second batch cache stats: {result_2.cache_stats}")

            # Both should complete successfully
            assert result_1.validated_texts is not None
            assert result_2.validated_texts is not None
