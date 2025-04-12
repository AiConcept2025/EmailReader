from email.mime.text import MIMEText
from smtplib import SMTP_SSL as SMTP

SMTPserver = 'smtp.att.yahoo.com'
sender = "danishevsky@yahoo.com"
destination = ['danishevsky@gmail.com']
USERNAME = "danishevsky@yahoo.com"
PASSWORD = "jesldoieqwsjeqai"
# typical values for text_subtype are plain, html, xml
text_subtype = 'plain'
subject = "Send from EmailReader"


def send_error_message(content: None = 'Send email Error'):
    try:
        msg = MIMEText(content, text_subtype)
        msg['Subject'] = subject
        msg['From'] = sender
        conn = SMTP(SMTPserver)
        conn.set_debuglevel(False)
        conn.login(USERNAME, PASSWORD)
        conn.sendmail(sender, destination, msg.as_string())

    except Exception as error:
        print(error)
    finally:
        conn.quit()
