"""
Google Text Translator

Wraps the existing GoogleTranslator subprocess-based translation.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any

from src.translation.base_translator import BaseTranslator

logger = logging.getLogger('EmailReader.Translation.GoogleText')


class GoogleTextTranslator(BaseTranslator):
    """
    Google Text Translator using subprocess.

    Wraps the existing translate_document executable that uses
    the GoogleTranslator package.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Google Text translator.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # Get executable path (default to translate_document in project root)
        self.executable_path = config.get(
            'executable_path',
            os.path.join(os.getcwd(), 'translate_document')
        )

        logger.info("Initialized GoogleTextTranslator")
        logger.debug("Executable path: %s", self.executable_path)

    def translate_document(
        self,
        input_path: str,
        output_path: str,
        target_lang: str = 'en'
    ) -> None:
        """
        Translate a document using the GoogleTranslator subprocess.

        Args:
            input_path: Path to input document (DOCX)
            output_path: Path to save translated document (DOCX)
            target_lang: Target language code (default: 'en')

        Raises:
            FileNotFoundError: If input file or executable doesn't exist
            RuntimeError: If translation fails
        """
        logger.info("Translating document: %s -> %s",
                   os.path.basename(input_path), target_lang)
        logger.debug("Input: %s", input_path)
        logger.debug("Output: %s", output_path)
        logger.debug("Target language: %s", target_lang)

        if not os.path.exists(input_path):
            logger.error("Input file not found: %s", input_path)
            raise FileNotFoundError(f"File not found: {input_path}")

        executable_path = Path(self.executable_path)
        if not executable_path.exists():
            logger.error("Translation executable not found: %s", executable_path)
            raise FileNotFoundError(f"Executable not found: {executable_path}")

        # Build command
        arguments = ['-i', input_path, '-o', output_path]
        if target_lang and target_lang != 'en':
            arguments += ['--target', target_lang]

        command = [str(executable_path)] + arguments
        logger.debug("Translation command: %s", ' '.join(command))

        try:
            logger.info("Starting translation subprocess")
            input_size = os.path.getsize(input_path) / 1024
            logger.debug("Input file size: %.2f KB", input_size)

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5 minute timeout
            )

            if result.stdout:
                logger.debug("Translation stdout: %s", result.stdout.strip())

            if result.stderr:
                logger.warning("Translation stderr: %s", result.stderr.strip())

            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path) / 1024
                logger.info("Translation completed successfully: %s (%.2f KB)",
                           os.path.basename(output_path), output_size)
            else:
                logger.error("Translation failed - output file not created")
                raise RuntimeError("Translation subprocess did not create output file")

        except subprocess.TimeoutExpired:
            logger.error("Translation timed out after 300 seconds")
            raise RuntimeError("Translation timed out")

        except subprocess.CalledProcessError as e:
            logger.error("Translation subprocess failed with exit code %d", e.returncode)
            if e.stdout:
                logger.error("Stdout: %s", e.stdout)
            if e.stderr:
                logger.error("Stderr: %s", e.stderr)
            raise RuntimeError(f"Translation failed: {e}")

        except Exception as e:
            logger.error("Unexpected error during translation: %s", e, exc_info=True)
            raise RuntimeError(f"Translation failed: {e}")
