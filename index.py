"""
Start point for the application.
"""
import time
from schedule import run_pending
from src.flowise_api import FlowiseAiAPI
from src.app import process_emails
from src.google_drive import GoogleApi


if __name__ == "__main__":
    flowiseApi = FlowiseAiAPI()
    googleApi = GoogleApi()

    process_emails()

    # Run on schedule
    while True:
        run_pending()
        time.sleep(1)
