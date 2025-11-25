import copy
import datetime
import logging
from v5.ryanair.helpers.search import search_api_response, get_fare_values_v4

logger = logging.getLogger(__name__)


class SearchFlightAutomation:

    def __init__(self, request_data):

        self.request_data = request_data
        self.adults = request_data.get('adults', 1)
        self.children = request_data.get('children', 0)
        self.infants = request_data.get('infants', 0)
        self.is_paginated = request_data.get('isPaginated', False)
        self.page_size = request_data.get('pageSize', 10)
        self.page = request_data.get('page', 1)

    def one_way_trip_flights(self, search_url):
        flights_data = []
        flights_data_response = {}
        total_departure_flight = 0
        message = "Request successful"

        constant_fields_data = get_fare_values_v4()

        if not constant_fields_data:
            message = "Unable to fetch constant values of value fare"
            return flights_data_response, message

        currency, departure_flight_data, arrival_flight_data, error = search_api_response(search_url)

        if departure_flight_data:
            five_dates_data = departure_flight_data['dates']

            if len(five_dates_data) == 5:
                searched_date_data = five_dates_data[2]

                departure_flights = searched_date_data['flights']

                if departure_flights:

                    departure_flights = [departure_flight for departure_flight in departure_flights if
                                         departure_flight.get('regularFare', None)]

                    # Results count
                    results_count = 0

                    total_departure_flight = len(departure_flights)
                    for departure_flight in departure_flights:

                        if self.is_paginated:
                            if results_count >= self.page * self.page_size:
                                break

                            elif results_count < (self.page - 1) * self.page_size:
                                results_count += 1
                                continue

                        flight_number = departure_flight['flightNumber']
                        flight_timings = departure_flight['segments'][0]['time']

                        value_fare_data = self.test_value_fare_data(
                            constant_fields_data=constant_fields_data,
                            currency=currency,
                            departure_fares_data=departure_flight['regularFare']['fares'],
                            return_fares_data=None
                        )

                        data = {
                            "result_id": "OW-FL1-{}".format(flight_number.split(" ")[1]),
                            "departure_flight_data": {
                                "flight_number": departure_flight['flightNumber'],
                                "flight_type": "Direct",
                                "origin_airport_name": departure_flight["segments"][0]['origin'],
                                "destination_airport_name": departure_flight["segments"][0]['destination'],
                                "departure_time": datetime.datetime.strptime(flight_timings[0],
                                                                             "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                                "arrival_time": datetime.datetime.strptime(flight_timings[1],
                                                                           "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                                "duration": departure_flight['duration'],
                            },
                            "return_flight_data": {},
                            "fare_types": [
                                value_fare_data
                            ]

                        }
                        results_count += 1
                        flights_data.append(data)

                else:
                    message = "Departure flights is not available"

            else:
                message = "5 days trips data is missing"

        else:
            message = "Departure trips data is missing"

        if len(flights_data):
            flights_data = sorted(flights_data, key=lambda d: d['fare_types'][0]['fare_value'])

        if self.is_paginated:
            pagination_info = self.one_way_trip_pagination_info(total_departure_flight)

            flights_data_response["total_pages"] = int(pagination_info['total_pages'])
            flights_data_response["page"] = self.page
            flights_data_response["page_size"] = self.page_size
            flights_data_response["next_page"] = pagination_info['next_page']
            flights_data_response["prev_page"] = pagination_info['prev_page']

        flights_data_response["results"] = flights_data

        return flights_data_response, message

    def one_way_trip_pagination_info(self, total_flights_result):
        page = self.page
        page_size = self.page_size

        total_pages = total_flights_result / self.page_size

        if total_pages > int(total_pages):
            total_pages = int(total_pages) + 1

        total_pages = int(total_pages)

        next_page = prev_page = None

        if total_pages > page:
            next_page = page + 1

        if page > 1:
            prev_page = page - 1

        first_result = page_size * (page - 1)
        last_result = page_size * page

        if last_result > total_flights_result:
            last_result = total_flights_result

        pagination_info = {
            'total_pages': total_pages,
            'next_page': next_page,
            'prev_page': prev_page,
            'first_result': first_result,
            'last_result': last_result
        }

        return pagination_info

    def return_trip_flights(self, search_url):
        flights_data = []
        flights_data_response = {}
        total_combination = 0
        message = "Request successful"

        constant_fields_data = get_fare_values_v4()

        currency, departure_flight_data, arrival_flight_data, error = search_api_response(search_url)

        if departure_flight_data and arrival_flight_data:
            dept_five_dates_data = departure_flight_data['dates']
            arvl_five_dates_data = arrival_flight_data['dates']

            if len(dept_five_dates_data) == 5 and len(arvl_five_dates_data) == 5:
                dept_searched_date_data = dept_five_dates_data[2]
                arvl_searched_date_data = arvl_five_dates_data[2]

                departure_flights = dept_searched_date_data['flights']
                arrival_flights = arvl_searched_date_data['flights']

                if not departure_flights:
                    message = "Departure flights are not available"
                    return flights_data_response, message

                if not arrival_flights:
                    message = "Arrival flights are not available"
                    return flights_data_response, message

                departure_flights = [departure_flight for departure_flight in departure_flights if
                                     departure_flight.get('regularFare', None)]

                arrival_flights = [arrival_flight for arrival_flight in arrival_flights if
                                   arrival_flight.get('regularFare', None)]

                total_departure_flight = len(departure_flights)
                total_arrival_flight = len(arrival_flights)
                total_combination = total_departure_flight * total_arrival_flight

                results_count = 0

                for departure_flight in departure_flights:
                    departureFlightKey = departure_flight['flightKey']
                    departureRegularFare = departure_flight.get('regularFare', None)

                    if not departureRegularFare:
                        total_combination -= total_arrival_flight
                        continue

                    dept_flight_number = departure_flight['flightNumber']
                    dept_flight_timings = departure_flight['segments'][0]['time']

                    for arrival_flight in arrival_flights:

                        if departure_flight["segments"][0]['origin'] != arrival_flight["segments"][0]['destination'] or \
                                departure_flight["segments"][0]['destination'] != arrival_flight["segments"][0]['origin']:
                            total_combination -= 1
                            continue

                        if self.is_paginated:
                            if results_count >= self.page * self.page_size:
                                break

                            elif results_count < (self.page - 1) * self.page_size:
                                results_count += 1
                                continue

                        arrivalFlightKey = arrival_flight['flightKey']
                        arrivalRegularFare = arrival_flight.get('regularFare', None)

                        if not arrivalRegularFare:
                            total_combination -= 1
                            continue

                        arvl_flight_number = arrival_flight['flightNumber']
                        arvl_flight_timings = arrival_flight['segments'][0]['time']

                        value_fare_data = self.test_value_fare_data(
                            constant_fields_data=constant_fields_data,
                            currency=currency,
                            departure_fares_data=departure_flight['regularFare']['fares'],
                            return_fares_data=arrival_flight['regularFare']['fares']
                        )

                        data = {
                            "result_id": "RT-FL1-{}-FL2-{}".format(dept_flight_number.split(" ")[1],
                                                                   arvl_flight_number.split(" ")[1]),
                            "departure_flight_data": {
                                "flight_number": departure_flight['flightNumber'],
                                "flight_type": "Direct",
                                "origin_airport_name": departure_flight["segments"][0]['origin'],
                                "destination_airport_name": departure_flight["segments"][0]['destination'],
                                "departure_time": datetime.datetime.strptime(dept_flight_timings[0],
                                                                             "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                                "arrival_time": datetime.datetime.strptime(dept_flight_timings[1],
                                                                           "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                                "duration": departure_flight['duration'],
                            },
                            "return_flight_data": {
                                "flight_number": arrival_flight['flightNumber'],
                                "flight_type": "Direct",
                                "origin_airport_name": arrival_flight["segments"][0]['origin'],
                                "destination_airport_name": arrival_flight["segments"][0]['destination'],
                                "departure_time": datetime.datetime.strptime(arvl_flight_timings[0],
                                                                             "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                                "arrival_time": datetime.datetime.strptime(arvl_flight_timings[1],
                                                                           "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                                "duration": arrival_flight['duration'],
                            },
                            "fare_types": [
                                value_fare_data
                            ]

                        }

                        copy_data = copy.deepcopy(data)
                        flights_data.append(copy_data)

                        results_count += 1

            else:
                message = "5 days trips data is missing"

        else:
            message = "Departure trips data is missing"

        if len(flights_data):
            flights_data = sorted(flights_data, key=lambda d: d['fare_types'][0]['fare_value'])

        if self.is_paginated:
            pagination_info = self.return_trip_pagination_info(total_combination)
            flights_data_response["total_pages"] = int(pagination_info['total_pages'])
            flights_data_response["page"] = self.page
            flights_data_response["page_size"] = self.page_size
            flights_data_response["next_page"] = pagination_info['next_page']
            flights_data_response["prev_page"] = pagination_info['prev_page']

        flights_data_response["results"] = flights_data

        return flights_data_response, message

    def return_trip_pagination_info(self, total_combination):
        page = self.page
        page_size = self.page_size

        total_pages = total_combination / page_size

        if total_pages > int(total_pages):
            total_pages = int(total_pages) + 1

        next_page = prev_page = None
        if total_pages > page:
            next_page = page + 1

        if page > 1:
            prev_page = page - 1

        pagination_info = {
            'total_pages': total_pages,
            'next_page': next_page,
            'prev_page': prev_page
        }

        return pagination_info

    def fare_breakdown_data(self, currency, total_fare_value, flight_fares_data):
        data = {}
        final_data = {}
        for flight_fare_data in flight_fares_data:

            if flight_fare_data["type"] == "ADT":

                seat_count = flight_fare_data['count']
                amount = flight_fare_data['amount']
                total_fare_value += seat_count * amount

                data["adult_seats_info"] = {
                    "seat_count": seat_count,
                    "items_included": [],
                    "items_description": [],
                    "fare_info": {
                        "currency": currency,
                        "value": amount
                    },
                    "others": {},
                    "discounts": []
                }

                if flight_fare_data.get("mandatorySeatFee", {}):
                    qty = flight_fare_data['mandatorySeatFee']['qty']
                    amt = flight_fare_data['mandatorySeatFee']['amt']
                    total_fare_value += qty * amt

                    mandatory_seat_info = {
                        "count": flight_fare_data['mandatorySeatFee']['qty'],
                        "fare_info": {
                            "currency": currency,
                            "value": flight_fare_data['mandatorySeatFee']['amt']
                        },
                    }
                    data["adult_seats_info"]["others"].update({
                        "mandatory_seat_info": mandatory_seat_info
                    })

            elif flight_fare_data["type"] == "CHD":

                seat_count = flight_fare_data['count']
                amount = flight_fare_data['amount']
                total_fare_value += seat_count * amount

                data["children_seats_info"] = {
                    "seat_count": seat_count,
                    "items_included": [],
                    "items_description": [],
                    "fare_info": {
                        "currency": currency,
                        "value": amount
                    },
                    "others": [],
                    "discounts": []
                }

        if self.infants:
            seat_count = self.infants
            amount = 25.00
            total_fare_value += seat_count * amount

            data["infants_seats_info"] = {
                "seat_count": self.infants,
                "items_included": [],
                "items_description": [],
                "fare_info": {
                    "currency": "EUR",
                    "value": 25.00
                },
                "others": [],
                "discounts": []
            }
        final_data['seats_info'] = data
        return total_fare_value, final_data

    def get_seats_data_v5(self, currency, departure_fares_data, return_fares_data):

        total_fare_value = 0
        data = {
            "departure_flight_info": {},
            "return_flight_info": {},
        }

        if departure_fares_data:
            total_fare_value, data["departure_flight_info"] = self.fare_breakdown_data(currency, total_fare_value, departure_fares_data)

        if return_fares_data:
            total_fare_value, data["return_flight_info"] = self.fare_breakdown_data(currency, total_fare_value, return_fares_data)

        copy_data = copy.deepcopy(data)

        total_fare_value = round(total_fare_value, 2)

        return total_fare_value, copy_data

    def test_value_fare_data(self, constant_fields_data, currency, departure_fares_data, return_fares_data=None):
        total_fare_value, fare_breakdown_data = self.get_seats_data_v5(currency, departure_fares_data, return_fares_data)

        data = {
            "fare_type": constant_fields_data['fare_type'],
            "fare_desc": constant_fields_data['fare_desc'],
            "ancillaries": [
                {
                    "ancillary_name": constant_fields_data['ancillaries']['ancillary_name'],
                    "ancillary_desc": constant_fields_data['ancillaries']['ancillary_desc']
                }
            ],
            "fare_currency": currency,
            "fare_value": total_fare_value,
            "fare_breakdown": fare_breakdown_data,
        }

        copy_data = copy.deepcopy(data)

        return copy_data
