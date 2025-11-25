from datetime import datetime
from .email_utils import send_email
from v1.ryanair.helpers.webdriver import close_webdriver
from .delete_file import delete_file_from_os
from custom_logger.logging import LogMessage
import logging
import json
from django.conf import settings

logger = logging.getLogger(__name__)

def send_error_mail(driver, subscriber, webdriver_obj, screen_name, exception, request_data=None):
    error = {
        "Project": 'Ryanair',
        "Screen": screen_name,
        "message": str(exception),
        "country_code": subscriber.country_code,
        "mobile": subscriber.mobile,
        "request_data": request_data,
        "log_added": True,
        "log_failure_message": None
    }
    try:
        time_now = datetime.now().time()
        send_completion_mail(driver, screen_name, time_now, str(error))
        logger.error(LogMessage(json.dumps(error), screen_name, time_now, driver).save_log)
    except Exception as e:
        print(e)
        error['log_added'] = False
        error['log_failure_message'] = str(e)
    close_webdriver(driver, webdriver_obj)
    return error

def send_completion_mail(driver, screen_name, time_now, message=None):
    file_name = (
            f"{str(settings.BASE_DIR)}/mystifly_api/screen_short/"
            + f"{screen_name} - {time_now}.png"
    )
    driver.save_screenshot(file_name)
    email_list = ["suim-scraping-team@mystifly.com"]
    send_email(f"{screen_name}", f"{message}", file_name, email_list)
    delete_file_from_os(file_name)

def easyjet_error_email(driver, search_id, screen_name, exception, request_data=None):
    error = {
        "Project":"Easyjet",
        "Screen": screen_name,
        "message": str(exception),
        "Search id ": search_id,
        "request_data": request_data,
        "log_added": True,
        "log_failure_message": None
    }
    try:
        time_now = datetime.now().time()
        send_completion_mail(driver, screen_name, time_now, str(error))
        logger.error(LogMessage(json.dumps(error), screen_name, driver).save_log)

        # logger.error(LogMessage(json.dumps(error), screen_name, time_now, driver).save_log)
    except Exception as e:
        print(e)
        error['log_added'] = False
        error['log_failure_message'] = str(e)
    # close_webdriver(driver)
    return error