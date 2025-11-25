from .scripts.ryanair_apis import RyanairExecuter, generate_html_content
import smtplib
from email.message import EmailMessage


def generate_ryanair_report():
    status_obj = RyanairExecuter()
    report = status_obj.get_report()
    html_content = generate_html_content(report)
    msg = EmailMessage()
    msg['Subject'] = 'Ryanair Scraping API Status'
    msg['From'] = "maheswaran.s@mystifly.com"
    msg['To'] = [' suim-scraping-team@mystifly.com']
    msg.add_alternative(html_content, subtype='html')

    with smtplib.SMTP('smtp.office365.com', 587) as smtp:
        smtp.starttls()
        smtp.login("maheswaran.s@mystifly.com", "Mystifly@123")
        smtp.send_message(msg)
