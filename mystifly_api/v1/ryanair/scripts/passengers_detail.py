import time
from datetime import datetime
from v1.ryanair.constants.xpaths import XPATHS
from v1.ryanair.constants.ids import IDS
from .common import CommonActions
from v1.ryanair.constants.class_names import CLASS_NAMES
from utils.email_utils import send_email


class PassengersDetail:
    def __init__(self, driver, request_data):
        self.driver = driver
        self.adult = 0
        self.child = 0
        self.teen = 0
        self.infant = 0
        self.request_data = request_data
        self.common_actions_obj = CommonActions(self.driver)

    def fill_passengers_info(self):
        self.common_actions_obj.click_on_login_later_button()
        time.sleep(2)
        passengers_data = self.request_data.get('PassengersDetails', None)

        if passengers_data:
            total_passengers = len(passengers_data)

            for passenger_data in passengers_data:
                passenger_data["is_added"] = False

            for passenger_number in range(1, total_passengers + 1):
                passenger_detail_box = self.driver.find_element_by_xpath(
                    XPATHS['PASSENGER_DETAIL_BOX'].format(passenger_number))

                self.fill_single_passenger_info(passengers_data, str(passenger_number), passenger_detail_box)

    def fill_single_passenger_info(self, passengers_data, passenger_number, passenger_detail_box_element):
        passenger_detail_box_info = passenger_detail_box_element.text.splitlines()
        adult_passenger = "Passenger " + passenger_number + " Adult"
        child_passenger = "Passenger " + passenger_number + " Child"
        teen_passenger = "Passenger " + passenger_number + " Teen"
        infant_passenger = "Passenger " + passenger_number + " Infant"

        if adult_passenger in passenger_detail_box_info:
            first_name_box_id = IDS['ADT_FN_BOX'].format(self.adult)
            last_name_box_id = IDS['ADT_LN_BOX'].format(self.adult)

            passenger_data = self.get_passenger_data_to_add(passengers_data, "ADT")

            self.fill_passenger_info(passenger_detail_box_element, passenger_data, first_name_box_id, last_name_box_id,
                                     is_title=True, dob_box_id=None)
            self.adult += 1

        elif child_passenger in passenger_detail_box_info:
            first_name_box_id = IDS['CHD_FN_BOX'].format(self.child)
            last_name_box_id = IDS['CHD_LN_BOX'].format(self.child)

            passenger_data = self.get_passenger_data_to_add(passengers_data, "CHD")

            self.fill_passenger_info(passenger_detail_box_element, passenger_data, first_name_box_id, last_name_box_id,
                                     is_title=False, dob_box_id=None)
            self.child += 1

        elif teen_passenger in passenger_detail_box_info:
            first_name_box_id = IDS['TEEN_FN_BOX'].format(self.teen)
            last_name_box_id = IDS['TEEN_LN_BOX'].format(self.teen)

            passenger_data = self.get_passenger_data_to_add(passengers_data, "TEEN")

            self.fill_passenger_info(passenger_detail_box_element, passenger_data, first_name_box_id, last_name_box_id,
                                     is_title=True, dob_box_id=None)
            self.teen += 1

        elif infant_passenger in passenger_detail_box_info:
            first_name_box_id = IDS['INF_FN_BOX'].format(self.infant)
            last_name_box_id = IDS['INF_LN_BOX'].format(self.infant)
            dob_box_id = IDS['INF_DOB_BOX'].format(self.infant)

            passenger_data = self.get_passenger_data_to_add(passengers_data, "INF")

            self.fill_passenger_info(passenger_detail_box_element, passenger_data, first_name_box_id, last_name_box_id,
                                     is_title=False, dob_box_id=dob_box_id)
            self.infant += 1

        else:
            pass

    # Fill passenger info
    def fill_passenger_info(self, passenger_detail_box_element, passenger_data, first_name_id, last_name_id,
                            is_title=False, dob_box_id=None):

        if is_title:
            dropdown_button = passenger_detail_box_element.find_element_by_class_name(CLASS_NAMES['DROPDOWN_BUTTON'])
            dropdown_button.click()
            dropdown_items = passenger_detail_box_element.find_elements_by_class_name(CLASS_NAMES['DROPDOWN_ITEMS'])
            for dropdown_item in dropdown_items:
                if dropdown_item.text.lower() == passenger_data["Title"].lower():
                    dropdown_item.click()
                    break

        if dob_box_id:
            dob_box_element = self.driver.find_element_by_id(dob_box_id)
            dob_box_element.clear()
            self.driver.execute_script("arguments[0].setAttribute('type', '')", dob_box_element)
            dob_box_element.send_keys(passenger_data['DOB'])

        first_name_element = self.driver.find_element_by_id(first_name_id)
        first_name_element.clear()
        first_name_element.send_keys(passenger_data['FirstName'])

        last_name_element = self.driver.find_element_by_id(last_name_id)
        last_name_element.clear()
        last_name_element.send_keys(passenger_data['LastName'])

    # Get passenger data to add into website
    def get_passenger_data_to_add(self, passengers_data, passenger_code):
        passenger_data = None

        for passenger_data in passengers_data:

            if not passenger_data["is_added"] and passenger_data["Code"] == passenger_code:
                passenger_data["is_added"] = True
                return passenger_data

        return passenger_data
