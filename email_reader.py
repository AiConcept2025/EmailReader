"""
Module providing a functionality for retrieve attachments and send
to document store
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict

from imap_tools import AND, MailBox
from schedule import every, repeat
from utils import read_json_secret_file, utc_to_local


supported_types = [
    "application/msword",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
    "text/plain",
    "application/rtf",
]

cwd = os.getcwd()


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
    date_file_path = Path(os.path.join(cwd, date_file))
    if date_file_path.is_file():
        with open(date_file_path, encoding="utf-8", mode="r") as file:
            date: str = file.read()
            date_time: datetime = datetime.strptime(
                date, "%Y-%m-%d %H:%M:%S %z")
    else:
        with open(date_file_path, encoding="utf-8", mode="w") as file:
            file.write(start_date)
            date_time: datetime = datetime.strptime(
                start_date, "%Y-%m-%d %H:%M:%S %z")
    last_date_time = utc_to_local(date_time)
    last_date: datetime = date_time.date()
    last_time: datetime = date_time.time()
    return (last_date_time, last_date, last_time)


def set_last_finish_time(date_file: str, start_date: datetime) -> None:
    """
    Save new finish scan date

    Args:
    date_file: path to the file
    start_date: datetime last scan
    """
    start_date = utc_to_local(start_date)
    date_file_path = Path(os.path.join(cwd, date_file))
    start_date_str: str = start_date.strftime("%Y-%m-%d %H:%M:%S %z")
    with open(date_file_path, encoding="utf-8", mode="w") as file:
        file.write(start_date_str)


@repeat(every(1).minute)
def extract_attachments_from_mailbox():
    """
    Reads emails from mailbox and sends qualified attachments
    fo document store
    """
    secrets: Dict = read_json_secret_file("secrets.json")
    email: Dict = secrets.get('email')
    if email is None:
        raise ValueError("No email object specified")
    last_date_time, last_date, _ = get_last_finish_time(
        email.get('date_file'),
        email.get('start_date'))

    attachments_file_path = Path(os.path.join(cwd, "documents"))

    with MailBox(host=email.get('imap_server')).login(
            username=email.get("username"),
            password=email.get("password"),
            initial_folder=email.get("initial_folder")) as mailbox:
        for msg in mailbox.fetch(criteria=AND(date_gte=last_date)):
            adjust_msg_date = utc_to_local(msg.date)
            if adjust_msg_date < last_date_time:
                continue
            for att in msg.attachments:
                try:
                    if att.filename == "":
                        continue
                    if att.content_type not in supported_types:
                        continue
                    # send file to document store
                    with open(
                        f"{attachments_file_path}/{
                            msg.from_} {att.filename}", "wb"
                    ) as f:
                        print(att.filename, att.content_type)
                        f.write(att.payload)
                except Exception as e:
                    print(e, att.filename, att.content_type)
                    continue

    set_last_finish_time(email.get("date_file"), datetime.now())
