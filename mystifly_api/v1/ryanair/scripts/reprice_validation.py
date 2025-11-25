import copy
import time
from v1.ryanair.constants.class_names import CLASS_NAMES
from v1.ryanair.constants.xpaths import XPATHS
from v1.ryanair.constants.fares_data import FARE_TYPE_BUTTON_CODES
from v1.ryanair.constants.css_selectors import CSS_SELECTORS
from v1.ryanair.constants.reprice import RETURN_TRIP_REPRICE_RESPONSE_STRUCTURE
from .common import CommonActions
from .search_flights import SearchFlightAutomation
from .basket import RyanAirBasket


class RepriceValidation:
    """
    This class contains methods related to reprice validation functionality.
    """

    def __init__(self, driver, request_data):
        self.driver = driver
        self.request_data = request_data
        self.basket_instance = RyanAirBasket(self.driver, self.request_data)
        self.common_actions = CommonActions(driver)
        self.departure_flights_list_constant = 1
        self.return_flights_list_constant = 2

    def reprice_validation(self):
        """
        :working: Deciding if user wants to do reprice validation for one-way or return trip.
        :return: Will return response for reprice validation API
        """
        response_data = {}
        is_verified = False

        time.sleep(1)
        result_id = self.request_data.get('ResultId')
        fare_details = self.request_data.get('FareDetails', None)

        if not fare_details:
            return response_data, is_verified

        result_id_items = result_id.split("-")

        if len(result_id_items) == 4:
            flight_number = result_id_items[2]
            fare_type = result_id_items[3]

            response_data = self.one_way_reprice_validation(flight_number, fare_type)

        elif len(result_id_items) == 6:
            departure_flight_number = result_id_items[2]
            arrival_flight_number = result_id_items[4]
            fare_type = result_id_items[5]

            response_data = self.return_trip_reprice_validation(departure_flight_number, arrival_flight_number,
                                                                fare_type)

        # Validate prices
        if fare_details["currency"] == response_data["total_amount_to_pay_info"]["currency"] and \
                fare_details["value"] == response_data["total_amount_to_pay_info"]["value"]:
            is_verified = True

        # Close the cart
        self.click_on_cart_button()

        return response_data, is_verified

    def one_way_reprice_validation(self, flight_number, fare_type):
        """
        :working: We are using this function to do reprice validation for one-way trips
        :param flight_number: Flight which user wants to book
        :param fare_type: This is the value of fare which user wants to select.
        :return: Will return response for one-way reprice validation API
        """

        response_data = RETURN_TRIP_REPRICE_RESPONSE_STRUCTURE
        is_clicked, flight_card_data = self.click_on_one_way_target_flight_card(flight_number)

        # Added sleep time to avoid scrapping detection. Website is blocking us from doing fast action.
        time.sleep(1)

        if is_clicked:

            if self.click_on_target_fare_button(fare_type):
                self.click_on_cart_button()

                if fare_type in [FARE_TYPE_BUTTON_CODES["PLUS_FARE"], FARE_TYPE_BUTTON_CODES["FAMILY_PLUS_FARE"],
                                 FARE_TYPE_BUTTON_CODES["FLEXI_PLUS_FARE"]]:
                    self.basket_instance.click_on_full_details_button(fare_type)

                basket_data = self.basket_instance.scrape_basket_items(fare_type)

                response_data["departure_flight_info"]["flight_info"] = flight_card_data
                response_data["departure_flight_info"]["seats_info"] = basket_data["departure_items_info"]
                response_data["departure_flight_info"]["tax_items_info"] = basket_data["departure_tax_items_info"]
                response_data["departure_flight_info"]["discounts"] = basket_data["departure_discount_items_info"]

                response_data["arrival_flight_info"]["flight_info"] = {}
                response_data["arrival_flight_info"]["seats_info"] = basket_data["arrival_items_info"]
                response_data["arrival_flight_info"]["tax_items_info"] = basket_data["arrival_tax_items_info"]
                response_data["arrival_flight_info"]["discounts"] = basket_data["arrival_discount_items_info"]
                response_data["total_amount_to_pay_info"] = self.basket_instance.scrape_total_amount_to_pay()

        else:
            print("Failed")

        return response_data

    def return_trip_reprice_validation(self, departure_flight_number, arrival_flight_number, fare_type):
        response_data = RETURN_TRIP_REPRICE_RESPONSE_STRUCTURE
        print(response_data)

        is_clicked, departure_flight_card_data, arrival_flight_card_data = self.click_on_return_trip_target_flight_card(
            departure_flight_number, arrival_flight_number
        )

        # Added sleep time to avoid scrapping detection. Website is blocking us from doing fast action.
        time.sleep(1)
        if is_clicked:
            if self.click_on_target_fare_button(fare_type):
                self.click_on_cart_button()

                if fare_type in [FARE_TYPE_BUTTON_CODES["PLUS_FARE"], FARE_TYPE_BUTTON_CODES["FAMILY_PLUS_FARE"],
                                 FARE_TYPE_BUTTON_CODES["FLEXI_PLUS_FARE"]]:
                    self.basket_instance.click_on_full_details_button(fare_type)

                time.sleep(1)
                basket_data = self.basket_instance.scrape_return_trip_basket_items(fare_type)

                response_data["departure_flight_info"]["flight_info"] = departure_flight_card_data
                response_data["departure_flight_info"]["seats_info"] = basket_data["departure_items_info"]
                response_data["departure_flight_info"]["tax_items_info"] = basket_data["departure_tax_items_info"]
                response_data["departure_flight_info"]["discounts"] = basket_data["departure_discount_items_info"]

                response_data["arrival_flight_info"]["flight_info"] = arrival_flight_card_data
                response_data["arrival_flight_info"]["seats_info"] = basket_data["arrival_items_info"]
                response_data["arrival_flight_info"]["tax_items_info"] = basket_data["arrival_tax_items_info"]
                response_data["arrival_flight_info"]["discounts"] = basket_data["arrival_discount_items_info"]

                response_data["total_amount_to_pay_info"] = self.basket_instance.scrape_total_amount_to_pay()

        print("Not clicked")

        return response_data

    def click_on_one_way_target_flight_card(self, flight_number):
        """
        :param flight_number: Flight which user wants to book
        :return: is_clicked: If we found the flight then will return True otherwise false.
        flight_card_data: If we found the flight then this variable will contain flight data.
        """
        is_clicked = False
        flight_card_data = {}

        flights_numbers = self.driver.find_elements_by_class_name(CLASS_NAMES['FLIGHT_NUMBER'])

        for result_number, flight_number_instance in enumerate(flights_numbers):
            if flight_number == flight_number_instance.text.split(" ")[1]:
                flight_card_data, result_number = SearchFlightAutomation(
                    self.driver, self.request_data).scrape_flight_card_info(
                    result_number + 1, self.departure_flights_list_constant)

                flight_number_instance.click()
                is_clicked = True
                break

        return is_clicked, flight_card_data

    def click_on_return_trip_target_flight_card(self, departure_flight_number, arrival_flight_number):
        arrival_flight_card_data = {}

        is_clicked, departure_flight_card_data = self.click_on_one_way_target_flight_card(departure_flight_number)
        time.sleep(1)
        if is_clicked:
            is_clicked = False
            flights_numbers = self.driver.find_elements_by_class_name(CLASS_NAMES['FLIGHT_NUMBER'])

            result_number = 0
            for flight_number_instance in flights_numbers:
                flight_number = flight_number_instance.text

                if not len(flight_number) or departure_flight_number == flight_number.split(" ")[1]:
                    continue

                elif arrival_flight_number == flight_number.split(" ")[1]:

                    arrival_flight_card_data, result_number = SearchFlightAutomation(
                        self.driver, self.request_data).scrape_flight_card_info(
                        result_number + 1, self.return_flights_list_constant)

                    flight_number_instance.click()
                    is_clicked = True
                    break

                result_number += 1

        return is_clicked, departure_flight_card_data, arrival_flight_card_data

    def click_on_target_fare_button(self, fare_type):
        """
        :param fare_type: This is the value of fare which user wants to select.
        :return: is_clicked: If we are able to click on request fare type button then we will return True otherwise false
        """
        is_clicked = False

        time.sleep(0.5)
        fare_rules_items = self.driver.find_element_by_class_name(CLASS_NAMES['FARE_RULES_INFO']).text.splitlines()
        print(fare_rules_items)
        if fare_type == FARE_TYPE_BUTTON_CODES['VALUE_FARE']:
            signup_button = self.driver.find_element_by_class_name(CLASS_NAMES['SIGNUP_BUTTON'])
            self.common_actions.scroll_to_element(signup_button)

            value_fare_button = self.driver.find_element_by_xpath(XPATHS['VALUE_FARE_BUTTON'])
            value_fare_button.click()

            continue_with_value_fare_button = self.driver.find_element_by_class_name(
                CLASS_NAMES['CONTINUE_WITH_VALUE_FARE_BUTTON'])

            time.sleep(0.5)
            self.common_actions.scroll_to_element(continue_with_value_fare_button)

            continue_with_value_fare_button.click()

            is_clicked = True

        elif fare_type == FARE_TYPE_BUTTON_CODES['REGULAR_FARE']:
            regular_fare_xpath_button = XPATHS['REGULAR_FARE_BUTTON']

            if 'Family Plus' in fare_rules_items:
                family_plus_index = fare_rules_items.index('Family Plus')
                if family_plus_index <= 15:
                    regular_fare_xpath_button = XPATHS['FAMILY_PLUS_FARE_BUTTON_1']

            regular_fare_button = self.driver.find_element_by_xpath(regular_fare_xpath_button)
            regular_fare_button.click()
            is_clicked = True

        elif fare_type == FARE_TYPE_BUTTON_CODES['PLUS_FARE']:
            plus_fare_button = self.driver.find_element_by_css_selector(CSS_SELECTORS['PLUS_FARE_BUTTON'])
            plus_fare_button.click()
            is_clicked = True

        elif fare_type == FARE_TYPE_BUTTON_CODES['FAMILY_PLUS_FARE']:
            fare_rules_items = self.driver.find_element_by_class_name(CLASS_NAMES['FARE_RULES_INFO']).text.splitlines()

            family_plus_index = fare_rules_items.index('Family Plus')

            # TODO: Add regex here or improve approach
            if 15 < family_plus_index <= 25:
                family_plus_button_xpath = XPATHS['FAMILY_PLUS_FARE_BUTTON_1']

            elif family_plus_index <= 15:
                family_plus_button_xpath = XPATHS['REGULAR_FARE_BUTTON']

            else:
                family_plus_button_xpath = XPATHS['FAMILY_PLUS_FARE_BUTTON_2']

            family_plus_fare_button = self.driver.find_element_by_xpath(family_plus_button_xpath)
            family_plus_fare_button.click()
            is_clicked = True

        elif fare_type == FARE_TYPE_BUTTON_CODES['FLEXI_PLUS_FARE']:
            flexi_plus_fare_button = self.driver.find_element_by_xpath(XPATHS['FLEXI_PLUS_FARE_BUTTON'])
            flexi_plus_fare_button.click()
            is_clicked = True

        return is_clicked

    def click_on_cart_button(self):
        """
        :working: We are using this function to click on cart button.
        :return: None
        """
        self.driver.find_element_by_xpath(XPATHS['CART_BUTTON']).click()
        time.sleep(2)
