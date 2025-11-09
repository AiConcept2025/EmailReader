"""
Enhanced logging module with comprehensive file and console logging
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

logger.info("="*80)
logger.info("EmailReader Application Started")
logger.info("Log file: %s", logging_path)
logger.info("="*80)
