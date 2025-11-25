import copy
import time
from datetime import datetime
from v1.ryanair.constants.xpaths import XPATHS
from v1.ryanair.constants.class_names import CLASS_NAMES
from .common import CommonActions
from .popups import HandlePopups
from .seat_map import SeatMap


class SeatSelection():
    def __init__(self, driver, booking_request):
        self.driver = driver
        self.booking_request = booking_request
        self.BABY_ICON_ID = "glyphs/baby"
        self.common_objs = CommonActions(self.driver)
        self.handle_popups_obj = HandlePopups(self.driver, request_data=self.booking_request)

    def continue_without_a_seat(self):
        self.driver.find_element_by_xpath(XPATHS['SELECT_SEATS_LATER']).click()
        self.driver.find_element_by_xpath(XPATHS['CONTINUE_WITHOUT_A_SEAT']).click()

    def prepare_seat_map(self, infants_included=True):
        seat_map = {}

        all_extra_leg_seats = self.driver.find_elements_by_class_name(CLASS_NAMES['EXTRA_LEGROOM_SEATS'])
        all_priority_seats = self.driver.find_elements_by_class_name(CLASS_NAMES['PRIORITY_SEATS'])
        all_standard_seats = self.driver.find_elements_by_class_name(CLASS_NAMES['STANDARD_SEATS'])
        all_unavailable_seats = self.driver.find_elements_by_class_name(CLASS_NAMES['UNAVAILABLE_SEAT'])

        self.driver.implicitly_wait(0)

        all_extra_leg_seats, all_extra_leg_infants_seats = self.get_seat_numbers(all_extra_leg_seats, infants_included)
        all_priority_seats, all_priority_infants_seats = self.get_seat_numbers(all_priority_seats, infants_included)
        all_standard_seats, all_standard_infants_seats = self.get_seat_numbers(all_standard_seats, infants_included)
        all_unavailable_seats, all_unavailable_infants_seats = self.get_seat_numbers(all_unavailable_seats, False)

        seat_pricing = SeatMap(self.driver).get_seat_map()

        extra_leg_seats_price_map = self.create_price_based_seat_group(all_extra_leg_seats, seat_pricing)
        extra_leg_infants_price_map = self.create_price_based_seat_group(all_extra_leg_infants_seats, seat_pricing)

        seat_map["ExtraLegroomSeatsInfo"] = {
            'SeatType': 'ExtraLegroom',
            'AvailableSeats': [extra_leg_seats_price_map[seat] for seat in extra_leg_seats_price_map],
            'InfantsSeats': [extra_leg_infants_price_map[seat] for seat in extra_leg_infants_price_map],
        }

        priority_seats_pricing_map = self.create_price_based_seat_group(all_priority_seats, seat_pricing)
        priority_infants_seats_pricing_map = self.create_price_based_seat_group(all_priority_infants_seats,
                                                                                seat_pricing)

        seat_map["FrontSeatsInfo"] = {
            'SeatType': 'Front',
            'AvailableSeats': [priority_seats_pricing_map[seat] for seat in priority_seats_pricing_map],
            'InfantsSeats': [priority_infants_seats_pricing_map[seat] for seat in priority_infants_seats_pricing_map],
        }

        standard_seats_pricing_map = self.create_price_based_seat_group(all_standard_seats, seat_pricing)
        standard_infants_seats_pricing_map = self.create_price_based_seat_group(all_standard_infants_seats,
                                                                                seat_pricing)
        seat_map["StandardSeatsInfo"] = {
            'SeatType': 'Standard',
            'AvailableSeats': [standard_seats_pricing_map[seat] for seat in standard_seats_pricing_map],
            'InfantsSeats': [standard_infants_seats_pricing_map[seat] for seat in standard_infants_seats_pricing_map],
        }

        seat_map["UnavailableSeatsInfo"] = all_unavailable_seats

        self.driver.implicitly_wait(10)

        seat_map = copy.deepcopy(seat_map)

        return seat_map

    def get_seat_numbers(self, seats, infants_included):
        all_seats = []
        all_infant_seats = []

        for seat in seats:
            seat_number = seat.get_attribute('id').split("-")[1]
            seat_number = self.update_seat_number(seat_number)
            all_seats.append(seat_number)

            if infants_included:
                icons = seat.find_elements_by_class_name(CLASS_NAMES['SEAT_ICON'])
                if icons:
                    if icons[0].get_attribute('iconid') == self.BABY_ICON_ID:
                        all_infant_seats.append(seat_number)

        return all_seats, all_infant_seats

    def update_seat_number(self, seat_number):
        if 'A' in seat_number:
            seat_number += "(W)"

        elif 'B' in seat_number:
            seat_number += "(M)"

        elif 'C' in seat_number:
            seat_number += "(A)"

        elif 'D' in seat_number:
            seat_number += "(A)"

        elif 'E' in seat_number:
            seat_number += "(M)"

        elif 'F' in seat_number:
            seat_number += "(W)"

        return seat_number

    def scrap_passengers_info(self):
        passengers_list = []

        seat_maps = {
            'Infant': None,
            'Child': None,
            'Adult/Teen': None,
        }
        passengers_elements = self.driver.find_elements_by_class_name(CLASS_NAMES['PASSENGERS_INFO'])

        for passenger_element in passengers_elements:
            passenger_element_list = passenger_element.text.splitlines()

            seat_type = passenger_element_list[-1]

            if seat_type == "Select your seat" or seat_type == "Or Random Seat Allocation":
                seat_type = "Adult/Teen"

            if not seat_maps.get(seat_type, None):
                passenger_element.click()
                seat_maps[seat_type] = self.prepare_seat_map()

            passengers_list.append({
                'Name': passenger_element_list[1],
                'SeatType': seat_type
            })

        passengers_elements[0].click()

        return passengers_list, seat_maps

    def check_seat_availability(self, passengers_seats_data):

        for passengers_seat_data in passengers_seats_data:
            target_seat_number = passengers_seat_data['SeatNumber']
            target_seat_type = passengers_seat_data['SeatType']
            is_selected, warning_title, warning_body = self.select_single_seat(target_seat_number, target_seat_type)

            if not is_selected:
                return is_selected, warning_title, warning_body

        return True, None, None

    def select_single_seat(self, target_seat_number, target_seat_type):
        seat_class_map = {
            'ExtraLegroom': 'EXTRA_LEGROOM_SEATS',
            'Front': 'PRIORITY_SEATS',
            'Standard': 'STANDARD_SEATS'
        }
        is_selected = False
        warning_title = warning_body = None

        if seat_class_map.get(target_seat_type, []):
            targeted_seats = self.driver.find_elements_by_class_name(CLASS_NAMES[seat_class_map.get(target_seat_type)])

        else:
            return is_selected, warning_title, warning_body

        self.driver.implicitly_wait(2)
        try:
            for seat in targeted_seats:
                seat_id = seat.get_attribute('id')

                if seat_id:
                    seat_number = seat_id.split("-")[1]
                    if seat_number == target_seat_number:
                        self.common_objs.scroll_to_element(seat)
                        seat.click()
                        warning_title, warning_body = self.handle_popups_obj.selected_wrong_infant_seat()

                        if warning_body or warning_body:
                            return is_selected, warning_title, warning_body

                        is_selected = True
                        break
        except Exception as ex:
            print(ex)

        self.driver.implicitly_wait(10)

        return is_selected, warning_title, warning_body

    def check_warnings(self):
        any_warning = False
        warning_title = warning_body = None

        warning_title_obj = self.driver.find_elements_by_class_name(CLASS_NAMES['WARNING_TITLE'])

        if len(warning_title_obj) == 1:
            any_warning = True
            warning_title = warning_title_obj[0].text
            warning_body = self.driver.find_element_by_class_name(CLASS_NAMES['WARNING_BODY']).text
            self.click_on_change_seat_button()

        return any_warning, warning_title, warning_body

    def click_on_change_seat_button(self):
        self.driver.find_element_by_class_name(CLASS_NAMES['FAMILY_SEATING_CTA_BTN']).click()

    def create_price_based_seat_group(self, seat_list, seat_pricing):

        seat_value_dic = {}

        for seat in seat_list:
            pricing = seat_pricing[seat]['value']
            currency = seat_pricing[seat]['currency']
            if pricing in seat_value_dic:
                seat_value_dic[pricing]['seats'].append(seat)
            else:
                seat_value_dic[pricing] = {
                    "seats": [seat],
                    "value": pricing,
                    "currency": currency
                }
        return seat_value_dic

    def change_journey_tab(self):
        journey_tab_element = self.driver.find_elements_by_class_name(CLASS_NAMES['JOURNEY_TAB'])

        # Change to departure flight seat selection
        journey_tab_element[0].click()

    def release_selected_seats(self):
        selected_seats_elements = self.driver.find_elements_by_class_name(CLASS_NAMES['SELECTED_SEATS'])

        for selected_seat_element in selected_seats_elements:
            self.common_objs.scroll_to_element(selected_seat_element)
            selected_seat_element.click()
            time.sleep(0.1)
