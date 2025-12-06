"""
Prompt caching manager for Claude API cost optimization.

Manages ephemeral caching of system prompts to achieve 90% cost savings
on repeated validations.
"""

import logging
from typing import Dict, Any

from src.logger import get_logger


class CacheManager:
    """Manages prompt caching for cost optimization."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize cache manager with caching config.

        Args:
            config: Caching configuration dict from config.yaml
        """
        self.enabled = config.get('enabled', True)
        self.cache_control_type = config.get('cache_control_type', 'ephemeral')

        # Cache statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.tokens_saved = 0

        self.logger = get_logger('EmailReader.Translation.CacheManager')

    def apply_cache_directive(
        self,
        system_prompt: str
    ) -> Dict[str, Any]:
        """
        Apply cache_control directive to system prompt.

        Args:
            system_prompt: The system prompt text to cache

        Returns:
            Formatted message block with caching directive

        Example:
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "System prompt...",
                        "cache_control": {"type": "ephemeral"}
                    }
                ]
            }
        """
        if not self.enabled:
            return {
                "role": "system",
                "content": system_prompt
            }

        return {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": self.cache_control_type}
                }
            ]
        }

    def log_cache_statistics(
        self,
        response_usage: Dict[str, int]
    ) -> None:
        """
        Track cache performance from API response.

        Args:
            response_usage: Usage statistics from Claude API response
                {
                    'input_tokens': 1000,
                    'cache_creation_input_tokens': 500,  # First request
                    'cache_read_input_tokens': 0         # Subsequent requests
                }
        """
        if 'cache_read_input_tokens' in response_usage:
            tokens_read = response_usage['cache_read_input_tokens']
            if tokens_read > 0:
                self.cache_hits += 1
                self.tokens_saved += tokens_read
                self.logger.info(
                    f"[CacheManager] Cache HIT: {tokens_read} tokens saved"
                )

        if 'cache_creation_input_tokens' in response_usage:
            self.cache_misses += 1
            tokens_created = response_usage['cache_creation_input_tokens']
            self.logger.info(
                f"[CacheManager] Cache MISS: {tokens_created} tokens cached for reuse"
            )

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Return cache performance metrics.

        Returns:
            Dictionary with cache statistics:
                - cache_hits: Number of cache hits
                - cache_misses: Number of cache misses
                - hit_rate_percent: Cache hit rate as percentage
                - tokens_saved: Total tokens saved via caching
                - cost_saved_usd: Estimated cost savings in USD
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        # Batch API pricing: $1.50 per M input tokens
        # Cache read discount: 90% (pay 10% of full price = $0.15 per M tokens)
        # Savings = tokens_saved * ($1.50 - $0.15) / 1M = tokens_saved * $1.35 / 1M
        cost_saved = self.tokens_saved * 1.35 / 1_000_000

        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate_percent': round(hit_rate, 2),
            'tokens_saved': self.tokens_saved,
            'cost_saved_usd': round(cost_saved, 4)
        }
