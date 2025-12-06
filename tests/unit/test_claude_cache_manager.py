"""Unit tests for Claude cache manager.

Tests the CacheManager class for prompt caching functionality and cost optimization.
"""

import pytest
from unittest.mock import Mock, patch
from src.translation.claude_validator.cache_manager import CacheManager


class TestCacheManagerInitialization:
    """Tests for CacheManager initialization."""

    def test_initialization_with_caching_enabled(self):
        """Verify cache manager initializes with caching enabled."""
        config = {
            'enabled': True,
            'cache_control_type': 'ephemeral'
        }
        manager = CacheManager(config)

        assert manager.enabled is True
        assert manager.cache_control_type == 'ephemeral'
        assert manager.cache_hits == 0
        assert manager.cache_misses == 0
        assert manager.tokens_saved == 0

    def test_initialization_with_caching_disabled(self):
        """Verify cache manager initializes with caching disabled."""
        config = {
            'enabled': False,
            'cache_control_type': 'ephemeral'
        }
        manager = CacheManager(config)

        assert manager.enabled is False
        assert manager.cache_control_type == 'ephemeral'

    def test_initialization_with_default_values(self):
        """Verify cache manager uses defaults for missing config keys."""
        config = {}
        manager = CacheManager(config)

        assert manager.enabled is True  # Default enabled
        assert manager.cache_control_type == 'ephemeral'  # Default

    def test_initialization_with_custom_cache_control_type(self):
        """Verify cache control type is configurable."""
        config = {
            'enabled': True,
            'cache_control_type': 'permanent'
        }
        manager = CacheManager(config)

        assert manager.cache_control_type == 'permanent'


class TestApplyCacheDirective:
    """Tests for apply_cache_directive method."""

    def test_apply_cache_directive_when_enabled(self):
        """Verify cache_control directive is added when caching enabled."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        system_prompt = "You are a helpful assistant."
        result = manager.apply_cache_directive(system_prompt)

        # Verify structure
        assert result['role'] == 'system'
        assert isinstance(result['content'], list)
        assert len(result['content']) == 1

        # Verify content block
        content_block = result['content'][0]
        assert content_block['type'] == 'text'
        assert content_block['text'] == system_prompt
        assert 'cache_control' in content_block
        assert content_block['cache_control']['type'] == 'ephemeral'

    def test_apply_cache_directive_when_disabled(self):
        """Verify plain format when caching disabled."""
        config = {'enabled': False, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        system_prompt = "You are a helpful assistant."
        result = manager.apply_cache_directive(system_prompt)

        # Verify plain format (no content array)
        assert result['role'] == 'system'
        assert result['content'] == system_prompt
        assert not isinstance(result['content'], list)

    def test_apply_cache_directive_with_multiline_prompt(self):
        """Verify cache directive works with multiline prompts."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        system_prompt = """You are a validator.

        Your job is to:
        1. Check grammar
        2. Fix formatting"""

        result = manager.apply_cache_directive(system_prompt)

        assert result['content'][0]['text'] == system_prompt
        assert 'cache_control' in result['content'][0]

    def test_apply_cache_directive_with_custom_cache_type(self):
        """Verify custom cache control type is applied."""
        config = {'enabled': True, 'cache_control_type': 'permanent'}
        manager = CacheManager(config)

        system_prompt = "Test prompt"
        result = manager.apply_cache_directive(system_prompt)

        assert result['content'][0]['cache_control']['type'] == 'permanent'


class TestLogCacheStatistics:
    """Tests for log_cache_statistics method."""

    def test_log_cache_statistics_tracks_hits(self):
        """Verify cache hit tracking from response_usage."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        # Simulate cache hit response
        response_usage = {
            'input_tokens': 1000,
            'cache_read_input_tokens': 500
        }

        manager.log_cache_statistics(response_usage)

        assert manager.cache_hits == 1
        assert manager.tokens_saved == 500
        assert manager.cache_misses == 0

    def test_log_cache_statistics_tracks_misses(self):
        """Verify cache miss tracking."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        # Simulate cache miss (creation) response
        response_usage = {
            'input_tokens': 1000,
            'cache_creation_input_tokens': 1000
        }

        manager.log_cache_statistics(response_usage)

        assert manager.cache_misses == 1
        assert manager.cache_hits == 0

    def test_log_cache_statistics_multiple_hits_and_misses(self):
        """Verify tracking of multiple cache operations."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        # First request - cache miss
        manager.log_cache_statistics({'cache_creation_input_tokens': 1000})

        # Second request - cache hit
        manager.log_cache_statistics({'cache_read_input_tokens': 1000})

        # Third request - cache hit
        manager.log_cache_statistics({'cache_read_input_tokens': 1000})

        assert manager.cache_misses == 1
        assert manager.cache_hits == 2
        assert manager.tokens_saved == 2000

    def test_log_cache_statistics_zero_cache_read_tokens(self):
        """Verify no hit is recorded when cache_read_input_tokens is 0."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        response_usage = {
            'input_tokens': 1000,
            'cache_read_input_tokens': 0
        }

        manager.log_cache_statistics(response_usage)

        # No hit recorded for 0 tokens
        assert manager.cache_hits == 0
        assert manager.tokens_saved == 0

    def test_log_cache_statistics_missing_keys(self):
        """Verify graceful handling of missing response keys."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        # Response with no cache info
        response_usage = {'input_tokens': 1000}

        # Should not raise error
        manager.log_cache_statistics(response_usage)

        assert manager.cache_hits == 0
        assert manager.cache_misses == 0


