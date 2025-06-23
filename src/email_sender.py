"""
Send error email
"""
from email.mime.text import MIMEText
from smtplib import SMTP_SSL as SMTP

SMTP_SERVER = 'smtp.att.yahoo.com'
SENDER = "danishevsky@yahoo.com"
destination = ['danishevsky@gmail.com']
USERNAME = "danishevsky@yahoo.com"
PASSWORD = "jesldoieqwsjeqai"
# typical values for text_subtype are plain, html, xml
TEXT_SUBTYPE = 'plain'
SUBJECT = "Send from EmailReader"


def send_error_message(content: None = 'Send email Error'):
    """
    Send email with error message
    """
    try:
        msg = MIMEText(content, TEXT_SUBTYPE)
        msg['Subject'] = SUBJECT
        msg['From'] = SENDER
        conn = SMTP(SMTP_SERVER)
        conn.set_debuglevel(False)
        conn.login(USERNAME, PASSWORD)
        conn.sendmail(SENDER, destination, msg.as_string())

    except Exception as error:
        print(error)
    finally:
        conn.quit()
