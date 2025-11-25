import copy
import datetime
import logging
from v3.ryanair.helpers.search import search_api_response, get_fare_values
from v3.ryanair.helpers.basket import create_booking, create_basket

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

        constant_fields_data = get_fare_values()

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
                    basket_id = create_basket()

                    if not basket_id:
                        message = "Unable to create basket"
                        return flights_data_response, message

                    # Results count
                    results_count = 0

                    departure_flights = [departure_flight for departure_flight in departure_flights if
                                         departure_flight.get('regularFare', None)]
                    total_departure_flight = len(departure_flights)
                    for departure_flight in departure_flights:

                        if self.is_paginated:
                            if results_count >= self.page * self.page_size:
                                break

                            elif results_count < (self.page - 1) * self.page_size:
                                results_count += 1
                                continue

                        flightKey = departure_flight['flightKey']

                        departureRegularFare = departure_flight.get('regularFare')
                        departureFareKey = departureRegularFare['fareKey']

                        flight_number = departure_flight['flightNumber']
                        flight_timings = departure_flight['segments'][0]['time']

                        value_fare_data = self.test_value_fare_data(
                            basketId=basket_id, constant_fields_data=constant_fields_data,
                            is_return=False, departureFareKey=departureFareKey, departureFlightKey=flightKey)

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

        # if len(flights_data):
        #     flights_data = sorted(flights_data, key=lambda d: d['fare_types'][0]['fare_value'])

        if self.is_paginated:
            pagination_info = self.one_way_trip_pagination_info(total_departure_flight)

            flights_data_response["total_pages"] = pagination_info['total_pages']
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

        constant_fields_data = get_fare_values()

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

                basket_id = create_basket()

                if not basket_id:
                    message = "Unable to create basket"
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

                    departureFareKey = departureRegularFare['fareKey']
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

                        arrivalFareKey = arrivalRegularFare['fareKey']

                        arvl_flight_number = arrival_flight['flightNumber']
                        arvl_flight_timings = arrival_flight['segments'][0]['time']

                        value_fare_data = self.test_value_fare_data(
                            basketId=basket_id, constant_fields_data=constant_fields_data,
                            is_return=True, departureFareKey=departureFareKey, departureFlightKey=departureFlightKey,
                            arrivalFareKey=arrivalFareKey, arrivalFlightKey=arrivalFlightKey)

                        value_fare_data = copy.deepcopy(value_fare_data)

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

        # if len(flights_data):
        #     flights_data = sorted(flights_data, key=lambda d: d['fare_types'][0]['fare_value'])

        if self.is_paginated:
            pagination_info = self.return_trip_pagination_info(total_combination)
            flights_data_response["total_pages"] = pagination_info['total_pages']
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

    @staticmethod
    def get_seats_data(currency, fares_data):

        data = {}

        for fare_data in fares_data:

            fare_type = fare_data['type']

            mandatory_seat_data = fare_data.get("mandatorySeatFee", {})

            if mandatory_seat_data:
                mandatory_seat_data = {
                    "name": "mandatorySeatFee",
                    "count": fare_data['mandatorySeatFee']['qty'],
                    "fare_info": {
                        "currency": currency,
                        "value": fare_data['mandatorySeatFee']['amt']
                    },
                }

            if fare_type == "ADT":
                data["adult_seats_info"] = {
                    "seat_count": fare_data['count'],
                    "items_included": [],
                    "items_description": [],
                    "fare_info": {
                        "currency": currency,
                        "value": fare_data['amount']
                    },
                    "others": [
                        mandatory_seat_data
                    ],
                    "discounts": []
                }

            elif fare_type == "CHD":
                data["children_seats_info"] = {
                    "seat_count": fare_data['count'],
                    "items_included": [],
                    "items_description": [],
                    "fare_info": {
                        "currency": currency,
                        "value": fare_data['amount']
                    },
                    "others": [],
                    "discounts": fare_data['discountAmount']
                }

        return data

    @staticmethod
    def get_seats_data_v2(booking_data, is_return=False):

        data = {
            "departure_flight_info": {},
            "return_flight_info": {},
        }
        try:
            currency = booking_data["currency"]
            fares_data = booking_data["gettingThere"]["components"]
            discounts = booking_data["gettingThere"]["discounts"]

            dept_discounts_data_list = []
            arvl_discounts_data_list = []
            for discount in discounts:

                discount_data = {
                    "code": discount["code"],
                    "quantity": discount["qty"],
                    "amount": round(discount["amount"], 2),
                }

                dis_journey_num = discount['journeyNum']
                if is_return and dis_journey_num == 1:
                    arvl_discounts_data_list.append(discount_data)

                else:
                    dept_discounts_data_list.append(discount_data)

            data["departure_flight_info"]["discounts"] = dept_discounts_data_list
            data["return_flight_info"]["discounts"] = arvl_discounts_data_list

            for fare_data in fares_data:

                flight_journey_num = fare_data['variant']['journeyNumber']

                fare_type = fare_data['code']

                if fare_type == "ADT":
                    adt = {
                        "seat_count": fare_data['quantity'],
                        "items_included": [],
                        "items_description": [],
                        "fare_info": {
                            "currency": currency,
                            "value": fare_data['price']['total']
                        },
                        "others": [],
                        "discounts": []
                    }
                    if is_return and flight_journey_num == 1:
                        data["return_flight_info"]["adult_seats_info"] = adt
                    else:
                        data["departure_flight_info"]["adult_seats_info"] = adt

                elif fare_type == "CHD":
                    chd = {
                        "seat_count": fare_data['quantity'],
                        "items_included": [],
                        "items_description": [],
                        "fare_info": {
                            "currency": currency,
                            "value": fare_data['price']['total']
                        },
                        "others": [],
                        "discounts": []
                    }
                    if is_return and flight_journey_num == 1:
                        data["return_flight_info"]["children_seats_info"] = chd
                    else:
                        data["departure_flight_info"]["children_seats_info"] = chd

                elif fare_type == "INF":
                    inf = {
                        "seat_count": fare_data['quantity'],
                        "items_included": [],
                        "items_description": [],
                        "fare_info": {
                            "currency": currency,
                            "value": fare_data['price']['total']
                        },
                        "others": [],
                        "discounts": []
                    }
                    if is_return and flight_journey_num == 1:
                        if data["return_flight_info"].get("infant_seats_info", None):
                            data["return_flight_info"]["infant_seats_info"]["seat_count"] = \
                                data["return_flight_info"]["infant_seats_info"]["seat_count"] + 1

                            data["return_flight_info"]["infant_seats_info"]["fare_info"]["value"] = \
                                data["return_flight_info"]["infant_seats_info"]["fare_info"]["value"] + \
                                fare_data['price']['total']

                        else:
                            data["return_flight_info"]["infant_seats_info"] = inf

                    else:
                        if data["departure_flight_info"].get("infant_seats_info", None):
                            data["departure_flight_info"]["infant_seats_info"]["seat_count"] = \
                                data["departure_flight_info"]["infant_seats_info"][
                                    "seat_count"] + 1

                            data["departure_flight_info"]["infant_seats_info"]["fare_info"]["value"] = \
                                data["departure_flight_info"]["infant_seats_info"]["fare_info"]["value"] + \
                                fare_data['price']['total']

                        else:
                            data["departure_flight_info"]["infant_seats_info"] = inf

                elif fare_type == "SETA":
                    seta = {
                        "seat_count": fare_data['quantity'],
                        "items_included": [],
                        "items_description": [],
                        "fare_info": {
                            "currency": currency,
                            "value": fare_data['price']['total']
                        },
                        "others": [],
                        "discounts": []
                    }

                    if is_return and flight_journey_num == 1:
                        if data["return_flight_info"].get("mandatory_seats_info", None):
                            data["return_flight_info"]["mandatory_seats_info"]["seat_count"] = \
                                data["return_flight_info"]["mandatory_seats_info"]["seat_count"] + 1

                            data["return_flight_info"]["mandatory_seats_info"]["fare_info"]["value"] = \
                                data["return_flight_info"]["mandatory_seats_info"]["fare_info"]["value"] + \
                                fare_data['price']['total']

                        else:
                            data["return_flight_info"]["mandatory_seats_info"] = seta

                    else:
                        if data["departure_flight_info"].get("mandatory_seats_info", None):
                            data["departure_flight_info"]["mandatory_seats_info"]["seat_count"] = \
                                data["departure_flight_info"]["mandatory_seats_info"][
                                    "seat_count"] + 1

                            data["departure_flight_info"]["mandatory_seats_info"]["fare_info"]["value"] = \
                                data["departure_flight_info"]["mandatory_seats_info"]["fare_info"]["value"] + \
                                fare_data['price']['total']

                        else:
                            data["departure_flight_info"]["mandatory_seats_info"] = seta

        except Exception as ex:
            pass

        copy_data = copy.deepcopy(data)

        return copy_data

    def test_value_fare_data(self, constant_fields_data, basketId, is_return, departureFareKey,
                             departureFlightKey, arrivalFareKey=None, arrivalFlightKey=None):
        data = {}

        request_data = {
            'basketId': basketId,
            'adults': self.adults,
            'children': self.children,
            'infants': self.infants,
            'departureFareKey': departureFareKey,
            'departureFlightKey': departureFlightKey,
            'arrivalFareKey': arrivalFareKey,
            'arrivalFlightKey': arrivalFlightKey,
        }

        response = create_booking(request_data)

        response = copy.deepcopy(response)

        if not response:
            return data

        create_booking_response = response['data']['createBooking']

        if constant_fields_data:
            data["fare_type"] = constant_fields_data['fare-card']['title-v2']['standard']
            data["fare_desc"] = constant_fields_data['fare-card']['subtitle-standard'],
            data["ancillaries"] = [
                    {
                        "ancillary_name": constant_fields_data['fare-card']['benefit-v2'][
                            'title-small_bag-standard'],
                        "ancillary_desc": constant_fields_data['fare-card']['benefit'][
                            'description-small_bag-standard']
                    }
                ]

        data = {
            "fare_currency": create_booking_response["currency"],
            "fare_value": create_booking_response["gettingThere"]["price"]["total"],
            "fare_breakdown": self.get_seats_data_v2(create_booking_response, is_return),
        }

        copy_data = copy.deepcopy(data)

        return copy_data
