"""
Enhanced logging module with comprehensive file and console logging.

This module provides:
- Centralized logging configuration for the EmailReader application
- Rotating file handler (10MB per file, 5 backups)
- Separate console and file formatters
- Module-specific loggers for different components
- OCR-specific loggers for provider operations
- Performance metrics logging
- Helper functions for consistent logger retrieval and performance tracking

Usage:
    >>> from src.logger import get_logger
    >>> logger = get_logger('MyModule')
    >>> logger.info('Operation completed')

    >>> from src.logger import log_performance_metric
    >>> log_performance_metric('ocr_process', 2.5, provider='landing_ai')
"""
import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Check if data folder exist
dir_data = os.path.join(os.getcwd(), 'data')
if not os.path.exists(dir_data) or not os.path.isdir(dir_data):
    os.mkdir(dir_data)

# Create logs directory in project root (not in data/)
logs_dir = os.path.join(os.getcwd(), 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Create log file path - always logs/email_reader.log
log_filename = "email_reader.log"
logging_path = os.path.join(logs_dir, log_filename)

# Configure root logger
logger = logging.getLogger('EmailReader')
logger.setLevel(logging.DEBUG)

# Clear existing handlers
logger.handlers = []

# Create formatters
# Detailed formatter for file output with all context
detailed_formatter = logging.Formatter(
    ('%(asctime)s | %(levelname)-8s | %(name)-25s | '
     '%(filename)-20s:%(lineno)-4d | %(funcName)-25s | %(message)s'),
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Simple formatter for console - less verbose for readability
simple_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%H:%M:%S'
)

# File handler with rotation - 10MB per file, keep 5 backups
file_handler = RotatingFileHandler(
    logging_path,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(detailed_formatter)

# Console handler - INFO level for less noise, DEBUG goes to file
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(simple_formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Create separate loggers for different modules
flowise_logger = logging.getLogger('EmailReader.Flowise')
gdrive_logger = logging.getLogger('EmailReader.GoogleDrive')
doc_processor_logger = logging.getLogger('EmailReader.DocProcessor')
translator_logger = logging.getLogger('EmailReader.Translator')
email_logger = logging.getLogger('EmailReader.Email')
ocr_logger = logging.getLogger('EmailReader.OCR')
utils_logger = logging.getLogger('EmailReader.Utils')

# OCR-specific loggers for detailed operation tracking
ocr_factory_logger = logging.getLogger('EmailReader.OCR.Factory')
ocr_default_logger = logging.getLogger('EmailReader.OCR.Default')
ocr_landing_ai_logger = logging.getLogger('EmailReader.OCR.LandingAI')
ocr_performance_logger = logging.getLogger('EmailReader.OCR.Performance')
document_analyzer_logger = logging.getLogger('EmailReader.DocumentAnalyzer')
layout_reconstructor_logger = logging.getLogger('EmailReader.LayoutReconstructor')

logger.info("="*80)
logger.info("EmailReader Application Started")
logger.info("Log file: %s", logging_path)
logger.info("="*80)


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the EmailReader namespace.

    This function ensures consistent logger naming across the application.
    If the name doesn't start with 'EmailReader', it will be prefixed.

    Args:
        name: Logger name (e.g., 'OCR.Factory' or 'EmailReader.OCR.Factory')

    Returns:
        Logger instance

    Examples:
        >>> logger = get_logger('OCR.Factory')
        >>> logger.info('Factory created provider')

        >>> logger = get_logger('EmailReader.DocumentAnalyzer')
        >>> logger.debug('Analyzing document...')
    """
    if not name.startswith('EmailReader'):
        name = f'EmailReader.{name}'
    return logging.getLogger(name)


def log_performance_metric(operation: str, duration_seconds: float,
                          document_path: str = None, **kwargs) -> None:
    """
    Log OCR performance metrics in a structured format.

    This function logs performance data in a consistent format that can be
    easily parsed for monitoring, analysis, and optimization.

    Args:
        operation: Name of the operation (e.g., 'ocr_process', 'layout_reconstruction')
        duration_seconds: Time taken in seconds
        document_path: Optional path to document being processed
        **kwargs: Additional metadata (provider, page_count, file_size, etc.)

    Examples:
        >>> log_performance_metric('ocr_process', 3.45,
        ...                        document_path='scan.pdf',
        ...                        provider='landing_ai',
        ...                        page_count=5)

        >>> log_performance_metric('layout_reconstruction', 1.2,
        ...                        content_blocks=42,
        ...                        table_count=3)
    """
    metadata = {
        'operation': operation,
        'duration_seconds': round(duration_seconds, 3),
        'duration_formatted': f"{duration_seconds:.2f}s"
    }

    if document_path:
        import os
        metadata['document'] = os.path.basename(document_path)
        if os.path.exists(document_path):
            metadata['file_size_kb'] = round(os.path.getsize(document_path) / 1024, 2)

    metadata.update(kwargs)

    # Format metadata as key=value pairs for easy parsing
    metadata_str = ' | '.join(f"{k}={v}" for k, v in metadata.items())

    ocr_performance_logger.info(f"PERFORMANCE | {metadata_str}")


# Export commonly used loggers and functions
__all__ = [
    'logger',
    'get_logger',
    'log_performance_metric',
    'flowise_logger',
    'gdrive_logger',
    'doc_processor_logger',
    'translator_logger',
    'email_logger',
    'ocr_logger',
    'ocr_factory_logger',
    'ocr_default_logger',
    'ocr_landing_ai_logger',
    'ocr_performance_logger',
    'document_analyzer_logger',
    'layout_reconstructor_logger',
    'utils_logger'
]
