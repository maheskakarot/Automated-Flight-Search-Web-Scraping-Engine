import os
import sys
import time
from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from v1.ryanair.constants.class_names import CLASS_NAMES
from v1.ryanair.constants.data_ref import DATA_REF
from v1.ryanair.constants.xpaths import XPATHS
from v1.ryanair.constants.css_selectors import CSS_SELECTORS
from .common import CommonActions
from selenium.webdriver.support import expected_conditions as EC


class Equipments:
    def __init__(self, driver, request_data):
        self.driver = driver
        self.request_data = request_data
        self.departure_flight_type = "Departure"
        self.arrival_flight_type = "Arrival"
        self.common_actions_obj = CommonActions(self.driver)

    def expand_all_dropdown(self):
        count = 0
        while count <= 3:
            expanded_button = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['EXPANDABLE_ICON'])

            for each in expanded_button:
                class_name = each.get_attribute('class').lower()
                if CLASS_NAMES['ICON_OPEN_BUTTON'] in class_name:
                    continue
                try:
                    each.click()
                except Exception as e:
                    pass

            count += 1

    @staticmethod
    def scrap_passenger_details(passengers_list):
        passengers = []
        for each in passengers_list:
            name = each.find_element(By.CLASS_NAME, CLASS_NAMES['PASSENGER_NAME_DIV']).text

            price = each.find_element(By.CLASS_NAME, CLASS_NAMES['PRICE']).text
            price_list = price.split('\n')

            if len(price_list) == 4:
                price_value = price_list[1] + price_list[2] + price_list[3]
                currency = price_list[0]
            else:
                currency = price_list[0]
                price_value = price_list[1]

            passengers.append(
                {
                    'Name': name,
                    'PriceInfo': {
                        'Currency': currency,
                        'Value': price_value
                    },
                }
            )
        return passengers

    def scrap_equipment_details(self, equipment_div):

        title = equipment_div.find_element(By.CLASS_NAME, CLASS_NAMES['TITLE']).text
        try:
            self.common_actions_obj.scroll_to_element(equipment_div)
            toggle_btns = equipment_div.find_element_by_class_name(CLASS_NAMES['TOGGLE_BTN_BAR'])
            toggle_btns.click()
            time.sleep(0.2)
        except Exception as e:

            pass
        try:
            alert = equipment_div.find_element(By.CLASS_NAME, CLASS_NAMES['ALERT']).text
        except NoSuchElementException as e:
            alert = None

        title_list = title.split('\n')
        if len(title_list) == 2:
            title = title_list[0]
            alert = title_list[1]

        wrapper_class = equipment_div.find_elements(By.CLASS_NAME, 'wrapper')
        passengers_list = equipment_div.find_elements(By.CLASS_NAME, CLASS_NAMES['PASSENGER_ROW'])
        passengers = {}
        if len(wrapper_class) == 2:
            passenger_list_length = len(passengers_list)

            passengers['DepartureFlight'] = {
                'Title': wrapper_class[0].text,
                'Passengers': self.scrap_passenger_details(passengers_list[:passenger_list_length // 2])
            }
            passengers['ArrivalFlight'] = {
                'Title': wrapper_class[1].text,
                'Passengers': self.scrap_passenger_details(passengers_list[passenger_list_length // 2:])
            }
        elif len(wrapper_class) == 1:
            passengers['DepartureFlight'] = {
                'Title': wrapper_class[0].text,
                'Passengers': self.scrap_passenger_details(passengers_list)
            }
            passengers['ArrivalFlight'] = None

        return {
            'Name': title,
            'Alert': alert,
            'SubCategory': None,
            'PassengersInfo': passengers
        }

    def retrieve_equipment_details(self):
        self.driver.implicitly_wait(0.2)
        self.expand_all_dropdown()

        equipments = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['EQUIPMENT'])
        details = []
        if len(equipments) == 3:
            sports_div = equipments[0]
            musical_div = equipments[1]
            baby_div = equipments[2]

            for each_section in [musical_div, baby_div]:
                details.append(self.scrap_equipment_details(each_section))

            sub_category = []
            # sports div
            sports_section = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['EXPANSION_PANEL'])

            for each_section in sports_section:
                sub_category.append(self.scrap_equipment_details(each_section))

            details.append({
                'Name': 'Sports Equipment',
                'SubCategory': sub_category,
                'Alert': None,
                'PassengersInfo': None
            })

        return details

    def click_increment_button(self, row_element, quantity):

        self.common_actions_obj.scroll_to_element(row_element)
        current_value = int(row_element.find_element_by_class_name(CLASS_NAMES['COUNTER_VALUE']).text)
        if current_value == quantity:
            return None

        while current_value != quantity:

            counter_btns = row_element.find_elements_by_class_name(CLASS_NAMES['COUNTER_BTN'])
            for counter_btn in counter_btns:
                data_ref = counter_btn.get_attribute("data-ref")
                if data_ref == DATA_REF['INCREMENT_COUNTER']:
                    counter_btn.click()

            time.sleep(1.5)
            current_value = int(row_element.find_element_by_class_name(CLASS_NAMES['COUNTER_VALUE']).text)

        return None

    def decide_div_selection(self, equipment_name):
        equipments = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['EQUIPMENT'])
        if len(equipments) == 3:
            sports_div = equipments[0]
            musical_div = equipments[1]
            baby_div = equipments[2]

            sports_section = self.driver.find_elements(By.CLASS_NAME, 'expansion-panel')
            bike_section = sports_section[0]
            golf_section = sports_section[1]
            ski_section = sports_section[2]
            large_section = sports_section[3]
            other_section = sports_section[4]

        if 'musical' in equipment_name.lower() or 'music' in equipment_name.lower():
            selected_equipment = musical_div

        elif 'baby' in equipment_name.lower():
            selected_equipment = baby_div
        elif 'bike' in equipment_name.lower():
            selected_equipment = bike_section
        elif 'golf' in equipment_name.lower():
            selected_equipment = golf_section
        elif 'ski' in equipment_name.lower():
            selected_equipment = ski_section
        elif 'large' in equipment_name.lower():
            selected_equipment = large_section
        elif 'other' in equipment_name.lower():
            selected_equipment = other_section

        return selected_equipment

    def make_equipment_selection(self, equipment_name, passenger_list):
        self.driver.implicitly_wait(0.2)
        if ('ArrivalFlight' not in passenger_list) and ('DepartureFlight' not in passenger_list):
            return -1

        arrival_flight_passenger_list = passenger_list['ArrivalFlight']
        departure_flight_passenger_list = passenger_list['DepartureFlight']

        for passenger in departure_flight_passenger_list:

            target_passenger_name = passenger['Name']
            count = passenger['Count']
            selected_equipment = self.decide_div_selection(equipment_name)

            total_passengers_list = selected_equipment.find_elements(By.CLASS_NAME, CLASS_NAMES['PASSENGER_ROW'])
            total_length = len(total_passengers_list)

            toggle_btns = selected_equipment.find_elements_by_class_name(CLASS_NAMES['TOGGLE_BTN_BAR'])

            if len(toggle_btns) == 0:
                passengers_list = total_passengers_list
            else:
                passengers_list = total_passengers_list[:total_length // 2]

            for each in passengers_list:
                name = each.find_element(By.CLASS_NAME, CLASS_NAMES['PASSENGER_NAME_DIV']).text
                if target_passenger_name.lower() in name.lower():
                    if count != 0:
                        self.click_increment_button(each, count)
                    break

        for passenger in arrival_flight_passenger_list:

            target_passenger_name = passenger['Name']
            count = passenger['Count']
            selected_equipment = self.decide_div_selection(equipment_name)
            total_passengers_list = selected_equipment.find_elements(By.CLASS_NAME, CLASS_NAMES['PASSENGER_ROW'])
            total_length = len(total_passengers_list)

            passengers_list = total_passengers_list[total_length // 2:]

            for each in passengers_list:
                name = each.find_element(By.CLASS_NAME, CLASS_NAMES['PASSENGER_NAME_DIV']).text

                if target_passenger_name.lower() in name.lower():
                    if count != 0:
                        self.click_increment_button(each, count)
                    break

    def select_equipments(self):
        is_return_type = False
        result_id = self.request_data.get("ResultId")
        result_id_items = result_id.split("-")

        if len(result_id_items) == 6:
            is_return_type = True

        equipments_data = self.request_data.get("EquipmentsData")

        for equipment_data in equipments_data:
            self.select_single_equipment(equipment_data, is_return_type)

    def select_single_equipment(self, equipment_data, is_return_type):
        name = equipment_data.get("Name")
        self.expand_all_equipments()
        target_equipment_element = self.get_equipment_section_element(name)

        departure_flight_data = equipment_data.get("DepartureFlightData", [])
        arrival_flight_data = equipment_data.get("ArrivalFlightData", [])

        if departure_flight_data:
            self.select_flight_wise_equipments(departure_flight_data, self.departure_flight_type, is_return_type,
                                               name, target_equipment_element)

        if arrival_flight_data:
            self.select_flight_wise_equipments(arrival_flight_data, self.arrival_flight_type, is_return_type,
                                               name, target_equipment_element)

    def select_flight_wise_equipments(self, flight_data, flight_type, is_return_type, equipment_name,
                                      target_equipment_element):
        sports_equipment_position = {
            "bike": 0,
            "golf": 1,
            "ski": 2,
            "large sports": 3,
            "other sports": 4,
        }

        if equipment_name.lower() not in ["music equipment", "baby equipment"]:
            wait = WebDriverWait(self.driver, 10)
            print('yes')
            self.driver.find_element(By.XPATH, XPATHS['EXPAND_SPORTS_EQUIPMENT'].format(sports_equipment_position[equipment_name.lower()]+1)).click()
            print('no')
            sports_equipment_position = sports_equipment_position[equipment_name.lower()]
            target_equipment_element = target_equipment_element.find_elements_by_css_selector(
                CSS_SELECTORS['SPORTS_EQUIPMENT'])[sports_equipment_position]

        for data in flight_data["PassengersInfo"]:
            passenger_name = data["Name"]
            quantity = data["Quantity"]

            if quantity:
                self.select_target_quantity(target_equipment_element, flight_type, is_return_type,
                                            passenger_name, quantity)

    def get_target_row_element(self, target_equipment_element, flight_type, is_return_type, passenger_name):
        target_row_element = None

        passengers_row_elements = target_equipment_element.find_elements_by_class_name(CLASS_NAMES['PASSENGER_ROW'])

        if flight_type == self.departure_flight_type and is_return_type:
            passengers_row_elements = passengers_row_elements[0: int(len(passengers_row_elements) / 2)]

        elif flight_type == self.arrival_flight_type and is_return_type:
            passengers_row_elements = passengers_row_elements[
                                      int(len(passengers_row_elements) / 2): len(passengers_row_elements)]

        for passengers_row_element in passengers_row_elements:
            if passenger_name.lower() in passengers_row_element.text.splitlines()[1].lower():
                target_row_element = passengers_row_element
                break

        return target_row_element

    def get_equipment_section_element(self, equipment_name):

        if "music" in equipment_name.lower():
            position = 2

        elif "baby" in equipment_name.lower():
            position = 3

        else:
            position = 1

        xpath = XPATHS['EQUIPMENT'].format(position)
        element = self.driver.find_element_by_xpath(xpath)

        return element

    def select_target_quantity(self, target_equipment_element, flight_type, is_return_type, passenger_name, quantity):
        row_element = self.get_target_row_element(target_equipment_element, flight_type,
                                                  is_return_type, passenger_name)

        self.common_actions_obj.scroll_to_element(row_element)
        # current_value = int(row_element.find_element_by_class_name(CLASS_NAMES['COUNTER_VALUE']).text)
        current_value = int(WebDriverWait(row_element, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, CLASS_NAMES['COUNTER_VALUE']))).text)

        print(current_value)

        if current_value == quantity:
            return None

        index = 0
        while current_value != quantity and index < quantity:

            counter_btns = row_element.find_elements_by_class_name(CLASS_NAMES['COUNTER_BTN'])
            for counter_btn in counter_btns:
                data_ref = counter_btn.get_attribute("data-ref")
                if data_ref == DATA_REF['INCREMENT_COUNTER']:
                    counter_btn.click()

            time.sleep(1.5)
            try:
                current_value = int(WebDriverWait(row_element, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, CLASS_NAMES['COUNTER_VALUE']))).text)

            except Exception as ex:
                print(ex)
                row_element = self.get_target_row_element(target_equipment_element, flight_type,
                                                          is_return_type, passenger_name)
                current_value = int(WebDriverWait(row_element, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, CLASS_NAMES['COUNTER_VALUE']))).text)

            index += 1

        return None

    def click_on_increment_btn(self, row_element, quantity):
        self.common_actions_obj.scroll_to_element(row_element)
        current_value = int(row_element.find_element_by_class_name(CLASS_NAMES['COUNTER_VALUE']).text)
        if current_value == quantity:
            return None

        while current_value != quantity and current_value < quantity:

            try:
                current_value = int(row_element.find_element_by_class_name(CLASS_NAMES['COUNTER_VALUE']).text)

                if current_value >= quantity:
                    break
                counter_btns = row_element.find_elements_by_class_name(CLASS_NAMES['COUNTER_BTN'])
                for counter_btn in counter_btns:
                    data_ref = counter_btn.get_attribute("data-ref")
                    if data_ref == DATA_REF['INCREMENT_COUNTER']:
                        counter_btn.click()

                time.sleep(1.5)
                current_value = int(row_element.find_element_by_class_name(CLASS_NAMES['COUNTER_VALUE']).text)

            except Exception as ex:
                print("Error - 360")
        return None

    def expand_all_equipments(self):
        wait = WebDriverWait(self.driver, 10)
        expand_equipments_button = wait.until(EC.element_to_be_clickable((By.XPATH, XPATHS['EXPAND_EQUIPMENTS'])))
        expand_equipments_button.click()

        for i in range(1,4):
            expand_sub_equipment = wait.until(EC.element_to_be_clickable((By.XPATH, XPATHS['EXPAND_SUB_EQUIPMENT'].format(i))))
            expand_sub_equipment.click()
            time.sleep(1)
