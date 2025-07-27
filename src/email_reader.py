"""
Module providing a functionality for retrieve attachments and send
to document store
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict
from langdetect import detect

from imap_tools import AND, MailBox

from src.convert_to_docx import (
    convert_pdf_to_docx, convert_txt_file_to_docx, convert_txt_to_docx)
from src.logger import logger
from src.utils import get_uuid, read_json_secret_file, utc_to_local
from src.pdf_image_ocr import is_pdf_searchable_pypdf
from src.process_documents import DocProcessor


supported_types = [
    "application/msword",       # .doc
    "application/pdf",         # .pdf
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/octet-stream",  # .docx
    "text/plain",            # .txt
    "application/rtf",      # .rtf

    "image/gif",       # .gif
    "image/jpeg",     # .jpg
    "image/png",     # .png
    "image/tiff",    # .tiff .tif
]

cwd = os.getcwd()


def delete_file(file_path: str):
    """
    Delete file by path
    """
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"File '{file_path}' deleted successfully.")
        except OSError as e:
            print(f"Error deleting file '{file_path}': {e}")
    else:
        print(f"File '{file_path}' does not exist.")


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


def extract_attachments_from_mailbox():
    """
    Reads emails from mailbox and sends qualified attachments
    fo document store
    """
    logger.info('Start extract documents from mailbox')
    secrets_file = os.path.join(os.getcwd(), 'credentials', "secrets.json")
    secrets: Dict = read_json_secret_file(secrets_file)
    email: Dict = secrets.get('email')
    if email is None:
        raise ValueError("No email object specified")
    last_date_time, last_date, _ = get_last_finish_time(
        email.get('date_file'),
        email.get('start_date'))
    attachments_file_path = Path(os.path.join(cwd, 'data', "documents"))
    docProcessor = DocProcessor(attachments_file_path)

    with MailBox(host=email.get('imap_server')).login(
            username=email.get("username"),
            password=email.get("password"),
            initial_folder=email.get("initial_folder")) as mailbox:
        for msg in mailbox.fetch(criteria=AND(date_gte=last_date)):
            adjust_msg_date = utc_to_local(msg.date)
            if adjust_msg_date < last_date_time:
                continue
            # Process email body
            if msg.text and len(msg.text) > 500:
                file_name = f"{msg.from_}+{get_uuid()}.docx"
                file_path = f"{attachments_file_path}/{file_name}"
                logger.info('Process email body %s', file_name)
                # convert_txt_to_docx(paragraph=msg.text,
                #                     docx_file_path=file_path)
            # Process attachments
            for attachment in msg.attachments:
                file_name = f"{msg.from_}+{attachment.filename}"
                file_name_no_ext, file_ext = os.path.splitext(file_name)
                try:
                    if attachment.filename == "":
                        logger.warning(
                            'Date: %s. Attachment from %s does not have name.',
                            adjust_msg_date, msg.from_)
                        continue
                    elif attachment.content_type not in supported_types:
                        logger.warning(
                            'Date: %s. Attachment %s from %s has not supported type.',
                            adjust_msg_date,
                            attachment.filename,
                            msg.from_)
                        continue
                    elif attachment.content_type == "application/pdf":  # Can be image or text
                        docProcessor.convert_pdf_payload_to_word(
                            client=msg.from_,
                            doc_name=attachment.filename,
                            payload=attachment.payload)
                        continue
                    elif attachment.content_type == "text/plain":
                        docProcessor.convert_plain_text_to_word(
                            client=msg.from_,
                            txt_file_name=attachment.filename,
                            payload=attachment.payload
                        )
                        continue
                    elif file_ext == ".rtf":
                        docProcessor.convert_rtf_text_to_world(
                            client=msg.from_,
                            rtf_file_name=attachment.filename,
                            payload=attachment.payload
                        )
                        continue
                    elif (
                            attachment.content_type == "application/octet-stream" or
                            attachment.content_type == "application/msword" or
                            attachment.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
                        # Word document
                        file_path = f"{attachments_file_path}/{file_name}"
                        # download file in temp folder
                        with open(file_path, "wb") as f:
                            f.write(attachment.payload)
                        continue

                    # Graphic formats
                    elif attachment.content_type == "image/gif":
                        continue
                    elif attachment.content_type == "image/jpeg":
                        continue
                    elif attachment.content_type == "image/png":
                        continue
                    elif attachment.content_type == "image/tiff":
                        continue
                    else:
                        continue

                except Exception as e:
                    logger.error('%s %s %s', e, attachment.filename,
                                 attachment.content_type)
                    continue

    set_last_finish_time(email.get("date_file"), datetime.now())
    logger.info('Finish email processing')
