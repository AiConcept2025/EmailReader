"""
Start point for the application.
"""
import os
import time
from schedule import run_pending
from src.app import process_emails


if __name__ == "__main__":
    # Check if data folder exist
    dir_data = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(dir_data) or not os.path.isdir(dir_data):
        os.mkdir(dir_data)
    # Check if documents folder exist
    dir_documents = os.path.join(os.getcwd(), 'data', 'documents')
    if not os.path.exists(dir_documents) or not os.path.isdir(dir_documents):
        os.mkdir(dir_documents)
    # Check if last_finish_time.txt exist
    dir_finish_tag = os.path.join(os.getcwd(), 'data', 'last_finish_time.txt')
    if not os.path.exists(dir_finish_tag) or not os.path.isfile(dir_finish_tag):
        with open(dir_finish_tag, 'w', encoding='utf-8') as file:
            file.write('2020-01-01 01:01:01 +0000')

    process_emails()

    # Run on schedule
    while True:
        run_pending()
        time.sleep(1)
