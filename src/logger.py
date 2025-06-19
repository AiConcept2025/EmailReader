"""
Logging module
"""
import os
import logging

# Check if data folder exist
dir_data = os.path.join(os.getcwd(), 'data')
if not os.path.exists(dir_data) or not os.path.isdir(dir_data):
    os.mkdir(dir_data)
# Create path
logging_path = os.path.join(os.getcwd(), 'data', 'logging.log')
# Delete if exist
try:
    os.remove(logging_path)
except FileNotFoundError:
    pass
logger = logging.getLogger(__name__)
logging.basicConfig(filename=logging_path,
                    format='%(asctime)s %(levelname)s %(filename)s: %(lineno)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S',
                    encoding='utf-8',
                    level=logging.DEBUG)
