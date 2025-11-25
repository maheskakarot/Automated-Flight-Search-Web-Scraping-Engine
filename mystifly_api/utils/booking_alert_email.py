from custom_logger.models import client_config, client_emails, operations_internal_emails
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta
from custom_logger.models import alert_schedules
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from v1.ryanair.constants.all_airport_details import AIRPORTS
import pytz

class Alert:

    def __init__(self, PNR, email_id, client_code):
        self.env = Environment(loader=FileSystemLoader('v1/ryanair/templates'))
        self.PNR = PNR
        self.email = email_id
        self.client_code = client_code


    def send_email(self, email_content, email_list, subject):
        print('sending mail')
        msg = MIMEMultipart()
        msg['From'] = "maheswaran.s@mystifly.com"
        msg['To'] = ", ".join(email_list)
        msg['Subject'] = subject

        msg.attach(MIMEText(email_content, 'html'))
        server = smtplib.SMTP('smtp-mail.outlook.com', 587)
        server.starttls()

        server.login("maheswaran.s@mystifly.com", "Mystifly@123")

        server.sendmail("maheswaran.s@mystifly.com", email_list, msg.as_string())
        server.quit()

    def store_alert_in_db(self,origin, destination, departure_date_time, arrival_date_time):
        print('storing in db')

        departure_date_time = datetime.strptime(departure_date_time, "%Y-%m-%d %H:%M:%S")
        input_timezone = pytz.timezone(AIRPORTS[origin][-1])
        localized_time = input_timezone.localize(departure_date_time)

        ist_timezone = pytz.timezone('Asia/Kolkata')
        ist_time = localized_time.astimezone(ist_timezone)

        alert_schedules.objects.create(
            journey_start=ist_time,
            timezone=AIRPORTS[origin][-1],
            pnr=self.PNR,
            email_used=self.email,
            client_code=self.client_code,
            origin_airport_code=origin
        )

        if arrival_date_time:
            arrival_date_time = datetime.strptime(arrival_date_time, "%Y-%m-%dT%H:%M:%S")
            input_timezone = pytz.timezone(AIRPORTS[destination][-1])
            localized_time = input_timezone.localize(arrival_date_time)

            ist_time = localized_time.astimezone(ist_timezone)

            alert_schedules.objects.create(
                journey_start=ist_time,
                timezone=AIRPORTS[destination][-1],
                pnr=self.PNR,
                email_used=self.email,
                client_code=self.client_code,
                origin_airport_code=destination
            )

    def get_emails_list(self):
        client_obj = client_config.objects.filter(client_code=self.client_code).last()
        email_list = []

        if client_obj.is_client_enabled:
            emails = client_emails.objects.filter(client_code=self.client_code)
            for email in emails:
                email_list.append(email.email_id)

        if client_obj.is_operations_enabled:
            emails = operations_internal_emails.objects.filter(is_ryanair_enabled=True)
            for email in emails:
                email_list.append(email.email_id)

        return email_list

    def send_confirmation(self, origin, destination, departure_date_time, arrival_date_time):
        print('inside send confirmation')
        email_list = self.get_emails_list()
        client_obj = client_config.objects.filter(client_code=self.client_code).last()

        if email_list:
            if client_obj.service_type == 'client':
                email_content = self.get_servicing_by_client_content()
            else:
                email_content = self.get_servicing_by_mystifly_content()

            subject = f"Ryanair Booking is Confirmed - PNR : {self.PNR}"
            self.send_email(email_content, email_list, subject)

        self.store_alert_in_db(origin, destination, departure_date_time, arrival_date_time)

    def send_24h_left_email(self):
        print('cronjab calling send 24h alert')
        email_list = self.get_emails_list()
        client_obj = client_config.objects.filter(client_code=self.client_code).last()
        if email_list:
            if client_obj.service_type == 'client':
                email_content = self.get_servicing_by_client_content()
            else:
                email_content = self.get_servicing_by_mystifly_content_24h()

            subject = f"Your Upcoming Ryanair Trip in Less Than 24 Hours – PNR : {self.PNR}"

    def get_servicing_by_client_content(self):
        print('getting client content')
        steps = [
            # step 2
            {
                'description': 'Click on My Bookings on the top-right of the page.',
                'image_url': 'https://drive.google.com/uc?export=view&id=1T4hqeAJMM5dxcP_J3ZRlYFeFGvgw0-js'
            },
            # step 3
            {
                'description': 'Next page, click on the Reservation Number option.',
                'image_url': 'https://drive.google.com/uc?export=view&id=1saKnh_9fqPJmuaVUhtHfYEz_71UuY0pA'
            },
            # step 4
            {
                'description': 'Key in the Reservation number and Email address given below and click on Retrieve your booking.You will now land to the next page as displayed below.',
                'image_url': 'https://drive.google.com/uc?export=view&id=1-QW756Fyp8azQcXQ7QfnqVz1pCsgJun9'
            },
            # step 5
            {
                'description': 'Click on the ‘Sign up’ option. Doing so, you have the option now to key in your email address and password. Now click on Sign up.You will now see a message on your screen saying an activation code is sent to your email.',
                'image_url': 'https://drive.google.com/uc?export=view&id=14rJzhebdhgTt4O45Jq8Em-FeVRxB2eXk'
            }
        ]

        template = self.env.get_template('service_by_client_template.html')

        # Render the template with the step data, email_id and PNR
        email_content = template.render(steps=steps, pnr=self.PNR, email_id=self.email)

        return email_content

    def get_servicing_by_mystifly_content(self):
        print('getting mystifly content')
        template = self.env.get_template('service_by_mystifly_confirmation_template.html')

        # Render the template with the step data, email_id and PNR
        email_content = template.render(pnr=self.PNR)

        return email_content

    def get_servicing_by_mystifly_content_24h(self):
        print('getting mystifly 24h content')
        template = self.env.get_template('service_by_mystifly_before24h_template.html')

        # Render the template with the step data, email_id and PNR
        email_content = template.render(pnr=self.PNR)

        return email_content


# Alert('ABCDE','japanmailbox').schedule_alert('MCN002', '2023-08-30 12:48:00', '2022-08-30 12:50:00')
