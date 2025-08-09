"""
Enhanced logging module with better configuration and multiple handlers
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

# Create logs directory
logs_dir = os.path.join(os.getcwd(), 'data', 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Create path with timestamp
log_filename = f"emailreader_{datetime.now().strftime('%Y%m%d')}.log"
logging_path = os.path.join(logs_dir, log_filename)

# Configure root logger
logger = logging.getLogger('EmailReader')
logger.setLevel(logging.DEBUG)

# Clear existing handlers
logger.handlers = []

# Create formatters
detailed_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

simple_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)

# File handler with rotation
file_handler = RotatingFileHandler(
    logging_path,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(detailed_formatter)

# Console handler
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

logger.info("="*60)
logger.info("EmailReader Application Started")
logger.info("="*60)
