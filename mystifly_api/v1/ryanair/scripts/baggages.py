from v1.ryanair.constants.class_names import CLASS_NAMES
from .common import CommonActions


class Baggages():
    def __init__(self, driver, request_data):
        self.driver = driver
        self.request_data = request_data
        self.common_actions_obj = CommonActions(self.driver)

    def select_included_baggages(self):
        try:
            radio_btn = self.driver.find_elements_by_class_name(CLASS_NAMES['RADIO_BTN'])[0]
            self.common_actions_obj.scroll_to_element(radio_btn)
            radio_btn.click()
        except Exception as ex:
            print("select_included_baggages - ", ex)
