import imaplib


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
        _, data = imap_server.search(None, "UNSEEN")

        # Get the number of unread emails
        num_unread_emails: int = len(data[0].split())

        # Logout from the Yahoo email account
        imap_server.logout()

        return f"You have {num_unread_emails} unread emails in your Yahoo inbox."

    except Exception as e:
        raise Exception(
            "Error while connecting to the Yahoo email server.") from e


# Example usage
username = "danishevsky@yahoo.com"
password = "jesldoieqwsjeqai"

result = check_yahoo_email(username, password)
print(result)
