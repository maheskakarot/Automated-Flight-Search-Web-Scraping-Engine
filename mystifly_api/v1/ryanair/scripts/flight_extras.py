import time
from .common import CommonActions


class FlightExtras():
    def __init__(self, driver, request_data):
        self.driver = driver
        self.request_data = request_data
        self.common_actions_obj = CommonActions(self.driver)

    def airport_and_trip(self):
        time.sleep(3)
        self.common_actions_obj.click_on_continue_button()

    def transport(self):
        time.sleep(3)
        self.common_actions_obj.click_on_container_cta()
