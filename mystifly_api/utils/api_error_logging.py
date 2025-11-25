import datetime
from .api_email_utils import send_email
from custom_logger.logging import LogMessage
import logging
import json

logger = logging.getLogger(__name__)


def send_error_mail( search_id, screen_name, exception, request_data=None):
    error = {
        "Screen": screen_name,
        "message": str(exception),
        "request_data": request_data,
        "log_added": True,
        "log_failure_message": None
    }
    try:
        send_completion_mail( screen_name, str(error))
        logger.error(LogMessage(json.dumps(error),screen_name, search_id=search_id).save_log)

    except Exception as e:
        error['log_added'] = False
        error['log_failure_message'] = str(e)
    return error


def send_completion_mail(screen_name, message=None):
    screen_name = screen_name
    email_list = ["suim-scraping-team@mystifly.com"]
    send_email(f"{message}", email_list)
