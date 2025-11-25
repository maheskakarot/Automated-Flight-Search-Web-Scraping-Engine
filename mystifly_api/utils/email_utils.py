import smtplib
import imghdr
from email.message import EmailMessage


def send_email(subject, body, attachment_name, to_addrs):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = "maheswaran.s@mystifly.com"
    msg['To'] = to_addrs
    msg.set_content(body)

    if attachment_name:
        with open(attachment_name, 'rb') as f:
            file_data = f.read()
            file_type = imghdr.what(f.name)
            file_name = f.name

        msg.add_attachment(file_data, maintype='image', subtype=file_type, filename=file_name)

    with smtplib.SMTP('smtp.office365.com', 587) as smtp:
        smtp.starttls()
        smtp.login("maheswaran.s@mystifly.com", "Mystifly@123")
        smtp.send_message(msg)
