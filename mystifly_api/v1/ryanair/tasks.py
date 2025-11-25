from datetime import datetime, timedelta
from account.models import SubscriberWebDriver, WebdriverLifeManager
from v1.ryanair.helpers.webdriver import SessionRemote
from django.utils import timezone
import pytz
from custom_logger.models import alert_schedules, client_config
from utils.booking_alert_email import Alert
def close_unused_webdriver():
    close_after = 8
    web_drivers_to_close = SubscriberWebDriver.objects.filter(is_active=True,
                                                              updated_on__lte=timezone.now().astimezone(pytz.timezone('Asia/Kolkata')) - timedelta(
                                                                  minutes=close_after))
    print(web_drivers_to_close.count())
    print("cronjobs executed")
    for web_driver_to_close in web_drivers_to_close:
        url = web_driver_to_close.url
        session_id = web_driver_to_close.session_id
        print(url, session_id)

        try:
            driver = SessionRemote(command_executor=url, desired_capabilities={})
            driver.session_id = session_id
            print(driver.title)
            driver.quit()
        except Exception as ex:
            print(ex)

        web_driver_to_close.is_active = False
        web_driver_to_close.save()


def check_journey_time_for_alert():

    print('inside check-journey-times cronjob')
    indian_timezone = pytz.timezone('Asia/Kolkata')
    current_time_in_india = timezone.now().astimezone(indian_timezone)
    time_threshold = current_time_in_india + timedelta(hours=24)

    records = alert_schedules.objects.filter(journey_start__lt=time_threshold)

    if records:

        for data in records:
            alert_obj = Alert(data.pnr, data.email_used, data.client_code)
            alert_obj.send_24h_left_email()

        records.delete()
