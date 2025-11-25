from v3.ryanair.helpers.basket import create_booking, create_basket
from v3.ryanair.helpers.search import search_api_response
from .search_flights import SearchFlightAutomation


class RepriceValidation:
    """
    This class contains methods related to reprice validation functionality.
    """

    def __init__(self, request_data):
        self.request_data = request_data
        self.search_obj = SearchFlightAutomation(self.request_data)

    def reprice_validation(self):
        """
        :working: Deciding if user wants to do reprice validation for one-way or return trip.
        :return: Will return response for reprice validation API
        """
        reprice_fare_info = {}
        is_verified = False
        error = None

        result_id = self.request_data.get('ResultId')
        fare_details = self.request_data.get('FareDetails', None)

        search_url = self.request_data.get('last_search_url')

        currency, departure_flight_data, arrival_flight_data, error = search_api_response(search_url)

        if not fare_details:
            error = "FareDetails is missing."
            return is_verified, error

        result_id_items = result_id.split("-")
        fare_type = result_id_items[-1]

        if len(result_id_items) == 4:
            flight_number = result_id_items[2]

            fare_value, error = self.api_one_way_reprice_validation(departure_flight_data, flight_number)

        elif len(result_id_items) == 6:
            departure_flight_number = result_id_items[2]
            arrival_flight_number = result_id_items[4]

            fare_value, error = self.api_return_trip_reprice_validation(departure_flight_data, arrival_flight_data,
                                                                        departure_flight_number, arrival_flight_number)

        else:
            error = "ResultId is invalid"
            return is_verified, reprice_fare_info, error

        reprice_fare_info = {"currency": currency, "value": fare_value}
        print(reprice_fare_info)
        # Validate prices
        if fare_details["currency"] == currency and fare_details["value"] == fare_value:
            is_verified = True

        return is_verified, reprice_fare_info, error

    def api_one_way_reprice_validation(self, departure_flight_data, flight_number):
        """
        :param departure_flight_data:
        :working: We are using this function to do reprice validation for one-way trips
        :param flight_number: Flight which user wants to book
        :return: Will return response for one-way reprice validation API
        """

        fare_value = None
        error = None

        if departure_flight_data:
            trip_dates_data = departure_flight_data['dates']

            if len(trip_dates_data) == 5:
                target_date_data = trip_dates_data[2]

                target_data = {
                    'departure_flight_number': flight_number,
                    'departure_flight_data': target_date_data,
                    'return_flight_number': None,
                    'return_flight_data': None,
                }
                fare_value = self.search_flight_number_in_targeted_data(target_data)

            else:
                error = "5 days trip data is missing"

        return fare_value, error

    def api_return_trip_reprice_validation(self, departure_flight_data, arrival_flight_data,
                                           departure_flight_number, arrival_flight_number):
        fare_value = None
        error = None

        if departure_flight_data and arrival_flight_data:
            dept_trip_dates_data = departure_flight_data['dates']
            arrival_trip_dates_data = arrival_flight_data['dates']

            if len(dept_trip_dates_data) == 5:
                dept_target_date_data = dept_trip_dates_data[2]
                arvl_target_date_data = arrival_trip_dates_data[2]

                target_data = {
                    'departure_flight_number': departure_flight_number,
                    'departure_flight_data': dept_target_date_data,
                    'return_flight_number': arrival_flight_number,
                    'return_flight_data': arvl_target_date_data,
                }
                fare_value = self.search_flight_number_in_targeted_data(target_data)

            else:
                error = "5 days trip data is missing"

        return fare_value, error

    def search_flight_number_in_targeted_data(self, target_data):

        fare_value = None

        departure_flight_number = target_data.get('departure_flight_number', None)
        departure_flight_data = target_data.get('departure_flight_data', None)
        return_flight_number = target_data.get('return_flight_number', None)
        return_flight_data = target_data.get('return_flight_data', None)

        if departure_flight_data and return_flight_data:
            departure_flights = departure_flight_data['flights']
            return_flights = return_flight_data['flights']

            for departure_flight in departure_flights:

                if departure_flight_number == departure_flight['flightNumber'].split(" ")[1]:

                    for return_flight in return_flights:
                        if return_flight_number == return_flight['flightNumber'].split(" ")[1]:
                            departureFlightKey = departure_flight['flightKey']
                            departureFareKey = departure_flight['regularFare']['fareKey']
                            arrivalFlightKey = return_flight['flightKey']
                            arrivalFareKey = return_flight['regularFare']['fareKey']
                            basket_id = create_basket()
                            value_fare_data = self.search_obj.test_value_fare_data(
                                basketId=basket_id, constant_fields_data={},
                                is_return=True, departureFareKey=departureFareKey,
                                departureFlightKey=departureFlightKey,
                                arrivalFareKey=arrivalFareKey, arrivalFlightKey=arrivalFlightKey)
                            fare_value = round(value_fare_data["fare_value"], 2)
                            return fare_value

        else:
            departure_flights = departure_flight_data['flights']

            for departure_flight in departure_flights:

                if departure_flight_number == departure_flight['flightNumber'].split(" ")[1]:
                    basket_id = create_basket()
                    departureFlightKey = departure_flight['flightKey']
                    departureFareKey = departure_flight['regularFare']['fareKey']
                    value_fare_data = self.search_obj.test_value_fare_data(
                        basketId=basket_id, constant_fields_data={},
                        is_return=False, departureFareKey=departureFareKey, departureFlightKey=departureFlightKey)
                    fare_value = round(value_fare_data["fare_value"], 2)
                    return fare_value

        return fare_value
