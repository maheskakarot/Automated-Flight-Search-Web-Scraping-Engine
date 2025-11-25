import time
from v1.ryanair.scripts.reprice_validation import RepriceValidation
from v1.ryanair.scripts.passengers_detail import PassengersDetail
from .baggages import Baggages
from v1.ryanair.constants.class_names import CLASS_NAMES
from account.models import SubscriberSearchHistory
from .common import CommonActions
from .popups import HandlePopups
from .seats_selection import SeatSelection


class Booking:
    def __init__(self, driver, request_data):
        self.driver = driver
        self.request_data = request_data
        self.reprice_validation_obj = RepriceValidation(self.driver, self.request_data)
        self.common_actions_obj = CommonActions(self.driver)
        self.passenger_detail_obj = PassengersDetail(self.driver, self.request_data)
        self.seat_selection_obj = SeatSelection(self.driver, self.request_data)
        self.baggages_obj = Baggages(self.driver, self.request_data)
        self.handle_popups_obj = HandlePopups(self.driver, self.request_data)

    def initiate_booking(self, is_driver_reused, subscriber, user_last_screen):
        response_data = {}
        is_initiated = False
        is_return_trip = False

        result_id = self.request_data.get('ResultId')
        fare_details = self.request_data.get('FareDetails', None)

        if not fare_details:
            return response_data, is_initiated

        result_id_items = result_id.split("-")

        if len(result_id_items) == 4:
            departure_flight_number = result_id_items[2]
            fare_type = result_id_items[3]

            if not is_driver_reused:
                # Added sleep time to avoid scraping detection
                time.sleep(1)
                self.reprice_validation_obj.click_on_one_way_target_flight_card(departure_flight_number)

                time.sleep(1)
                self.reprice_validation_obj.click_on_target_fare_button(fare_type)
                time.sleep(1)

        elif len(result_id_items) == 6:
            is_return_trip = True
            departure_flight_number = result_id_items[2]
            arrival_flight_number = result_id_items[4]
            fare_type = result_id_items[5]

            if not is_driver_reused:
                # Added sleep time to avoid scraping detection
                time.sleep(1)
                self.reprice_validation_obj.click_on_return_trip_target_flight_card(departure_flight_number,
                                                                                    arrival_flight_number)

                time.sleep(1)
                self.reprice_validation_obj.click_on_target_fare_button(fare_type)

        else:
            return response_data, is_initiated

        self.passenger_detail_obj.fill_passengers_info()

        self.common_actions_obj.click_on_continue_flow_button()

        last_history_obj = SubscriberSearchHistory.objects.filter(subscriber=subscriber).last()

        if last_history_obj.child:
            self.handle_popups_obj.dismiss_family_seating_popup()
            time.sleep(2)

        if user_last_screen == SubscriberSearchHistory.SEAT_SELECTION_SCREEN:
            self.seat_selection_obj.change_journey_tab()
            self.seat_selection_obj.release_selected_seats()

        passengers_info, seat_maps_dict = self.seat_selection_obj.scrap_passengers_info()
        response_data['SeatMap'] = seat_maps_dict
        response_data['SelectSeatsFor'] = passengers_info

        response_data['CartItems'] = {}
        response_data = self.common_actions_obj.scrape_cart_items(is_return_trip, fare_type, response_data)

        return response_data, is_initiated

    def one_way_seat_selection(self, subscriber, fare_type):
        seat_map = None
        any_warning = False

        is_selected, warning_title, warning_body = self.seat_selection_obj.check_seat_availability(
            self.request_data["PassengersSeatsInfo"])
        if is_selected:
            self.common_actions_obj.click_on_continue_button()
            any_warning, warning_title, warning_body = self.seat_selection_obj.check_warnings()

            if not any_warning:
                self.handle_popups_obj.dismiss_crowd_popup(fare_type)

        return is_selected, seat_map, any_warning, warning_title, warning_body

    def return_trip_seat_selection(self, fare_type):
        seat_maps_dict = any_warning = passengers_info = None

        is_selected, warning_title, warning_body = self.seat_selection_obj.check_seat_availability(
            self.request_data["PassengersSeatsInfo"])

        if not is_selected:
            return is_selected, seat_maps_dict, any_warning, warning_title, warning_body

        if self.request_data["SeatSelectionFor"] == "Departure Flight":
            self.driver.find_element_by_class_name(CLASS_NAMES['NEXT_FLIGHT_BTN']).click()

            any_warning, warning_title, warning_body = self.seat_selection_obj.check_warnings()

            if any_warning:
                return is_selected, seat_maps_dict, any_warning, warning_title, warning_body

            try:
                self.driver.find_elements_by_class_name(CLASS_NAMES['PROMPT_BTN'])[0].click()
            except Exception as ex:
                print(ex)

            passengers_info, seat_maps_dict = self.seat_selection_obj.scrap_passengers_info(is_return=True)

        else:
            self.common_actions_obj.click_on_continue_button()

            any_warning, warning_title, warning_body = self.seat_selection_obj.check_warnings()

            if any_warning:
                return is_selected, seat_maps_dict, any_warning, warning_title, warning_body

            self.handle_popups_obj.dismiss_crowd_popup(fare_type)

        return is_selected, seat_maps_dict, any_warning, warning_title, warning_body

    def baggages_selection(self, fare_type, is_return_trip):
        if self.request_data.get("SelectIncludedBags", False):
            fares_with_select_included_bags = ["VF", "PF", "FMPF"]
            if fare_type in fares_with_select_included_bags:
                self.baggages_obj.select_included_baggages()

        self.common_actions_obj.click_on_continue_button()

        self.handle_popups_obj.dismiss_baggages_popup()

        time.sleep(2)

        return None
