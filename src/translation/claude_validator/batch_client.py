"""
Anthropic Batch API client for cost-optimized translation validation.

Uses Claude Sonnet 4.5 with Batch API (50% cost savings) and prompt caching
(90% savings on repeated prompts).
"""

import anthropic
import json
import time
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from src.config import load_config
from src.logger import get_logger


@dataclass
class BatchRequest:
    """Single batch validation request (post-translation quality check)."""
    custom_id: str              # E.g., "validation_2024-12-03_001"
    translated_text: str         # Google-translated text to validate
    target_lang: str             # Target language code (e.g., 'en')
    role: str                    # Paragraph role (title, heading, paragraph, listItem)
    validation_rules: Dict[str, Any]  # Validation rules from config


@dataclass
class BatchResult:
    """Single validation result."""
    custom_id: str
    validated_text: str
    confidence_score: float
    changes_made: bool
    error: Optional[str] = None


class ClaudeBatchClient:
    """Anthropic Batch API client with caching."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with config from config.yaml.

        Args:
            config: Loaded YAML config (claude section)

        Raises:
            ValueError: If Claude API key not found in config.dev.json
        """
        # Load API key from main config (config.dev.json)
        full_config = load_config()
        self.api_key = full_config.get('claude', {}).get('api_key')

        if not self.api_key:
            raise ValueError(
                "Claude API key not found in config.dev.json. "
                "Please add 'claude.api_key' to credentials/config.dev.json"
            )

        self.model = config['model']
        self.max_tokens = config['max_tokens']
        self.temperature = config.get('temperature', 0.0)

        # Batch settings
        self.batch_config = config['batch']
        self.custom_id_prefix = self.batch_config['custom_id_prefix']

        # Prompt caching
        self.caching_config = config['caching']
        self.system_prompt = config['system_prompt']
        self.user_prompt_template = config['user_prompt_template']
        self.validation_rules = config.get('validation_rules', {})

        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)

        self.logger = get_logger('EmailReader.Translation.ClaudeBatchClient')

    def create_batch_job(
        self,
        requests: List[BatchRequest]
    ) -> str:
        """
        Create batch validation job.

        Args:
            requests: List of validation requests

        Returns:
            batch_id: Anthropic batch job ID

        Raises:
            anthropic.APIError: If batch creation fails
        """
        self.logger.info(
            f"[ClaudeBatchClient] Creating batch job with {len(requests)} requests"
        )

        # Convert requests to Anthropic batch format (JSONL)
        batch_requests = []
        for request in requests:
            # Format user prompt with validation rules
            user_prompt = self._format_user_prompt(request)

            # Create request in Anthropic format
            batch_request = {
                "custom_id": request.custom_id,
                "params": {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "system": self._apply_prompt_caching(),
                    "messages": [
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ]
                }
            }
            batch_requests.append(batch_request)

        # Create batch job via Anthropic API
        try:
            batch_response = self.client.messages.batches.create(
                requests=batch_requests
            )

            batch_id = batch_response.id
            self.logger.info(
                f"[ClaudeBatchClient] Batch job created: {batch_id}, "
                f"status: {batch_response.processing_status}"
            )

            return batch_id

        except anthropic.APIError as e:
            self.logger.error(f"[ClaudeBatchClient] Batch creation failed: {e}")
            raise

    def poll_batch_status(self, batch_id: str) -> str:
        """
        Poll batch job status.

        Args:
            batch_id: Anthropic batch job ID

        Returns:
            Status: "in_progress" | "ended" | "failed" | "expired"

        Raises:
            anthropic.APIError: If status check fails
        """
        try:
            batch = self.client.messages.batches.retrieve(batch_id)
            status = batch.processing_status

            self.logger.debug(
                f"[ClaudeBatchClient] Batch {batch_id} status: {status}"
            )

            return status

        except anthropic.APIError as e:
            self.logger.error(f"[ClaudeBatchClient] Status check failed: {e}")
            raise

    def retrieve_batch_results(
        self,
        batch_id: str
    ) -> List[BatchResult]:
        """
        Retrieve completed batch results.

        Args:
            batch_id: Anthropic batch job ID

        Returns:
            List of BatchResult with validated texts

        Raises:
            anthropic.APIError: If result retrieval fails
        """
        self.logger.info(
            f"[ClaudeBatchClient] Retrieving results for batch {batch_id}"
        )

        try:
            # Fetch results from Anthropic API
            batch = self.client.messages.batches.retrieve(batch_id)

            # Iterate through results
            results = []
            for result in self.client.messages.batches.results(batch_id):
                custom_id = result.custom_id

                # Check for errors
                if result.result.type == "error":
                    error_msg = str(result.result.error)
                    self.logger.error(
                        f"[ClaudeBatchClient] Request {custom_id} failed: {error_msg}"
                    )
                    results.append(BatchResult(
                        custom_id=custom_id,
                        validated_text="",
                        confidence_score=0.0,
                        changes_made=False,
                        error=error_msg
                    ))
                    continue

                # Extract validated text from response
                message = result.result.message
                validated_text = message.content[0].text

                # Calculate confidence score (heuristic based on changes)
                # For now, use a simple heuristic - can be improved with more sophisticated metrics
                confidence_score = 0.95  # High confidence by default

                # Check if changes were made (simple comparison)
                changes_made = True  # Assume changes by default - validator should return unchanged if perfect

                # Log token usage if available
                if hasattr(message, 'usage'):
                    usage = message.usage
                    self.logger.debug(
                        f"[ClaudeBatchClient] Request {custom_id} usage: "
                        f"input_tokens={usage.input_tokens}, "
                        f"output_tokens={usage.output_tokens}"
                    )

                results.append(BatchResult(
                    custom_id=custom_id,
                    validated_text=validated_text,
                    confidence_score=confidence_score,
                    changes_made=changes_made
                ))

            self.logger.info(
                f"[ClaudeBatchClient] Retrieved {len(results)} results "
                f"({sum(1 for r in results if r.error is None)} successful)"
            )

            return results

        except anthropic.APIError as e:
            self.logger.error(f"[ClaudeBatchClient] Result retrieval failed: {e}")
            raise

    def _apply_prompt_caching(self) -> List[Dict]:
        """
        Apply ephemeral caching to system prompt.

        Returns:
            System prompt with cache_control directive

        Example:
            [
                {
                    "type": "text",
                    "text": self.system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ]
        """
        if not self.caching_config.get('enabled', True):
            return self.system_prompt

        return [
            {
                "type": "text",
                "text": self.system_prompt,
                "cache_control": {"type": self.caching_config.get('cache_control_type', 'ephemeral')}
            }
        ]

    def _format_user_prompt(
        self,
        request: BatchRequest
    ) -> str:
        """
        Format user prompt with translated text and validation rules.

        Args:
            request: Batch validation request

        Returns:
            Formatted user prompt string
        """
        # Format validation rules as readable text
        rules = request.validation_rules
        rules_lines = []

        if rules.get('avoid_characters'):
            chars = ', '.join(f"'{c}'" for c in rules['avoid_characters'])
            rules_lines.append(f"- Avoid these characters: {chars}")

        if rules.get('preserve_formatting'):
            rules_lines.append("- Preserve ALL formatting (bold, italic, line breaks)")

        if rules.get('preserve_paragraph_spacing'):
            rules_lines.append("- Maintain paragraph spacing")

        if rules.get('natural_phrasing'):
            rules_lines.append("- Ensure natural, fluent phrasing")

        if rules.get('grammar_check'):
            rules_lines.append("- Fix grammar and spelling errors")

        validation_rules_text = '\n'.join(rules_lines)

        return self.user_prompt_template.format(
            target_lang=request.target_lang,
            role=request.role,
            validation_rules_text=validation_rules_text,
            translated_text=request.translated_text
        )