class TestGetCacheStats:
    """Tests for get_cache_stats method."""

    def test_get_cache_stats_calculates_hit_rate(self):
        """Verify cache statistics calculation (hit rate)."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        # Simulate 3 requests: 1 miss, 2 hits
        manager.log_cache_statistics({'cache_creation_input_tokens': 1000})
        manager.log_cache_statistics({'cache_read_input_tokens': 500})
        manager.log_cache_statistics({'cache_read_input_tokens': 500})

        stats = manager.get_cache_stats()

        assert stats['cache_hits'] == 2
        assert stats['cache_misses'] == 1
        assert stats['hit_rate_percent'] == 66.67  # 2/3 = 66.67%

    def test_get_cache_stats_calculates_tokens_saved(self):
        """Verify tokens_saved is correctly reported."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        manager.log_cache_statistics({'cache_read_input_tokens': 1000})
        manager.log_cache_statistics({'cache_read_input_tokens': 500})

        stats = manager.get_cache_stats()

        assert stats['tokens_saved'] == 1500

    def test_get_cache_stats_calculates_cost_saved(self):
        """Verify cost savings calculated correctly."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        # 1,000 tokens saved
        # Cost formula: tokens_saved * $1.35 / 1_000_000
        manager.log_cache_statistics({'cache_read_input_tokens': 1_000_000})

        stats = manager.get_cache_stats()

        # Expected: 1_000_000 * 1.35 / 1_000_000 = $1.35
        assert stats['cost_saved_usd'] == 1.35

    def test_get_cache_stats_cost_rounding(self):
        """Verify cost savings are properly rounded."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        # Use tokens that result in non-round cost
        manager.log_cache_statistics({'cache_read_input_tokens': 12345})

        stats = manager.get_cache_stats()

        # Expected: 12345 * 1.35 / 1_000_000 = 0.0166575 -> rounded to 0.0167
        expected_cost = round(12345 * 1.35 / 1_000_000, 4)
        assert stats['cost_saved_usd'] == expected_cost

    def test_get_cache_stats_zero_requests(self):
        """Verify handling with no requests (avoid division by zero)."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        stats = manager.get_cache_stats()

        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0
        assert stats['hit_rate_percent'] == 0
        assert stats['tokens_saved'] == 0
        assert stats['cost_saved_usd'] == 0.0

    def test_get_cache_stats_returns_all_keys(self):
        """Verify all expected keys are in stats dict."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        manager.log_cache_statistics({'cache_creation_input_tokens': 100})

        stats = manager.get_cache_stats()

        expected_keys = {
            'cache_hits',
            'cache_misses',
            'hit_rate_percent',
            'tokens_saved',
            'cost_saved_usd'
        }
        assert set(stats.keys()) == expected_keys

    def test_get_cache_stats_100_percent_hit_rate(self):
        """Verify hit rate calculation at 100%."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        # All hits, no misses
        manager.log_cache_statistics({'cache_read_input_tokens': 100})
        manager.log_cache_statistics({'cache_read_input_tokens': 100})
        manager.log_cache_statistics({'cache_read_input_tokens': 100})

        stats = manager.get_cache_stats()

        assert stats['cache_hits'] == 3
        assert stats['cache_misses'] == 0
        assert stats['hit_rate_percent'] == 100.0

    def test_get_cache_stats_zero_percent_hit_rate(self):
        """Verify hit rate calculation at 0%."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        # All misses, no hits
        manager.log_cache_statistics({'cache_creation_input_tokens': 100})
        manager.log_cache_statistics({'cache_creation_input_tokens': 100})

        stats = manager.get_cache_stats()

        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 2
        assert stats['hit_rate_percent'] == 0.0

    def test_get_cache_stats_batching_pricing_formula(self):
        """Verify Batch API pricing formula is correct."""
        config = {'enabled': True, 'cache_control_type': 'ephemeral'}
        manager = CacheManager(config)

        # Batch API pricing:
        # Input: $1.50 per M tokens
        # Cache read: $0.15 per M tokens (90% discount)
        # Savings: $1.50 - $0.15 = $1.35 per M tokens

        # 1 million tokens saved
        manager.log_cache_statistics({'cache_read_input_tokens': 1_000_000})

        stats = manager.get_cache_stats()

        assert stats['cost_saved_usd'] == 1.35  # $1.35 per M tokens
