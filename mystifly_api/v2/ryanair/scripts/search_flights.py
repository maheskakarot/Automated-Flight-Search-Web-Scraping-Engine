import copy
import time
import logging
from custom_logger.logging import LogMessage
from v1.ryanair.constants.class_names import CLASS_NAMES
from v1.ryanair.constants.xpaths import XPATHS
from v1.ryanair.scripts.fares import ScrapeFareInfo
from v1.ryanair.constants.css_selectors import CSS_SELECTORS
from v1.ryanair.models import Airport
from .common import CommonActions

logger = logging.getLogger(__name__)


class SearchFlightAutomation:

    def __init__(self, driver, request_data):

        self.driver = driver
        self.adults = request_data.get('adults', 1)
        self.children = request_data.get('children', 0)
        self.infants = request_data.get('infants', 0)
        self.nearby_origin_airport = request_data.get('nearby_origin_airport', False)
        self.nearby_destination_airport = request_data.get('nearby_destination_airport', False)
        self.departure_flights_list_constant = 1
        self.return_flights_list_constant = 2
        self.common_actions = CommonActions(self.driver)

    def one_way_trip_flights(self, page, page_size, is_paginated):
        flights_data = []
        message = "Request successful"

        total_flights_result = self.scrape_number_of_available_flights(self.departure_flights_list_constant)

        first_result = 0
        last_result = total_flights_result
        pagination_info = {
            "total_pages": 1,
            "next_page": None,
            "prev_page": None,
        }

        if is_paginated:
            pagination_info = self.one_way_trip_pagination_info(page, page_size)
            first_result = pagination_info['first_result']
            last_result = pagination_info['last_result']

        result_number = 1

        scrape_fare_info = ScrapeFareInfo(self.driver, self.adults, self.children, self.infants, is_return=False)
        for item in range(first_result, last_result):
            flight_card_data, result_number = self.scrape_flight_card_info(result_number,
                                                                           self.departure_flights_list_constant,
                                                                           self.common_actions)

            if len(flight_card_data):
                results = self.driver.find_elements_by_class_name(CLASS_NAMES['FLIGHT_SELECT_BUTTON'])
                results[item].click()

                fare_types = scrape_fare_info.all_fares_data()
                flight_fare_types_data = copy.deepcopy(fare_types)

                self.common_actions.edit_flight_button()

                if not flight_fare_types_data[0]["data_mismatch"]:
                    flight_data = {
                        "result_id": "OW-FL1-{}".format(flight_card_data['flight_number'].split(" ")[1]),
                        "departure_flight_data": {
                            "flight_number": flight_card_data['flight_number'],
                            "flight_type": flight_card_data['flight_type'],
                            "origin_airport_name": flight_card_data['origin_airport_name'],
                            "destination_airport_name": flight_card_data['destination_airport_name'],
                            "departure_time": flight_card_data['departure_time'],
                            "arrival_time": flight_card_data['arrival_time'],
                            "duration": flight_card_data['duration'],
                        },
                        "arrival_flight_data": {},
                        "fare_types": flight_fare_types_data,
                    }
                    flights_data.append(flight_data)

        if not len(flights_data):
            logger.error(LogMessage("No flights available", self.driver).save_log)
            message = "No flights available"

        flights_data = {
            "total_pages": pagination_info['total_pages'],
            "count": total_flights_result,
            "page_size": page_size,
            "next_page": pagination_info['next_page'],
            "prev_page": pagination_info['prev_page'],
            "results": flights_data
        }

        return flights_data, message

    def one_way_trip_pagination_info(self, page, page_size):
        total_flights_result = self.scrape_number_of_available_flights(self.departure_flights_list_constant)

        total_pages = total_flights_result / page_size

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

    def return_trip_flights(self, page, page_size, is_paginated):
        flights_data = []
        message = "Request successful"

        number_of_departure_flights = self.scrape_number_of_available_flights(self.departure_flights_list_constant)

        if number_of_departure_flights == 0:
            message = "No departure flight available"
            return flights_data, message

        number_of_return_flights = self.scrape_number_of_available_flights(self.return_flights_list_constant)

        if number_of_return_flights == 0:
            message = "No arrival flight available"
            return flights_data, message

        if is_paginated:
            total_pages, prev_page, next_page = self.return_trip_pagination_info(number_of_departure_flights,
                                                                                 number_of_return_flights, page_size,
                                                                                 page)

            departure_airports = arrival_airports = None

            if self.nearby_origin_airport or self.nearby_destination_airport:
                departure_airports, arrival_airports, total_pages = self.nearby_airports_data(
                    number_of_departure_flights,
                    number_of_return_flights
                )

                total_pages = total_pages / page_size
                if total_pages > int(total_pages):
                    total_pages = int(total_pages) + 1

            if page > total_pages:
                message = "Request was failed."
                return flights_data, message

            flights_data = self.return_trip_paginated_data(number_of_departure_flights, number_of_return_flights,
                                                           page_size, page, self.common_actions, flights_data,
                                                           departure_airports, arrival_airports)

            flights_data = {
                "total_pages": int(total_pages),
                "count": number_of_departure_flights * number_of_return_flights,
                "page_size": page_size,
                "next_page": next_page,
                "prev_page": prev_page,
                "results": flights_data
            }

        else:
            flights_data = self.return_trip_data_without_pagination(number_of_departure_flights,
                                                                    number_of_return_flights,
                                                                    flights_data, self.common_actions)

        return flights_data, message

    def scrape_flight_card_info(self, result_number, flights_list_constant, common_actions_obj=None):
        element = self.driver.find_element_by_xpath(
            XPATHS['FLIGHT_INFO'].format(flights_list_constant, result_number))

        if common_actions_obj:
            common_actions_obj.scroll_to_element(element)

        flight_main_info = element.text.splitlines()

        # Expected list
        # ['Ryanair', '06:30', 'London Stansted', 'Duration 1h 15m', '07:45', 'Dublin', 'Flight no.', 'FR 203', 'Type',
        # 'Direct', 'Value Fare', '£315.79', 'Select']
        while len(flight_main_info) == 11 and result_number < 50:
            result_number += 1
            element = self.driver.find_element_by_xpath(
                XPATHS['FLIGHT_INFO'].format(flights_list_constant, result_number))

            if common_actions_obj:
                common_actions_obj.scroll_to_element(element)
            flight_main_info = element.text.splitlines()

        result_number += 1
        flight_card_data = {}
        if len(flight_main_info) >= 13:
            try:
                origin_airport_code = Airport.objects.filter(name__icontains=flight_main_info[2])[0].code
                destination_airport_code = Airport.objects.filter(name__icontains=flight_main_info[5])[0].code
            except Exception as ex:
                print(ex)
                origin_airport_code = flight_main_info[2]
                destination_airport_code = flight_main_info[5]

            flight_card_data = {
                "flight_number": flight_main_info[7],
                "flight_type": flight_main_info[9],
                "origin_airport_name": origin_airport_code,
                "destination_airport_name": destination_airport_code,
                "departure_time": flight_main_info[1],
                "arrival_time": flight_main_info[4],
                "duration": flight_main_info[3],
            }
        return flight_card_data, result_number

    def scrape_number_of_available_flights(self, flights_list_constant):
        """
        This function will return total number of available flights
        """

        available_flights = self.driver.find_element_by_xpath(
            XPATHS['FLIGHTS_LIST']
            .format(flights_list_constant)) \
            .text.splitlines().count('Select')

        return available_flights

    def return_trip_pagination_info(self, number_of_departure_flights, number_of_return_flights, page_size, page):

        total_combination = number_of_departure_flights * number_of_return_flights

        total_pages = total_combination / page_size

        if total_pages > int(total_pages):
            total_pages = int(total_pages) + 1

        next_page = prev_page = None
        if total_pages > page:
            next_page = page + 1

        if page > 1:
            prev_page = page - 1

        return total_pages, prev_page, next_page

    def return_trip_data_without_pagination(self, number_of_departure_flights, number_of_return_flights,
                                            flights_data, common_actions_obj):
        departure_flight_number = 1

        scrape_fare_info = ScrapeFareInfo(self.driver, self.adults, self.children, self.infants, is_return=True)
        for departure_flight in range(1, number_of_departure_flights + 1):

            departure_flight_data, departure_flight_number = self.scrape_flight_card_info(
                departure_flight_number,
                self.departure_flights_list_constant, common_actions_obj)

            return_flight_number = 1

            for return_flight in range(1, number_of_return_flights + 1):
                return_flight_data, return_flight_number = self.scrape_flight_card_info(
                    return_flight_number,
                    self.return_flights_list_constant, common_actions_obj)

                departure_flight_select_button = self.driver.find_element_by_xpath(
                    XPATHS['SELECT_BUTTON'].format(self.departure_flights_list_constant, departure_flight_number - 1))

                return_flight_select_button = self.driver.find_element_by_xpath(
                    XPATHS['SELECT_BUTTON'].format(self.return_flights_list_constant, return_flight_number - 1))

                departure_flight_select_button.click()
                time.sleep(0.1)
                return_flight_select_button.click()

                fare_types = scrape_fare_info.all_fares_data()
                flight_fare_types_data = copy.deepcopy(fare_types)

                self.common_actions.edit_flight_button()

                combination_data = {
                    'result_id': "RT-FL1-{}-FL2-{}".format(departure_flight_data['flight_number'].split(" ")[1],
                                                           return_flight_data['flight_number'].split(" ")[1]),
                    'departure_flight_data': departure_flight_data,
                    'return_flight_data': return_flight_data,
                    "fare_types": flight_fare_types_data,
                }

                flights_data.append(combination_data)

        return flights_data

    def return_trip_paginated_data(self, number_of_departure_flights, number_of_return_flights, page_size, page,
                                   common_actions_obj, flights_data, departure_airports, arrival_airports):

        first_combination = page_size * (page - 1) + 1
        last_combination = page_size * page

        departure_flight_number = 1
        combination_number = 1

        scrape_fare_info = ScrapeFareInfo(self.driver, self.adults, self.children, self.infants, is_return=True)

        for departure_flight in range(1, number_of_departure_flights + 1):
            departure_flight_data, departure_flight_number = self.scrape_flight_card_info(
                departure_flight_number,
                self.departure_flights_list_constant)

            return_flight_number = 1
            if arrival_airports:
                number_of_return_flights = arrival_airports[departure_flight_data['origin_airport_name']]

            for return_flight in range(1, number_of_return_flights + 1):

                if combination_number > last_combination:
                    return flights_data

                if first_combination <= combination_number <= last_combination:

                    departure_flight_select_button = self.driver.find_element_by_xpath(
                        XPATHS['SELECT_BUTTON'].format(self.departure_flights_list_constant,
                                                       departure_flight_number - 1))

                    departure_flight_select_button.click()
                    time.sleep(0.1)

                    return_flight_data, return_flight_number = self.scrape_flight_card_info(
                        return_flight_number,
                        self.return_flights_list_constant)

                    return_flight_select_button = self.driver.find_element_by_xpath(
                        XPATHS['SELECT_BUTTON'].format(self.return_flights_list_constant, return_flight_number - 1))

                    self.common_actions.scroll_to_element(return_flight_select_button)
                    return_flight_select_button.click()

                    fare_types = scrape_fare_info.all_fares_data()
                    flight_fare_types_data = copy.deepcopy(fare_types)
                    self.common_actions.edit_flight_button()

                    if not flight_fare_types_data[0]["data_mismatch"]:
                        combination_data = {
                            'result_id': "RT-FL1-{}-FL2-{}".format(departure_flight_data['flight_number'].split(" ")[1],
                                                                   return_flight_data['flight_number'].split(" ")[1]),
                            'departure_flight_data': departure_flight_data,
                            'return_flight_data': return_flight_data,
                            "fare_types": flight_fare_types_data,
                        }

                        flights_data.append(combination_data)

                else:
                    return_flight_number += 1

                combination_number += 1

        return flights_data

    def nearby_airports_data(self, number_of_departure_flights, number_of_return_flights):
        departure_airports = {}
        arrival_airports = {}

        departure_flight_number = 1
        for departure_flight in range(1, number_of_departure_flights + 1):
            departure_flight_data, departure_flight_number = self.scrape_flight_card_info(
                departure_flight_number,
                self.departure_flights_list_constant)

            if departure_airports.get(departure_flight_data['origin_airport_name'], 0):
                departure_airports[departure_flight_data['origin_airport_name']] += 1

            else:
                departure_airports[departure_flight_data['origin_airport_name']] = 1

        return_flight_number = 1
        for return_flight in range(1, number_of_return_flights + 1):
            return_flight_data, return_flight_number = self.scrape_flight_card_info(
                return_flight_number,
                self.return_flights_list_constant)

            if arrival_airports.get(return_flight_data['destination_airport_name'], 0):
                arrival_airports[return_flight_data['destination_airport_name']] += 1

            else:
                arrival_airports[return_flight_data['destination_airport_name']] = 1

        total_pages = 0

        for airport_name, departure_flight_count in departure_airports.items():
            total_pages += arrival_airports[airport_name] * departure_flight_count

        return departure_airports, arrival_airports, total_pages

    def sort_flights(self, sort_by):
        self.driver.implicitly_wait(2)
        try:
            sort_btns = self.driver.find_elements_by_class_name(CLASS_NAMES['SORT_BTN'])
            for sort_btn in sort_btns:
                sort_btn.click()
                time.sleep(0.5)

                sorting_items = self.driver.find_elements_by_css_selector(CSS_SELECTORS['SORT_ITEM'])

                for sorting_item in sorting_items:
                    if str(sorting_item.text).lower() == sort_by.lower():
                        sorting_item.click()
                        break

        except Exception as ex:
            print(ex)

        self.driver.implicitly_wait(10)
