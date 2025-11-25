import smtplib
import imghdr
from email.message import EmailMessage
from easyjet.config import EMAIL,PASSWORD

def send_email(body, to_addrs):
    msg = EmailMessage()
    msg['Subject'] = "scraping error logs"
    msg['From'] = EMAIL
    msg['To'] = to_addrs
    msg.set_content(body)

    with smtplib.SMTP('smtp.office365.com',587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL, PASSWORD)
        smtp.send_message(msg)

