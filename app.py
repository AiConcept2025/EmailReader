"""
Module processes email attachments
"""

import time
from schedule import run_pending
from email_reader import extract_attachments_from_mailbox
from flowise_api import FlowiseAiAPI

if __name__ == "__main__":
    flowiseApi = FlowiseAiAPI()

    extract_attachments_from_mailbox()
    while True:
        run_pending()
        time.sleep(1)
