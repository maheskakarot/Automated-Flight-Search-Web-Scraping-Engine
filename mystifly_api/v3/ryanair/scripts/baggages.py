import time
from v1.ryanair.constants.class_names import CLASS_NAMES
from v1.ryanair.constants.data_ref import DATA_REF
from v1.ryanair.constants.css_selectors import CSS_SELECTORS
from v1.ryanair.constants.fares_data import FARE_TYPE_BUTTON_CODES
from v1.ryanair.constants.data_at import DATA_AT
from .common import CommonActions


class Baggages():
    def __init__(self, driver, request_data):
        self.driver = driver
        self.request_data = request_data
        self.cabin_section_type = "CabinBags"
        self.checkin_section_type = "CheckInBags"
        self.departure_flight_type = "Departure"
        self.arrival_flight_type = "Arrival"
        self.small_bag = "1 Small Bag only"
        self.priority_bag = "Priority & 2 Cabin Bags"
        self.ten_kg_check_in_bag = "10kg Check-in Bag"
        self.twenty_kg_check_in_bag = "20kg Check-in Bag"
        self.common_actions_obj = CommonActions(self.driver)

    def select_included_baggages(self):
        try:
            radio_btn = self.driver.find_elements_by_class_name(CLASS_NAMES['RADIO_BTN'])[0]
            self.common_actions_obj.scroll_to_element(radio_btn)
            radio_btn.click()
        except Exception as ex:
            print("select_included_baggages 1 - ", ex)

    def scrape_bags_data(self):
        result_id = self.request_data.get('ResultId')
        result_id_items = result_id.split("-")
        fare_type = result_id_items[-1]

        cabin_bags_element = check_in_bags_element = None

        if len(result_id_items) == 6:
            # Click on all toggle buttons to unlock hidden items
            self.click_on_all_toggle_btns()

        sections = self.get_all_sections_element()

        if len(sections) == 4:
            cabin_bags_element = sections[0]
            check_in_bags_element = sections[1]

            departure_flight_title = self.scrape_flight_title(self.get_target_div_element(
                check_in_bags_element, DATA_REF['DEPT_FLIGHT_PRODUCT']))

            arrival_flight_title = self.scrape_flight_title(self.get_target_div_element(
                check_in_bags_element, DATA_REF['ARVL_FLIGHT_PRODUCT']))

            bags_data = {
                "CabinBags": self.scrape_section_wise_data(fare_type, self.cabin_section_type, cabin_bags_element,
                                                           departure_flight_title, arrival_flight_title),

                "CheckInBags": self.scrape_section_wise_data(fare_type, self.checkin_section_type,
                                                             check_in_bags_element,
                                                             departure_flight_title, arrival_flight_title)
            }

        else:
            bags_data = {}

        return bags_data

    def get_all_sections_element(self):
        all_sections = self.driver.find_elements_by_class_name(CLASS_NAMES['BAGGAGES_SECTIONS'])
        return all_sections

    def scrape_section_wise_data(self, fare_type, section_type, target_section_element, departure_flight_title,
                                 arrival_flight_title):
        self.common_actions_obj.scroll_to_element(target_section_element)

        self.expand_icons(fare_type, section_type, target_section_element)
        self.common_actions_obj.close_small_popup_box()

        departure_flight_data = {}
        arrival_flight_data = {}

        departure_flight_element = self.get_target_div_element(
            target_section_element, DATA_REF['DISCLOSURE_DEPT_FLIGHT_PRODUCT'], DATA_REF['DEPT_FLIGHT_PRODUCT'],
        )

        arrival_flight_element = self.get_target_div_element(
            target_section_element, DATA_REF['DISCLOSURE_ARVL_FLIGHT_PRODUCT'], DATA_REF['ARVL_FLIGHT_PRODUCT'],
        )

        if departure_flight_element:
            departure_flight_data = self.scrape_flight_data(fare_type, section_type, departure_flight_element,
                                                            departure_flight_title)

        if arrival_flight_element:
            arrival_flight_data = self.scrape_flight_data(fare_type, section_type, arrival_flight_element,
                                                          arrival_flight_title)

        data = {
            "DepartureFlightData": departure_flight_data,
            "ArrivalFlightData": arrival_flight_data,
        }

        return data

    def scrape_flight_data(self, fare_type, section_type, flight_element, flight_title):
        passengers_data = []
        rows = flight_element.find_elements_by_css_selector(CSS_SELECTORS['PASSENGERS_ROWS'])

        for row in rows:
            passenger_data = self.scrape_passenger_wise_data(fare_type, section_type, row)
            passengers_data.append(passenger_data)

        flight_data = {
            "Title": flight_title,
            "PassengersData": passengers_data
        }

        return flight_data

    def expand_icons(self, fare_type, section_type, section_element):
        self.driver.implicitly_wait(1)
        try:
            if section_type != self.checkin_section_type or \
                    fare_type not in [FARE_TYPE_BUTTON_CODES['FAMILY_PLUS_FARE']]:
                already_expanded_icons = section_element.find_elements_by_class_name(CLASS_NAMES['EXPANDED_ICON'])

                for icon in already_expanded_icons:
                    self.common_actions_obj.scroll_to_element(icon)
                    icon.click()

            icons = section_element.find_elements_by_css_selector(CSS_SELECTORS['ICON_TO_EXPAND'])

            for icon in icons:
                self.common_actions_obj.scroll_to_element(icon)
                icon.click()

        except Exception as ex:
            print(ex)

        self.driver.implicitly_wait(10)

    def click_on_all_toggle_btns(self):
        toggle_btns = self.driver.find_elements_by_class_name(CLASS_NAMES['TOGGLE_BTN'])[:2]

        for toggle_btn in toggle_btns:
            toggle_btn.click()
            time.sleep(0.2)

    @staticmethod
    def get_target_div_element(parent_div_element, targeted_data_ref_1, targeted_data_ref_2=None):
        target_div_element = None
        items = parent_div_element.find_elements_by_class_name(CLASS_NAMES['BASE_CLASS'])

        for item in items:
            data_ref = item.get_attribute('data-ref')

            if data_ref == targeted_data_ref_1:
                target_div_element = item
                break

        if targeted_data_ref_2 and not target_div_element:
            for item in items:
                data_ref = item.get_attribute('data-ref')

                if data_ref == targeted_data_ref_2:
                    target_div_element = item
                    break

        return target_div_element

    @staticmethod
    def scrape_flight_title(flight_element):
        title = None

        if not flight_element:
            return title

        title = flight_element.find_element_by_css_selector(CSS_SELECTORS['FLIGHT_TITLE']).text

        return title

    def scrape_passenger_wise_data(self, fare_type, section_type, passenger_row_element):
        products = []
        passenger_name = passenger_row_element.find_element_by_class_name(CLASS_NAMES['PAX_NAME']).text.splitlines()[1]

        if section_type == "CabinBags":
            product_2 = passenger_row_element.find_elements_by_class_name("card__item--product")[1]

            products.append(self.small_bag_data())
            products.append(self.scrape_priority_bag_data(product_2))

        else:
            product_1 = passenger_row_element.find_element_by_class_name("ten-kg")
            product_2 = passenger_row_element.find_element_by_class_name("twenty-kg")
            products = [self.ten_kg_bag_data(fare_type, product_1),
                        self.twenty_kg_bag_data(fare_type, product_2)]

        data = {
            "PassengerName": passenger_name,
            "ProductsInfo": products
        }

        return data

    @staticmethod
    def small_bag_data():
        data = {
            "Name": "1 Small Bag only",
            "PriceInfo": {
                "Currency": None,
                "Value": None
            },
            "Included": True,
            "Message": "Included with fare",
            "QuantityInfo": {
                "Max": 1,
                "Min": 0,
                "Current": 0
            }
        }

        return data

    def scrape_priority_bag_data(self, product_element):
        product_info = product_element.text.splitlines()
        included = False
        max_quantity = 1
        min_quantity = 0
        current_quantity = 0
        message = None

        currency = product_info[1]
        value = self.get_price_value(currency, product_info)

        product_detail_info = {
            'product_name': 'Priority & 2 Cabin Bags',
            'currency': currency,
            'value': value,
            'included': included,
            'message': message,
            'max_quantity': max_quantity,
            'min_quantity': min_quantity,
            'current_quantity': current_quantity,
        }

        data = self.prepare_product_data(product_detail_info)

        return data

    def ten_kg_bag_data(self, fare_type, product_element):
        product_info = product_element.text.splitlines()

        included = False
        currency = value = message = None
        max_quantity = 1
        min_quantity = 0
        current_quantity = 0

        if fare_type == FARE_TYPE_BUTTON_CODES['FAMILY_PLUS_FARE']:
            included = True
            message = product_info[0]
            max_quantity = 1
            min_quantity = 1
            current_quantity = 1

        else:
            currency = product_info[1]
            value = self.get_price_value(currency, product_info)

        product_detail_info = {
            'product_name': '10kg Check-in Bag',
            'currency': currency,
            'value': value,
            'included': included,
            'message': message,
            'max_quantity': max_quantity,
            'min_quantity': min_quantity,
            'current_quantity': current_quantity,
        }

        data = self.prepare_product_data(product_detail_info)

        return data

    def twenty_kg_bag_data(self, fare_type, product_element):
        product_info = product_element.text.splitlines()

        included = False
        message = None
        max_quantity = 3
        min_quantity = 0
        current_quantity = 0

        if fare_type in [FARE_TYPE_BUTTON_CODES['FAMILY_PLUS_FARE'], FARE_TYPE_BUTTON_CODES['PLUS_FARE']]:
            message = product_info[-1]
            if "included" in message.lower():
                included = True
                max_quantity = 1
                min_quantity = 1
                current_quantity = 1

            else:
                message = None

        currency = product_info[1]
        value = self.get_price_value(currency, product_info)

        product_detail_info = {
            'product_name': '20kg Check-in Bag',
            'currency': currency,
            'value': value,
            'included': included,
            'message': message,
            'max_quantity': max_quantity,
            'min_quantity': min_quantity,
            'current_quantity': current_quantity,
        }

        data = self.prepare_product_data(product_detail_info)

        return data

    @staticmethod
    def prepare_product_data(product_info):
        data = {
            "Name": product_info['product_name'],
            "PriceInfo": {
                "Currency": product_info['currency'],
                "Value": product_info['value']
            },
            "Included": product_info['included'],
            "Message": product_info['message'],
            "QuantityInfo": {
                "Max": product_info['max_quantity'],
                "Min": product_info['min_quantity'],
                "Current": product_info['current_quantity']
            }
        }
        return data

    @staticmethod
    def get_price_value(currency, price_info):
        currency_index = price_info.index(currency)

        if '.' in price_info:
            value = float("{}{}{}".format(
                price_info[currency_index + 1],
                price_info[currency_index + 2],
                price_info[currency_index + 3],
            ).replace(",", ""))

        else:
            value = float("{}".format(
                price_info[currency_index + 1]
            ).replace(",", ""))

        return value

    def select_baggages(self):
        result_id = self.request_data.get("ResultId")
        result_id_items = result_id.split("-")
        fare_type = result_id_items[-1]

        sections = self.get_all_sections_element()

        if len(sections) == 4:
            cabin_bags_element = sections[0]
            check_in_bags_element = sections[1]

            self.select_cabin_bags(cabin_bags_element, fare_type)
            self.select_check_in_bags(check_in_bags_element, fare_type)

    def select_cabin_bags(self, target_section_element, fare_type):
        departure_flight_element = self.get_target_div_element(
            target_section_element, DATA_REF['DISCLOSURE_DEPT_FLIGHT_PRODUCT'], DATA_REF['DEPT_FLIGHT_PRODUCT'],
        )

        arrival_flight_element = self.get_target_div_element(
            target_section_element, DATA_REF['DISCLOSURE_ARVL_FLIGHT_PRODUCT'], DATA_REF['ARVL_FLIGHT_PRODUCT'],
        )
        cabin_bags_data = self.request_data.get("CabinBags", {})

        if cabin_bags_data:
            departure_flight_data = cabin_bags_data.get("DepartureFlightData", {})
            arrival_flight_data = cabin_bags_data.get("ArrivalFlightData", {})

            self.select_cabin_bags_flight_wise(self.cabin_section_type, self.departure_flight_type,
                                               departure_flight_data,
                                               departure_flight_element, fare_type)
            self.select_cabin_bags_flight_wise(self.cabin_section_type, self.arrival_flight_type, arrival_flight_data,
                                               arrival_flight_element, fare_type)

    def select_cabin_bags_flight_wise(self, section_name, flight_type, flight_data, flight_element, fare_type):
        if fare_type in [FARE_TYPE_BUTTON_CODES['REGULAR_FARE'], FARE_TYPE_BUTTON_CODES['FLEXI_PLUS_FARE']]:
            return None

        if flight_data:
            products_info = flight_data.get("ProductsInfo", [])

            if products_info:
                for product_info in products_info:
                    product_name = product_info["Name"]
                    add_to_all = product_info["AddToAll"]

                    if add_to_all:
                        target_data_at = self.get_target_data_at(section_name, flight_type, product_name)
                        self.add_all_passenger_btn(target_data_at, flight_element, product_name)

                    else:
                        passengers_info = product_info.get("PassengersInfo", [])

                        for passenger_info in passengers_info:
                            passenger_name = passenger_info["Name"]
                            add_product = passenger_info["Add"]

                            if add_product:
                                self.add_cabin_bag_per_passenger(flight_element, product_name, passenger_name)

    def select_check_in_bags(self, target_section_element, fare_type):
        departure_flight_element = self.get_target_div_element(
            target_section_element, DATA_REF['DISCLOSURE_DEPT_FLIGHT_PRODUCT'], DATA_REF['DEPT_FLIGHT_PRODUCT'],
        )

        arrival_flight_element = self.get_target_div_element(
            target_section_element, DATA_REF['DISCLOSURE_ARVL_FLIGHT_PRODUCT'], DATA_REF['ARVL_FLIGHT_PRODUCT'],
        )

        check_in_bags_data = self.request_data.get("CheckInBags", {})

        if check_in_bags_data:
            departure_flight_data = check_in_bags_data.get("DepartureFlightData", {})
            arrival_flight_data = check_in_bags_data.get("ArrivalFlightData", {})

            self.select_check_in_bags_flight_wise("CheckInBags", "Departure", departure_flight_data,
                                                  departure_flight_element, fare_type)
            self.select_check_in_bags_flight_wise("CheckInBags", "Arrival", arrival_flight_data,
                                                  arrival_flight_element, fare_type)

    def select_check_in_bags_flight_wise(self, section_name, flight_type, flight_data, flight_element, fare_type):
        if flight_data:
            products_info = flight_data.get("ProductsInfo", [])

            if products_info:
                for product_info in products_info:
                    product_name = product_info["Name"]
                    add_to_all = product_info["AddToAll"]

                    if fare_type == FARE_TYPE_BUTTON_CODES[
                        "FAMILY_PLUS_FARE"] and product_name.lower() == self.ten_kg_check_in_bag.lower():
                        continue

                    if add_to_all:
                        target_data_at = self.get_target_data_at(section_name, flight_type, product_name)
                        self.add_all_passenger_btn(target_data_at, flight_element, product_name)

                    else:
                        passengers_info = product_info.get("PassengersInfo", [])

                        for passenger_info in passengers_info:
                            passenger_name = passenger_info["Name"]
                            add_product = passenger_info["Add"]
                            quantity = passenger_info["Quantity"]

                            if add_product:
                                if product_name.lower() == self.ten_kg_check_in_bag.lower():
                                    self.add_ten_kg_check_in_bag(flight_element, passenger_name)

                                else:
                                    self.add_twenty_kg_check_in_bag(flight_element, passenger_name, quantity)

    def get_target_data_at(self, section, flight_type, product_name):
        if section == self.cabin_section_type:
            if flight_type == self.departure_flight_type:
                if product_name.lower() == self.small_bag.lower():
                    data_at = DATA_AT['DEPT_SMALL_BAG']

                else:
                    data_at = DATA_AT['DEPT_PRIORITY_BAG']
            else:
                if product_name.lower() == self.small_bag.lower():
                    data_at = DATA_AT['ARVL_SMALL_BAG']

                else:
                    data_at = DATA_AT['ARVL_PRIORITY_BAG']

        else:
            if flight_type == self.departure_flight_type:
                if product_name.lower() == self.ten_kg_check_in_bag.lower():
                    data_at = DATA_AT['DEPT_SMALL_CABIN_BAG']

                else:
                    data_at = DATA_AT['DEPT_LARGE_CABIN_BAG']
            else:
                if product_name.lower() == self.ten_kg_check_in_bag.lower():
                    data_at = DATA_AT['ARVL_SMALL_CABIN_BAG']

                else:
                    data_at = DATA_AT['ARVL_LARGE_CABIN_BAG']

        return data_at

    def add_cabin_bag_per_passenger(self, flight_element, product_name, target_passenger_name):
        rows = flight_element.find_elements_by_css_selector(CSS_SELECTORS['PASSENGERS_ROWS'])

        for row in rows:
            passenger_name = row.find_element_by_class_name(CLASS_NAMES['PAX_NAME']).text.splitlines()[1]
            if target_passenger_name.lower() in passenger_name.lower():
                radio_btns = row.find_elements_by_class_name(CLASS_NAMES['RADIO_BTN'])
                if product_name.lower() == self.small_bag.lower():
                    radio_btns[0].click()
                    break

                else:
                    radio_btns[1].click()
                    break

    def add_all_passenger_btn(self, targeted_data_at, flight_element, product_name):
        is_added = False
        add_all_btns = self.driver.find_elements_by_class_name(CLASS_NAMES['ADD_TO_ALL_CTA'])

        for add_all_btn in add_all_btns:
            data_at = add_all_btn.get_attribute("data-at")

            if data_at == targeted_data_at:
                add_all_btn.click()
                is_added = True
                break

        if not is_added:
            rows = flight_element.find_elements_by_css_selector(CSS_SELECTORS['PASSENGERS_ROWS'])

            if len(rows) == 1:
                row = rows[0]

                if product_name.lower() in [self.small_bag.lower(), self.priority_bag.lower()]:
                    radio_btns = row.find_elements_by_class_name(CLASS_NAMES['RADIO_BTN'])

                    if product_name.lower() == self.small_bag.lower():
                        radio_btns[0].click()

                    else:
                        radio_btns[1].click()

                else:
                    if product_name.lower() == self.ten_kg_check_in_bag.lower():
                        add_btn = row.find_element_by_class_name(CLASS_NAMES['BAGGAGE_ADD_BTN'])
                        add_btn.click()

                    else:
                        self.increase_twenty_kg_check_in_bags(row, 1)

    @staticmethod
    def add_ten_kg_check_in_bag(flight_element, target_passenger_name):
        rows = flight_element.find_elements_by_css_selector(CSS_SELECTORS['PASSENGERS_ROWS'])

        for row in rows:
            passenger_name = row.find_element_by_class_name(CLASS_NAMES['PAX_NAME']).text.splitlines()[1]
            if target_passenger_name.lower() in passenger_name.lower():
                add_btn = row.find_element_by_class_name(CLASS_NAMES['BAGGAGE_ADD_BTN'])
                add_btn.click()
                break

    def add_twenty_kg_check_in_bag(self, flight_element, target_passenger_name, quantity):
        rows = flight_element.find_elements_by_css_selector(CSS_SELECTORS['PASSENGERS_ROWS'])

        for row in rows:
            passenger_name = row.find_element_by_class_name(CLASS_NAMES['PAX_NAME']).text.splitlines()[1]
            if target_passenger_name.lower() in passenger_name.lower():
                self.increase_twenty_kg_check_in_bags(row, quantity)
                break

    @staticmethod
    def increase_twenty_kg_check_in_bags(row_element, quantity):
        current_value = int(row_element.find_element_by_class_name(CLASS_NAMES['COUNTER_VALUE']).text)

        if current_value == quantity:
            return None

        index = 0
        while current_value != quantity and index < quantity:
            counter_btns = row_element.find_elements_by_class_name(CLASS_NAMES['COUNTER_BTN'])
            for counter_btn in counter_btns:
                data_ref = counter_btn.get_attribute("data-ref")
                if data_ref == DATA_REF['INCREMENT_COUNTER']:
                    counter_btn.click()

            current_value = int(row_element.find_element_by_class_name(CLASS_NAMES['COUNTER_VALUE']).text)
            index += 1
            time.sleep(1)

        return None
