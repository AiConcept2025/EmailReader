"""
Main Claude Sonnet 4.5 translation validator orchestrator.

Coordinates batch validation workflow with prompt caching for cost optimization.
Integrates with GoogleBatchTranslator for post-translation quality checking.
"""

import time
import yaml
from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path

from src.models.paragraph import Paragraph
from src.translation.claude_validator.batch_client import (
    ClaudeBatchClient,
    BatchRequest,
    BatchResult
)
from src.translation.claude_validator.cache_manager import CacheManager
from src.logger import get_logger


@dataclass
class ValidationResult:
    """Validation result container."""
    validated_texts: List[str]
    confidence_scores: List[float]
    changes_made: int
    quality_metrics: Dict[str, Any]
    cache_stats: Dict[str, Any]


class ClaudeTranslationValidator:
    """
    Main validator coordinating batch validation with caching.

    Integrates with GoogleBatchTranslator post-translation for quality checking.
    Uses Anthropic Batch API (50% cost savings) with prompt caching (90% savings).
    """

    def __init__(self, config_path: str):
        """
        Initialize validator with YAML config.

        Args:
            config_path: Path to config.yaml

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_path_obj = Path(config_path)
        if not config_path_obj.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.claude_config = self.config['claude']

        # Initialize components
        self.batch_client = ClaudeBatchClient(self.claude_config)
        self.cache_manager = CacheManager(self.claude_config['caching'])

        # Settings
        self.validation_mode = self.claude_config['validation']['mode']
        self.confidence_threshold = self.claude_config['validation']['confidence_threshold']

        self.logger = get_logger('EmailReader.Translation.ClaudeValidator')

    def validate_translations(
        self,
        translated_paragraphs: List[Paragraph],
        target_lang: str,
        use_batch: bool = True
    ) -> ValidationResult:
        """
        Validate translated paragraphs using Claude Sonnet 4.5 (post-translation quality check).

        Args:
            translated_paragraphs: Paragraph objects with Google-translated content
            target_lang: Target language code (e.g., 'en')
            use_batch: Use batch API (default) or individual API calls

        Returns:
            ValidationResult with validated texts and metrics

        Workflow:
            1. Create BatchRequest objects from translated paragraphs (NO source text)
            2. Submit batch job to Claude API
            3. Poll for completion (up to 24 hours)
            4. Retrieve validated results (grammar/format fixes only)
            5. Map back to paragraph order
            6. Log metrics (token usage, cache performance, changes)
        """
        self.logger.info(
            f"[ClaudeValidator] Validating {len(translated_paragraphs)} paragraphs "
            f"(target language: {target_lang})"
        )

        if use_batch:
            return self._validate_batch(translated_paragraphs, target_lang)
        else:
            return self._validate_individual(translated_paragraphs, target_lang)

    def _validate_batch(
        self,
        translated_paragraphs: List[Paragraph],
        target_lang: str
    ) -> ValidationResult:
        """
        Execute batch validation workflow (post-translation quality check).

        Args:
            translated_paragraphs: Paragraph objects with translated content
            target_lang: Target language code

        Returns:
            ValidationResult with validated texts and metrics
        """
        # Step 1: Create batch requests (NO source text - only translated text + rules)
        requests = []
        for i, para in enumerate(translated_paragraphs):
            request = BatchRequest(
                custom_id=f"{self.batch_client.custom_id_prefix}_{i:04d}",
                translated_text=para.content,  # Google-translated content
                target_lang=target_lang,
                role=para.role,
                validation_rules=self.claude_config.get('validation_rules', {})
            )
            requests.append(request)

        self.logger.info(f"[ClaudeValidator] Created {len(requests)} batch requests")

        # Step 2: Submit batch job
        batch_id = self.batch_client.create_batch_job(requests)
        self.logger.info(f"[ClaudeValidator] Batch job created: {batch_id}")

        # Step 3: Poll for completion
        status = self._poll_until_complete(batch_id)

        if status != 'ended':
            raise RuntimeError(f"Batch job failed with status: {status}")

        # Step 4: Retrieve results
        results = self.batch_client.retrieve_batch_results(batch_id)

        # Step 5: Map back to paragraph order
        validated_texts = self._map_results_to_order(results, len(translated_paragraphs))

        # Step 6: Calculate metrics
        original_texts = [para.content for para in translated_paragraphs]
        metrics = self._calculate_validation_metrics(
            original_texts, validated_texts, results
        )

        self.logger.info(f"[ClaudeValidator] Validation complete: {metrics}")

        return ValidationResult(
            validated_texts=validated_texts,
            confidence_scores=[r.confidence_score for r in results],
            changes_made=sum(1 for r in results if r.changes_made),
            quality_metrics=metrics,
            cache_stats=self.cache_manager.get_cache_stats()
        )

    def _validate_individual(
        self,
        translated_paragraphs: List[Paragraph],
        target_lang: str
    ) -> ValidationResult:
        """
        Execute individual API calls (fallback mode).

        Note: This is a fallback implementation. Batch mode is preferred
        for cost optimization (50% savings).

        Args:
            translated_paragraphs: Paragraph objects with translated content
            target_lang: Target language code

        Returns:
            ValidationResult with validated texts and metrics
        """
        # TODO: Implement individual validation mode if needed
        # For now, raise NotImplementedError as batch mode is the primary implementation
        raise NotImplementedError(
            "Individual validation mode not yet implemented. "
            "Please use batch mode (use_batch=True)"
        )

    def _poll_until_complete(self, batch_id: str) -> str:
        """
        Poll batch status until completion.

        Args:
            batch_id: Anthropic batch job ID

        Returns:
            Final status: "ended" | "failed" | "expired"

        Raises:
            TimeoutError: If batch exceeds max wait time
        """
        max_wait_seconds = self.claude_config['batch'].get('max_wait_hours', 24) * 3600
        polling_interval = self.claude_config['batch']['polling_interval_seconds']

        elapsed = 0
        while elapsed < max_wait_seconds:
            status = self.batch_client.poll_batch_status(batch_id)

            if status in ['ended', 'failed', 'expired']:
                self.logger.info(
                    f"[ClaudeValidator] Batch {batch_id} completed with status: {status}"
                )
                return status

            self.logger.debug(
                f"[ClaudeValidator] Batch {batch_id} status: {status}, "
                f"waiting {polling_interval}s... (elapsed: {elapsed}s)"
            )

            time.sleep(polling_interval)
            elapsed += polling_interval

        raise TimeoutError(
            f"Batch job {batch_id} exceeded max wait time ({max_wait_seconds}s)"
        )

    def _map_results_to_order(
        self,
        results: List[BatchResult],
        expected_count: int
    ) -> List[str]:
        """
        Map batch results back to original paragraph order.

        Args:
            results: List of batch results (may be unordered)
            expected_count: Expected number of results

        Returns:
            List of validated texts in original paragraph order

        Raises:
            ValueError: If result count doesn't match expected count
        """
        # Sort by custom_id suffix (e.g., validation_0001 → index 1)
        sorted_results = sorted(
            results,
            key=lambda r: int(r.custom_id.split('_')[-1])
        )

        validated_texts = [r.validated_text for r in sorted_results]

        if len(validated_texts) != expected_count:
            self.logger.warning(
                f"[ClaudeValidator] Expected {expected_count} results, "
                f"got {len(validated_texts)}"
            )
            raise ValueError(
                f"Result count mismatch: expected {expected_count}, got {len(validated_texts)}"
            )

        return validated_texts

    def _calculate_validation_metrics(
        self,
        original_texts: List[str],
        validated_texts: List[str],
        results: List[BatchResult]
    ) -> Dict[str, Any]:
        """
        Calculate quality metrics.

        Args:
            original_texts: Original translated texts (from Google)
            validated_texts: Validated texts (from Claude)
            results: Batch results with metadata

        Returns:
            Dictionary with quality metrics
        """
        total = len(results)
        changes = sum(1 for r in results if r.changes_made)
        avg_confidence = sum(r.confidence_score for r in results) / total if total > 0 else 0
        errors = sum(1 for r in results if r.error is not None)

        # Calculate actual text changes (comparing original vs validated)
        actual_changes = sum(
            1 for orig, val in zip(original_texts, validated_texts)
            if orig.strip() != val.strip()
        )

        return {
            'total_paragraphs': total,
            'paragraphs_changed': actual_changes,
            'change_rate_percent': round(actual_changes / total * 100, 2) if total > 0 else 0,
            'avg_confidence': round(avg_confidence, 3),
            'errors': errors,
            'success_rate_percent': round((total - errors) / total * 100, 2) if total > 0 else 0
        }
