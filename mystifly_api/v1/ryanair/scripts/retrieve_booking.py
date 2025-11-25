import time
from selenium.webdriver.common.by import By
from v1.ryanair.constants.class_names import CLASS_NAMES
from v1.ryanair.constants.urls import MANAGE_BOOKING_URL


class RetrieveBooking:

    def __init__(self, driver):
        self.driver = driver

    def retrieve_upcoming_booking(self, reservation_number=None):
        self.driver.get(MANAGE_BOOKING_URL)
        upcoming_trip_ticket_list = []

        try:
            self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['VIEW_MORE_TRIPS']).click()
        except:
            pass

        if reservation_number:
            try:
                self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['UPCOMING_TRIPS_BTN']).click()
            except:
                pass

            upcoming_cards_desc = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['UPCOMING_CARDS_DESC'])

            target_card_number = None
            i = 0
            for upcoming_card_desc in upcoming_cards_desc:
                card_desc = upcoming_card_desc.text.splitlines()

                if reservation_number in card_desc[2]:
                    target_card_number = i
                    break

                i += 1

            upcoming_trip_ticket = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['MANAGE_UPCOMING_BOOKINGS'])
            upcoming_trip_ticket[target_card_number].click()
            upcoming_trip_ticket_list = self.scrape_trip_detail(upcoming_trip_ticket_list)

            return upcoming_trip_ticket_list

        upcoming_trip_ticket = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['MANAGE_UPCOMING_BOOKINGS'])

        current_working_ticket = 0
        for each_ticket in upcoming_trip_ticket:
            upcoming_trip_ticket = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['MANAGE_UPCOMING_BOOKINGS'])
            upcoming_trip_details = {}
            flight_details = {}
            passengers_list = []
            upcoming_trip_ticket[current_working_ticket].click()
            current_working_ticket += 1

            journey_date = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['JOURNEY_DATE']).text
            upcoming_trip_details['journey_date'] = journey_date

            flight_pnr = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['RESERVATION_NO']).text
            upcoming_trip_details['reservation_no'] = flight_pnr

            flight_time = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['DEPARTURE']).text
            flight_time_list = flight_time.split('\n')
            flight_details['departure_time'] = flight_time_list[0]
            flight_details['departure_destination'] = flight_time_list[1]

            arrival_flight = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['ARRIVAL']).text
            arrival_flight_list = arrival_flight.split('\n')
            flight_details['arrival_time'] = arrival_flight_list[0]
            flight_details['arrival_destination'] = arrival_flight_list[1]

            flight_duration = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['FLIGHT_DURATION']).text
            flight_duration_list = flight_duration.split('\n')
            flight_details['duration'] = flight_duration_list[0]
            flight_details['flight_code'] = flight_duration_list[1]
            flight_details['flight_status'] = None

            upcoming_trip_details['flight_details'] = flight_details

            passenger_name = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['PASSENGER_NAME'])
            baggage_details = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['BAGGAGE_DETAILS'])

            passenger_details = {
                'name': passenger_name.text,
                'baggage': baggage_details.text
            }
            passengers_list.append(passenger_details)

            upcoming_trip_details['passenger_details'] = passengers_list

            upcoming_trip_ticket_list.append(upcoming_trip_details)
            self.driver.back()

        return upcoming_trip_ticket_list

    def retrieve_past_trip(self, reservation_number=None):

        past_trip_list = []

        past_booking_button = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['PAST_BOOKING'])
        current_past_booking = 0
        for past_booking in past_booking_button:
            past_booking_button = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['PAST_BOOKING'])
            ticket_details = {}
            flight_details = {}
            passengers_list = []
            past_booking_button[current_past_booking].click()
            current_past_booking += 1

            journey_date = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['JOURNEY_DATE']).text
            ticket_details['journey_date'] = journey_date

            reservation_no = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['RESERVATION_NO']).text
            ticket_details['reservation_no'] = reservation_no

            flight_detail = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['FLIGHT_DETAILS']).text
            flight_details_list = flight_detail.split('\n')
            destination = flight_details_list[0]
            timing = flight_details_list[2]
            flight_details['departure_time'] = timing[:timing.index('-') - 1]
            flight_details['departure_destination'] = destination[:destination.index('to') - 1]
            flight_details['arrival_time'] = timing[timing.index('-') + 2:]
            flight_details['arrival_destination'] = destination[destination.index('to') + 3:]
            flight_details['flight_code'] = flight_details_list[3]

            flight_details['flight_status'] = flight_details_list[4]
            ticket_details['flight_details'] = flight_details

            passenger_name = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['PASSENGER_NAME'])
            baggage_details = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['BAGGAGE_DETAILS'])

            passenger_details = {
                'name': passenger_name.text,
                'baggage': baggage_details.text
            }
            passengers_list.append(passenger_details)
            ticket_details['passenger_details'] = passengers_list
            past_trip_list.append(ticket_details)
            self.driver.get(MANAGE_BOOKING_URL)

        return past_trip_list

    def scrape_trip_detail(self, upcoming_trip_ticket_list):
        upcoming_trip_details = {}
        flight_details = {}
        passengers_list = []

        journey_date = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['JOURNEY_DATE']).text
        upcoming_trip_details['journey_date'] = journey_date

        flight_pnr = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['RESERVATION_NO']).text
        upcoming_trip_details['reservation_no'] = flight_pnr

        flight_time = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['DEPARTURE']).text
        flight_time_list = flight_time.split('\n')
        flight_details['departure_time'] = flight_time_list[0]
        flight_details['departure_destination'] = flight_time_list[1]

        arrival_flight = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['ARRIVAL']).text
        arrival_flight_list = arrival_flight.split('\n')
        flight_details['arrival_time'] = arrival_flight_list[0]
        flight_details['arrival_destination'] = arrival_flight_list[1]

        flight_duration = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['FLIGHT_DURATION']).text
        flight_duration_list = flight_duration.split('\n')
        flight_details['duration'] = flight_duration_list[0]
        flight_details['flight_code'] = flight_duration_list[1]
        flight_details['flight_status'] = None

        upcoming_trip_details['flight_details'] = flight_details

        passenger_name = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['PASSENGER_NAME'])
        baggage_details = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['BAGGAGE_DETAILS'])

        passenger_details = {
            'name': passenger_name.text,
            'baggage': baggage_details.text
        }
        passengers_list.append(passenger_details)

        upcoming_trip_details['passenger_details'] = passengers_list

        upcoming_trip_ticket_list.append(upcoming_trip_details)

        return upcoming_trip_ticket_list
