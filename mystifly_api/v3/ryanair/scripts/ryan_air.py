import time
from .reprice_validation import RepriceValidation
from .search_flights import SearchFlightAutomation


class RyanairWebsiteAutomation:
    def __init__(self, booking_request):
        self.booking_request = booking_request

    def search_flights(self, url):

        search_flight_automation_obj = SearchFlightAutomation(self.booking_request)

        if self.booking_request.get('isReturn'):
            flights_data, message = search_flight_automation_obj.return_trip_flights(url)

        else:
            flights_data, message = search_flight_automation_obj.one_way_trip_flights(url)

        return flights_data, message

    def reprice_validation(self):
        is_verified, reprice_fare_info, error = RepriceValidation(self.booking_request).reprice_validation()
        return is_verified, reprice_fare_info, error
