import json
from typing import Dict
from datetime import datetime, timezone


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
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
