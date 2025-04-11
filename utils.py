"""
Utilities
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from dateutil import tz


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
        with open(file_path, encoding="utf-8", mode="r") as file:
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


def utc_to_local(utc_dt: datetime) -> datetime:
    """
    Convert date/time to local time zone

    Args:

    """
    time_stamp = utc_dt.replace(tzinfo=timezone.utc)
    return time_stamp


def list_all_dir_files():
    """
    List all files in specify folder
    Args:
        folder: folder name
    """
    cwd = os.getcwd()
    secrets: Dict = read_json_secret_file("secrets.json")
    documents_folder = secrets.get("documents").get("documents_folder")
    attachments_path = Path(os.path.join(cwd, documents_folder))
    attachments_dir_list = os.listdir(attachments_path)
    return attachments_dir_list


def list_files_in_directory(folder_path: str) -> List:
    """
    Lists all files in the specified directory.

    Args:
      folder_path: The path to the directory.

    Returns:
      A list of file names in the directory.
    """
    try:
        file_list = os.listdir(folder_path)
        return file_list
    except FileNotFoundError:
        print(f"Error: Directory not found: {folder_path}")
        return []
    except NotADirectoryError:
        print(f"Error: Not a directory: {folder_path}")
        return []
