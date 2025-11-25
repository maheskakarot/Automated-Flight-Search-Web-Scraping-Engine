import time
from v1.ryanair.scripts.flight_extras import FlightExtras
from v1.ryanair.scripts.payment import Payment
from v1.ryanair.helpers.webdriver import change_driver_tab
from .seats_selection import SeatSelection
from v1.ryanair.constants.xpaths import XPATHS
from .common import CommonActions
from .popups import HandlePopups
from .fast_track import FastTrack
from .booking import Booking
from .baggages import Baggages
from .reprice_validation import RepriceValidation
from .search_flights import SearchFlightAutomation


class RyanairWebsiteAutomation:
    def __init__(self, driver, booking_request):
        self.driver = driver
        self.booking_request = booking_request
        self.booking_obj = Booking(self.driver, self.booking_request)
        self.handle_popups_obj = HandlePopups(self.driver, self.booking_request)
        self.flight_extras_obj = FlightExtras(self.driver, self.booking_request)
        self.common_actions_obj = CommonActions(self.driver)
        self.payment_obj = Payment(self.driver, self.booking_request)
        self.fast_track_instance = FastTrack(self.driver, self.booking_request)
        self.baggages_instance = Baggages(self.driver, self.booking_request)

    def search_flights(self, url):
        if self.booking_request["is_driver_reused"]:
            change_driver_tab(self.driver, self.booking_request["last_history_obj"], url)

        else:
            self.driver.get(url)

        if not self.booking_request.get('is_driver_reused'):
            self.common_actions_obj.accept_cookies()

        search_flight_automation_obj = SearchFlightAutomation(self.driver, self.booking_request)

        search_flight_automation_obj.sort_flights("Lowest Price")

        if self.booking_request.get('isReturn'):
            flights_data, message = search_flight_automation_obj \
                .return_trip_flights(self.booking_request.get('page'),
                                     self.booking_request.get('pageSize'),
                                     self.booking_request.get('isPaginated'))

        else:
            flights_data, message = search_flight_automation_obj.one_way_trip_flights(
                self.booking_request.get('page'),
                self.booking_request.get('pageSize'),
                self.booking_request.get('isPaginated')
            )

        return flights_data, message

    def reprice_validation(self):
        response_data, is_verified = RepriceValidation(self.driver, self.booking_request).reprice_validation()
        return response_data, is_verified

    def initiate_booking(self, is_driver_reused, subscriber, user_last_screen):
        self.common_actions_obj.keep_session_alive()
        response_data, is_initiated = self.booking_obj.initiate_booking(
            is_driver_reused, subscriber,
            user_last_screen, request_data=self.booking_request
        )
        return response_data, is_initiated

    def seat_selection(self, subscriber):
        self.common_actions_obj.keep_session_alive()
        # seats_header_element = self.driver.find_element_by_xpath(XPATHS['SEATS_HEADER'])
        # self.common_actions_obj.scroll_to_element(seats_header_element)
        request_id_items = self.booking_request["ResultId"].split("-")
        ContinueWithoutSeatsSelection = self.booking_request.get("ContinueWithoutSeatsSelection", None)
        fare_type = request_id_items[-1]
        seat_map = any_warning = warning_title = warning_body = None

        if ContinueWithoutSeatsSelection:
            SeatSelection(self.driver, self.booking_request).continue_without_a_seat()
            is_selected = True
        elif len(request_id_items) == 4:
            is_selected, seat_map, any_warning, warning_title, warning_body = self.booking_obj.one_way_seat_selection(
                subscriber, fare_type)

        else:
            is_selected, seat_map, any_warning, warning_title, warning_body = self.booking_obj.return_trip_seat_selection(
                fare_type)

        return is_selected, seat_map, any_warning, warning_title, warning_body

    def baggages_selection(self, is_driver_reused):
        self.common_actions_obj.keep_session_alive()
        response_data = {'CartItems': {}}
        request_id_items = self.booking_request["ResultId"].split("-")
        is_return_trip = True

        fare_type = request_id_items[-1]
        if len(request_id_items) == 4:
            is_return_trip = False

        self.booking_obj.baggages_selection(fare_type, is_return_trip)

        time.sleep(2)
        response_data = self.common_actions_obj.scrape_cart_items(is_return_trip, fare_type, response_data)

        return response_data

    def retrieve_fast_track_info(self):
        self.common_actions_obj.keep_session_alive()
        fast_track_info = self.fast_track_instance.retrieve_fast_track_info()

        return fast_track_info

    def add_fast_track_to_flights(self):
        self.common_actions_obj.keep_session_alive()
        response_data = {'CartItems': {}}
        request_id_items = self.booking_request["ResultId"].split("-")
        is_return_trip = True

        fare_type = request_id_items[-1]
        if len(request_id_items) == 4:
            is_return_trip = False

        self.fast_track_instance.add_fastrack()

        time.sleep(2)
        response_data = self.common_actions_obj.scrape_cart_items(is_return_trip, fare_type, response_data)
        self.flight_extras_obj.airport_and_trip()

        self.flight_extras_obj.transport()

        self.common_actions_obj.click_on_checkout_button()
        return response_data

    def complete_payment(self):
        is_payment_complete, reservation_number, errors, error_title, error_content = self.payment_obj.complete_payment()
        return is_payment_complete, reservation_number, errors, error_title, error_content

    def scrape_baggages_data(self):
        self.common_actions_obj.keep_session_alive()
        data = self.baggages_instance.scrape_bags_data()

        return data

    def select_baggages(self):
        self.common_actions_obj.keep_session_alive()
        bags_header_element = self.driver.find_element_by_xpath(XPATHS['BAGS_HEADER'])
        self.common_actions_obj.scroll_to_element(bags_header_element)
        self.common_actions_obj.close_baggages_warning_box()
        self.baggages_instance.select_baggages()

        return None
