import imaplib
import json
from typing import Dict


def read_json_file(file_path: str) -> (Dict | None):
    """
    Reads a JSON file and returns its content as a Python dictionary.

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


def check_yahoo_email(username: str, password: str):
    """
    Check Yahoo email using IMAP protocol.

    Args:
        username (str): Yahoo email username.
        password (str): Yahoo email password.

    Returns:
        str: A string indicating the number of unread emails in the inbox.

    Raises:
        Exception: If there is an error while connecting to the Yahoo email
        server.
    """
    try:
        # Connect to the Yahoo IMAP server
        imap_server: imaplib.IMAP4_SSL = imaplib.IMAP4_SSL(
            "imap.mail.yahoo.com")

        # Login to the Yahoo email account
        imap_server.login(username, password)

        # Select the inbox folder
        imap_server.select("inbox")

        # Search for unread emails
        _, data = imap_server.search(None, "ALL")

        # Get the number of unread emails
        num_unread_emails: int = len(data[0].split())

        # Logout from the Yahoo email account
        imap_server.logout()

        return f"You have {num_unread_emails} unread emails in your Yahoo inbox."

    except Exception as e:
        raise Exception(
            "Error while connecting to the Yahoo email server.") from e


if __name__ == "__main__":

    secrets: Dict = read_json_file("secrets.json")

    username = secrets.get('username')
    password = secrets.get('password')

    result = check_yahoo_email(username, password)
    print(result)
