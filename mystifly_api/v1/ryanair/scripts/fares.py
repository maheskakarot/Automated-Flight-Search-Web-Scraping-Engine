from datetime import datetime
import time
from v1.ryanair.constants.xpaths import XPATHS
from v1.ryanair.constants.fares_data import (VALUE_FARE_DATA, REGULAR_FARE_DATA, PLUS_FARE_DATA,
                                          FLEXI_PLUS_FARE_DATA, FAMILY_PLUS_FARE_DATA)
from v1.ryanair.constants.css_selectors import CSS_SELECTORS
from v1.ryanair.constants.class_names import CLASS_NAMES

from utils.delete_file import delete_file_from_os
from utils.email_utils import send_email
from .common import CommonActions
from .basket import RyanAirBasket


class ScrapeFareInfo:
    def __init__(self, driver, adults, children, infants, is_return):
        self.driver = driver
        self.adults = adults
        self.children = children
        self.infants = infants
        self.is_return = is_return
        self.basket_obj = RyanAirBasket(self.driver, request_data={})
        self.common_obj = CommonActions(self.driver)

    def all_fares_data(self):
        fare_types = []

        family_plus_fare_data = flexi_plus_fare_data = {}

        value_fare_data = self.scrape_value_fare_data()

        fare_rules_items = self.driver.find_element_by_class_name(CLASS_NAMES['FARE_RULES_INFO']).text.splitlines()

        regular_fare_button_xpath = XPATHS['REGULAR_FARE_BUTTON']

        if 'Family Plus' in fare_rules_items:
            family_plus_index = fare_rules_items.index('Family Plus')
            if family_plus_index <= 15:
                regular_fare_button_xpath = XPATHS['FAMILY_PLUS_FARE_BUTTON_1']

        regular_fare_data = self.scrape_fare_data(xpath=regular_fare_button_xpath,
                                                  fare_response_data=REGULAR_FARE_DATA)
        plus_fare_data = self.scrape_plus_fare_data()

        # TODO: Need to add a regex here
        if 'Family Plus' in fare_rules_items:
            family_plus_index = fare_rules_items.index('Family Plus')

            if 15 < family_plus_index <= 25:
                family_plus_fare_button_xpath = XPATHS['FAMILY_PLUS_FARE_BUTTON_1']

            elif family_plus_index <= 15:
                family_plus_fare_button_xpath = XPATHS['REGULAR_FARE_BUTTON']

            else:
                family_plus_fare_button_xpath = XPATHS['FAMILY_PLUS_FARE_BUTTON_2']

            family_plus_fare_data = self.scrape_fare_data(xpath=family_plus_fare_button_xpath,
                                                          fare_response_data=FAMILY_PLUS_FARE_DATA)

        # TODO: Need to add a regex here
        if 'Flexi Plus' in fare_rules_items:
            flexi_plus_fare_data = self.scrape_fare_data(xpath=XPATHS['FLEXI_PLUS_FARE_BUTTON'],
                                                         fare_response_data=FLEXI_PLUS_FARE_DATA)

        # Appending data in main fare types list
        fare_types.append(value_fare_data)
        fare_types.append(regular_fare_data)
        fare_types.append(plus_fare_data)

        if len(flexi_plus_fare_data):
            fare_types.append(flexi_plus_fare_data)

        if len(family_plus_fare_data):
            fare_types.append(family_plus_fare_data)

        return fare_types

    def scrape_fare_data(self, xpath, fare_response_data):
        i = 1
        fare_data = self.driver.find_element_by_xpath(xpath).text.splitlines()

        # Expected sample list
        # ['£', '22', '.', '00', 'more', 'on each flight']
        # TODO: Need to update logic - Will add regex here
        while (len(fare_data) != 6 or len(fare_data) != 4) and i < 5:
            time.sleep(0.1)
            fare_data = self.driver.find_element_by_xpath(xpath).text.splitlines()
            i += 1

        if len(fare_data) == 4:
            fare_currency = fare_data[0]
            fare_value = "{} {} {}".format(fare_data[1], fare_data[2], fare_data[3])

        elif len(fare_data) != 6:
            # TODO: Add a alert
            return None

        else:
            fare_currency = fare_data[0]
            fare_value = "{}{}{} {} {}".format(fare_data[1], fare_data[2], fare_data[3], fare_data[4], fare_data[5])

        fare_data = fare_response_data
        fare_data['fare_currency'] = fare_currency
        fare_data['fare_value'] = fare_value

        return fare_data

    def scrape_value_fare_data(self):
        fare_data = []
        try:
            i = 1
            value_fare_data = self.driver.find_element_by_xpath(XPATHS['VALUE_FARE_BUTTON']).text.splitlines()

            # Expected sample list
            # ['Continue for', '£', '10', '.', '99']
            # TODO: Need to update logic - Will add regex here
            while (len(value_fare_data) != 5 or len(value_fare_data) != 3) and i < 6:
                time.sleep(0.5)
                value_fare_data = self.driver.find_element_by_xpath(XPATHS['VALUE_FARE_BUTTON']).text.splitlines()
                i += 1

            if len(value_fare_data) == 3:
                fare_currency = value_fare_data[1]
                fare_value = "{}".format(value_fare_data[2])

            elif len(value_fare_data) != 5:
                # TODO: Add a alert
                return None

            else:
                fare_currency = value_fare_data[1]
                fare_value = float("{}{}{}".format(value_fare_data[2], value_fare_data[3], value_fare_data[4]).replace(',', ''))

            # TODO: Need to add an alert when fare_value is zero
            fare_data = VALUE_FARE_DATA
            fare_data['fare_currency'] = fare_currency
            fare_data['fare_value'] = fare_value
            fare_data['data_mismatch'] = False

            fare_breakdown = self.fare_breakdown()
            fare_data["fare_breakdown"] = fare_breakdown

            print(fare_value, fare_breakdown["total_amount_to_pay"]["value"])
            if str(fare_value) != str(fare_breakdown["total_amount_to_pay"]["value"]):
                message = "Data\n" \
                          "Value Fare - {}\n" \
                          "Cart Fare - {}".format(fare_data, fare_breakdown["total_amount_to_pay"]["value"])

                fare_data['data_mismatch'] = True
                file_name = f"{datetime.now()}.png"
                self.driver.save_screenshot(file_name)
                email_list = ["sahilkanger21@gmail.com", "giri.p@mystifly.com", "vimalm@mystifly.com"]

                send_email(f"Value Fare price mismatch", message, file_name, email_list)
                delete_file_from_os(file_name)

        except Exception as ex:
            # TODO: Add alert here
            print(ex)

        return fare_data

    def scrape_plus_fare_data(self):
        i = 1
        fare_data = self.driver.find_element_by_css_selector(CSS_SELECTORS['PLUS_FARE_BUTTON']).text.splitlines()

        # Expected sample list
        # ['£', '22', '.', '00', 'more', 'on each flight']
        # TODO: Need to update logic - Will add regex here
        while (len(fare_data) != 6 or len(fare_data) != 4) and i < 5:
            time.sleep(0.1)
            fare_data = self.driver.find_element_by_css_selector(CSS_SELECTORS['PLUS_FARE_BUTTON']).text.splitlines()
            i += 1

        if len(fare_data) == 4:
            fare_currency = fare_data[0]
            fare_value = "{} {} {}".format(fare_data[1], fare_data[2], fare_data[3])

        elif len(fare_data) != 6:
            # TODO: Add a alert
            return None

        else:
            fare_currency = fare_data[0]
            fare_value = "{}{}{} {} {}".format(fare_data[1], fare_data[2], fare_data[3], fare_data[4], fare_data[5])

        fare_data = PLUS_FARE_DATA
        fare_data['fare_currency'] = fare_currency
        fare_data['fare_value'] = fare_value

        return fare_data

    def fare_breakdown(self):
        fare_breakdown = {}

        # Click on cart button to view fare breakdown
        self.common_obj.click_on_cart_button()

        basket_data = self.basket_obj.scrape_basket_items(fare_type="VF")

        fare_breakdown["departure_flight_info"] = {}
        fare_breakdown["arrival_flight_info"] = {}

        fare_breakdown["departure_flight_info"]["seats_info"] = basket_data["departure_items_info"]
        fare_breakdown["departure_flight_info"]["tax_items_info"] = basket_data["departure_tax_items_info"]
        fare_breakdown["departure_flight_info"]["discounts"] = basket_data["departure_discount_items_info"]
        fare_breakdown["arrival_flight_info"]["seats_info"] = basket_data["arrival_items_info"]
        fare_breakdown["arrival_flight_info"]["tax_items_info"] = basket_data["arrival_tax_items_info"]
        fare_breakdown["arrival_flight_info"]["discounts"] = basket_data["arrival_discount_items_info"]

        total_amount_to_pay = self.basket_obj.scrape_total_amount_to_pay()
        fare_breakdown['total_amount_to_pay'] = total_amount_to_pay

        # Close the cart menu
        self.common_obj.click_on_cart_button(sleep=False)

        return fare_breakdown
