"""
Module providing a functionality for retrieve attachments and send
to document store
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict
# from langdetect import detect

from imap_tools import AND, MailBox

# from src.convert_to_docx import (
#    convert_pdf_to_docx, convert_txt_file_to_docx, convert_txt_to_docx)
from src.utils import get_uuid, utc_to_local
from src.config import load_config
# from src.pdf_image_ocr import is_pdf_searchable_pypdf
from src.process_documents import DocProcessor

# Get logger for this module
logger = logging.getLogger('EmailReader.Email')


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
    logger.debug("Entering get_last_finish_time()")
    logger.debug("Date file: %s, start_date: %s", date_file, start_date)

    date_file_path = Path(os.path.join(cwd, date_file))
    logger.debug("Full date file path: %s", date_file_path)

    if date_file_path.is_file():
        logger.debug("Date file exists, reading last scan time")
        with open(date_file_path, encoding="utf-8", mode="r") as file:
            date: str = file.read()
            logger.debug("Read date string: %s", date)
            date_time: datetime = datetime.strptime(
                date, "%Y-%m-%d %H:%M:%S %z")
        logger.info("Last scan time loaded: %s", date_time)
    else:
        logger.info("Date file doesn't exist, creating with default: %s", start_date)
        with open(date_file_path, encoding="utf-8", mode="w") as file:
            file.write(start_date)
            date_time: datetime = datetime.strptime(
                start_date, "%Y-%m-%d %H:%M:%S %z")

    last_date_time = utc_to_local(date_time)
    last_date: datetime = date_time.date()
    last_time: datetime = date_time.time()

    logger.debug("Returning: last_date_time=%s, last_date=%s, last_time=%s",
                last_date_time, last_date, last_time)
    return (last_date_time, last_date, last_time)


def set_last_finish_time(date_file: str, start_date: datetime) -> None:
    """
    Save new finish scan date

    Args:
    date_file: path to the file
    start_date: datetime last scan
    """
    logger.debug("Entering set_last_finish_time()")
    logger.debug("Date file: %s, start_date: %s", date_file, start_date)

    start_date = utc_to_local(start_date)
    date_file_path = Path(os.path.join(cwd, date_file))
    start_date_str: str = start_date.strftime("%Y-%m-%d %H:%M:%S %z")

    logger.debug("Writing date string: %s to %s", start_date_str, date_file_path)
    with open(date_file_path, encoding="utf-8", mode="w") as file:
        file.write(start_date_str)

    logger.info("Last finish time saved: %s", start_date_str)


def extract_attachments_from_mailbox():
    """
    Reads emails from mailbox and sends qualified attachments
    fo document store
    """
    logger.info("="*80)
    logger.info('Starting extract_attachments_from_mailbox()')
    logger.debug("Current working directory: %s", cwd)

    try:
        logger.debug("Loading configuration")
        config: Dict = load_config()

        email: Dict = config.get('email')
        if email is None:
            logger.error("No email configuration found in config")
            raise ValueError("No email object specified")

        logger.debug("Email config - server: %s, username: %s",
                    email.get('imap_server'), email.get('username'))

        last_date_time, last_date, _ = get_last_finish_time(
            email.get('date_file'),
            email.get('start_date'))
        logger.info("Scanning for emails since: %s", last_date_time)

        attachments_file_path = Path(os.path.join(cwd, 'data', "documents"))
        logger.debug("Attachments will be saved to: %s", attachments_file_path)

        logger.debug("Initializing DocProcessor")
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
                _, file_ext = os.path.splitext(file_name)
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
