"""
Claude Sonnet 4.5 Post-Translation Quality Validator.

This package provides cost-optimized translation quality validation using:
- Anthropic Batch API (50% cost savings)
- Prompt caching (90% savings on repeated prompts)
- Post-translation quality checking (grammar/format/style)
"""

from src.translation.claude_validator.validator import ClaudeTranslationValidator, ValidationResult
from src.translation.claude_validator.batch_client import ClaudeBatchClient, BatchRequest, BatchResult
from src.translation.claude_validator.cache_manager import CacheManager

__all__ = [
    'ClaudeTranslationValidator',
    'ValidationResult',
    'ClaudeBatchClient',
    'BatchRequest',
    'BatchResult',
    'CacheManager',
]
