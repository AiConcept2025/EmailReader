from imap_tools import MailBox, AND
import json
from datetime import datetime, timezone
from typing import Dict
from pathlib import Path
import os


supported_types = [
    "application/msword",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
    "text/plain",
    "application/rtf",
]


def utc_to_local(utc_dt: datetime) -> datetime:
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


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


def get_last_finish_time(
        date_file: str, start_date: str) -> tuple[datetime, datetime]:
    """
    Retrieve date/time when  last scan started

    Args:
    date_file: date/time file name
    start_date: default date/time

    Returns:
    tuple: date time
    """
    cwd = os.getcwd()
    date_file_path = Path(os.path.join(cwd, date_file))
    if date_file_path.is_file():
        with open(date_file_path, 'r') as file:
            date: str = file.read()
            date_time: datetime = datetime.strptime(
                date, "%Y-%m-%d %H:%M:%S %z")
    else:
        with open(date_file_path, "w") as file:
            file.write(start_date)
            date_time: datetime = datetime.strptime(
                start_date, "%Y-%m-%d %H:%M:%S %z")
    date_time = utc_to_local(date_time)
    last_date: datetime = date_time.date()
    last_time: datetime = date_time.time()
    return (last_date, last_time)


def set_last_finish_time(date_file: str, start_date: datetime) -> None:
    """
    Save new finish scan date

    Args:
    date_file: path to the file
    start_date: datetime last scan
    """
    cwd = os.getcwd()
    date_file_path = Path(os.path.join(cwd, date_file))
    start_date_str: str = start_date.strftime("%Y-%m-%d %H:%M:%S %z")
    with open(date_file_path, 'w') as file:
        file.write(start_date_str)


date_string_z = "2025-03-01 10:30:00 +0800"
parsed_dt_z = datetime.strptime(date_string_z, "%Y-%m-%d %H:%M:%S %z")
print(parsed_dt_z)


secrets: Dict = read_json_secret_file("secrets.json")
username = secrets.get('username')
password = secrets.get('password')
imap_server = secrets.get("imap_server")
date_file = secrets.get("date_file")
start_date = secrets.get("start_date")

last_date, last_time = get_last_finish_time(date_file, start_date)

cwd = os.getcwd()
attachments_file_path = Path(os.path.join(cwd, "attachments"))

with MailBox(imap_server).login(
        username, password) as mailbox:
    for msg in mailbox.fetch(AND(date_gte=last_date)):

        print(utc_to_local(msg.date).time())
        print(last_time)

        for att in msg.attachments:
            try:
                if att.filename == '':
                    continue
                if att.content_type not in supported_types:
                    continue
                with open(
                    f'{attachments_file_path}/{msg.from_} {att.filename}', 'wb'
                ) as f:
                    print(att.filename, att.content_type)
                    f.write(att.payload)
            except Exception as e:
                print(e, att.filename, att.content_type)
                continue

set_last_finish_time(date_file, datetime.now())
