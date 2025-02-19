from imap_tools import MailBox, AND
import datetime
import json
from typing import Dict

supported_types = [
    "application/msword",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
    "text/plain",
    "application/rtf",
]


def read_json_secret_file(file_path: str) -> (Dict | None):
    """
    Reads a JSON Secrets file and returns its content as a Python dictionary.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: A dictionary representing the JSON data,
        or None if an error occurs.
    """
    try:
        with open(file_path, 'r') as file:
            data: Dict = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{file_path}'")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


secrets: Dict = read_json_secret_file("secrets.json")

username = secrets.get('username')
password = secrets.get('password')
imap_server = secrets.get("imap_server")

with MailBox(imap_server).login(
        username, password) as mailbox:
    for msg in mailbox.fetch(AND(date_gte=datetime.datetime(2020, 3, 15), date_lt=datetime.date(2021, 3, 15))):
        print(msg.date)
        for att in msg.attachments:
            try:
                if att.filename == '':
                    continue
                if att.content_type not in supported_types:
                    continue
                with open(
                        f'C:/Projects/test/{msg.from_} {att.filename}', 'wb'
                ) as f:
                    print(att.filename, att.content_type)
                    f.write(att.payload)
            except Exception as e:
                print(e, att.filename, att.content_type)
                continue
