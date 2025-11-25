import time

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

from v1.ryanair.constants.class_names import CLASS_NAMES
from v1.ryanair.constants.data_ref import DATA_REF
from v1.ryanair.constants.ids import IDS
from v1.ryanair.constants.urls import MANAGE_BOOKING_URL
from v1.ryanair.constants.xpaths import XPATHS


class Reissuance:

    def __init__(self, driver):
        self.driver = driver

    def flight_search(self, source, destination, journey_date, reservation_no):
        self.driver.get(MANAGE_BOOKING_URL)

        self.driver.implicitly_wait(5)

        self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['LOAD_MORE_BUTTON']).click()

        manage_buttons = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['MANAGE_UPCOMING_BOOKINGS'])

        for each in manage_buttons:
            data_ref = each.get_attribute('data-ref')
            if data_ref == DATA_REF['MANAGE_BOOKING'].format(reservation_no):
                each.click()
                try:
                    self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['INCOMPLETE_PAYMENT_BUTTON_POPUP'])
                    return -1
                except NoSuchElementException as e:
                    pass
                break

        options = self.driver.find_elements(By.CLASS_NAME, 'expansion-panel__title')
        for option in options:

            if option.text.lower() == 'change your flights':
                option.click()

                text = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['PANEL_CONTENT']).text

                self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['EXPANSION_PANEL_BUTTON']).click()
                break

        self.driver.implicitly_wait(10)
        active_element = self.driver.switch_to.active_element
        self.driver.implicitly_wait(2)

        input_fields = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['CORE_INPUT'])
        input_fields[0].clear()
        input_fields[1].clear()
        input_fields[0].send_keys(source)

        input_fields[1].send_keys(destination)

        self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['TICKET_DIV']).click()

        date_field = self.driver.find_element(By.CLASS_NAME, 'dd')
        date_field.clear()
        date_list = journey_date.split('/')
        date_field.send_keys(date_list[0])
        self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['TICKET_DIV']).click()

        month_field = self.driver.find_element(By.CLASS_NAME, 'mm')
        month_field.clear()
        month_field.send_keys(date_list[1])

        self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['TICKET_DIV']).click()
        year_field = self.driver.find_element(By.CLASS_NAME, 'yyyy')
        year_field.clear()
        year_field.send_keys(date_list[2])

        self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['TICKET_DIV']).click()

        active_element.find_element(By.CLASS_NAME, CLASS_NAMES['FOOTER']).click()

        self.driver.implicitly_wait(2)

        flight_row = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['FLIGHT_ROW'])
        flights = flight_row.find_elements(By.CLASS_NAME, CLASS_NAMES['FLIGHT_HEADER'])
        flight_list = []
        for flight in flights:
            try:
                flight.find_element(By.CLASS_NAME, CLASS_NAMES['SOLD_OUT_FLIGHT'])
                continue
            except NoSuchElementException:
                pass

            duration_div = flight.find_element(By.CLASS_NAME, CLASS_NAMES['DURATION'])
            duration_text_list = duration_div.text.split('\n')
            flight_mode = duration_text_list[0]
            duration = duration_text_list[1][1:-1]

            flight_time_div = flight.find_element(By.CLASS_NAME, CLASS_NAMES['TIME'])
            flight_time_list = flight_time_div.text.split('\n')
            departure_time = flight_time_list[0]
            arrival_time = flight_time_list[1]

            cities_div = flight.find_element(By.CLASS_NAME, CLASS_NAMES['CITY']).text
            cities = cities_div.split('\n')
            departure_city = cities[0]
            arrival_city = cities[1]

            flight_number = flight.find_element(By.CLASS_NAME, CLASS_NAMES['FLIGHT_NUMBER_DIV'])
            flight_no = flight_number.text

            flight_list.append(
                {
                    'duration': duration,
                    'arrival_time': arrival_time,
                    'arrival_city': arrival_city,
                    'departure_time': departure_time,
                    'departure_city': departure_city,
                    'flight_mode': flight_mode,
                    'flight_number': flight_no
                }
            )
        return flight_list

    def select_flight_find_fare_difference(self, flight_no):

        flights = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['FLIGHT_HEADER'])
        details = {}
        price_class_name = {
            'new_price': CLASS_NAMES['CHANGE_FLIGHT_NEW_PRICE'],
            'original_price': CLASS_NAMES['CHANGE_FLIGHT_ORIGINAL_PRICE'],
            'change_fee': CLASS_NAMES['CHANGE_FEE'],
            'price_difference': CLASS_NAMES['CHANGE_FLIGHT_DIFFERENCE']
        }
        for flight in flights:

            flight_number = flight.find_element(By.CLASS_NAME, CLASS_NAMES['FLIGHT_NUMBER_DIV'])

            if flight_number.text.lower() == flight_no.lower():
                flight.find_element(By.CLASS_NAME, CLASS_NAMES['FLIGHT_SELECTION_BUTTON']).click()
                time.sleep(3)
                footer = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['FOOTER']).click()

                self.driver.implicitly_wait(3)

                cart_details = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['CHANGE_FLIGHT_CART'])

                price_info = self.get_price_difference(price_class_name,
                                                       cart_details)

                cart_total = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['CHANGE_FLIGHT_CART_TOTAL'])
                total_price_text = cart_total.find_element(By.CLASS_NAME, CLASS_NAMES['CHANGE_FLIGHT_CART_PRICE']).text
                total_price_list = total_price_text.split(' ')

                price_info['total_price'] = {
                    'currency': total_price_list[0],
                    'price': total_price_list[1]
                }

                old_flight_details_div = self.driver.find_element(By.CLASS_NAME,
                                                                  CLASS_NAMES['OLD_FLIGHT_TICKET_DETAILS'])
                old_flight_details_text = old_flight_details_div.find_element(By.CLASS_NAME,
                                                                              CLASS_NAMES[
                                                                                  'OLD_FLIGHT_DESTINATION']).text
                old_flight_details_list = old_flight_details_text.split('-')

                old_flight_time_text = old_flight_details_div.find_element(By.CLASS_NAME, CLASS_NAMES['TIME']).text
                old_flight_time_list = old_flight_time_text.split('-')

                old_flight_date_text = old_flight_details_div.find_element(By.CLASS_NAME, CLASS_NAMES['DATE']).text
                old_flight_number_text = old_flight_details_div.find_element(By.CLASS_NAME,
                                                                             CLASS_NAMES['FLIGHT_NUMBER_DIV']).text

                new_flight_details_div = self.driver.find_element(By.CLASS_NAME,
                                                                  CLASS_NAMES['CHANGE_FLIGHT_NEW_TICKET_DETAILS'])
                new_flight_details_text = new_flight_details_div.find_element(By.TAG_NAME,
                                                                              CLASS_NAMES['CHANGE_FLIGHT_LABEL']).text
                new_flight_details_list = new_flight_details_text.split('-')

                new_flight_time_text = new_flight_details_div.find_element(By.CLASS_NAME, CLASS_NAMES['TIME']).text
                new_flight_time_list = new_flight_time_text.split('-')

                new_flight_date_text = new_flight_details_div.find_element(By.CLASS_NAME, 'date').text
                new_flight_number_text = new_flight_details_div.find_element(By.CLASS_NAME,
                                                                             CLASS_NAMES['FLIGHT_NUMBER_DIV']).text

                details = {
                    'old_flight_details': {
                        'departure_city': old_flight_details_list[0],
                        'departure_time': old_flight_time_list[0],
                        'arrival_city': old_flight_details_list[1],
                        'arrival_time': old_flight_time_list[1],
                        'date': old_flight_date_text,
                        'flight_number': old_flight_number_text
                    },
                    'new_flight_details': {
                        'departure_city': new_flight_details_list[0],
                        'departure_time': new_flight_time_list[0],
                        'arrival_city': new_flight_details_list[1],
                        'arrival_time': new_flight_time_list[1],
                        'date': new_flight_date_text,
                        'flight_number': new_flight_number_text
                    },
                    'price_info': price_info

                }

                return details

    def initiate_payment(self, card_detail, address_1, address_2, pincode, city, state, country):
        try:
            self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['FOOTER']).click()
        except NoSuchElementException as e:
            pass

        self.add_address_details(address_1, address_2, pincode, city, state, country)
        self.add_card_info(card_detail)
        time.sleep(3)

        terms_div = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['TERMS'])
        terms_div.find_element(By.CLASS_NAME, CLASS_NAMES['CHECKBOX']).click()

        cta_div = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['CTA_DIV'])

        cta_div.find_element(By.CLASS_NAME, CLASS_NAMES['CHECKOUT_BUTTON']).click()

        error_div = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['ERROR_DIV'])
        failed_payment_dialog = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['FAILED_PAYMENT_DIALOG'])
        if len(error_div) or len(failed_payment_dialog):
            return -1
        return 0

    def add_card_info(self, card_detail):

        expiry_month_div = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['EXPIRY_MONTH'])
        expiry_month_div.send_keys(card_detail['ExpiryMonth'])

        expiry_year_div = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['EXPIRY_YEAR'])
        expiry_year_div.send_keys(card_detail['ExpiryYear'])

        cvv_div = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['CVV'])
        cvv_input_field = cvv_div.find_element(By.CLASS_NAME, CLASS_NAMES['INPUT_FIELD'])
        cvv_input_field.send_keys(card_detail['CVV'])

        cardholder_div = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['CARDHOLDER'])
        cardholder_div.send_keys(card_detail['HolderName'])

        # Switch to credit card iframe
        self.driver.switch_to.frame(self.driver.find_element_by_class_name('card-iframe'))

        card_no_input_area = self.driver.find_element(By.CLASS_NAME, 'b2')
        card_no_input_area.send_keys(card_detail['CardNumber'])

        # Switch to default content
        self.driver.switch_to.default_content()

    def add_address_details(self, address_1, address_2, pincode, city, state, country):

        address_line_1_div = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['ADDRESS_1'])
        address_line_1_input_field = address_line_1_div.find_element(By.ID, IDS['BILLING_ADDRESS_1'])
        address_line_1_input_field.send_keys(address_1)

        if address_2:
            address_line_2_div = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['ADDRESS_2'])
            address_line_2_input_field = address_line_2_div.find_element(By.ID, IDS['BILLING_ADDRESS_2'])

            address_line_2_input_field.send_keys(address_2)

        city_div = self.driver.find_element(By.ID, IDS['BILLING_CITY'])
        city_div.send_keys(city)

        try:
            pincode_div = self.driver.find_element(By.ID, IDS['BILLING_PINCODE'])
            pincode_div.send_keys(pincode)
        except NoSuchElementException as e:
            pass

        country_div = self.driver.find_element(By.ID, IDS['BILLING_COUNTRY'])
        country_div.send_keys(country)

        try:
            state_div = self.driver.find_element(By.ID, IDS['BILLING_STATE'])
            state_div.send_keys(state)
        except NoSuchElementException as e:
            pass

    def get_price_difference(self, class_names, cart_details):

        details = {}
        for class_name in class_names:

            try:
                price_div = cart_details.find_element(By.CLASS_NAME, class_names[class_name])
                price_text = price_div.find_element(By.CLASS_NAME, CLASS_NAMES['FLIGHT_PRICE']).text
                price_list = price_text.split(' ')
                price = {
                    'currency': price_list[0],
                    'price': price_list[1]
                }

            except NoSuchElementException as e:
                price = {
                    'currency': None,
                    'price': None
                }

            details[class_name] = price

        return details

    def print_receipt(self, reservation_no):

        self.driver.get(MANAGE_BOOKING_URL)

        self.driver.implicitly_wait(5)

        self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['LOAD_MORE_BUTTON']).click()

        manage_buttons = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['MANAGE_UPCOMING_BOOKINGS'])

        for each in manage_buttons:
            data_ref = each.get_attribute('data-ref')
            if data_ref == DATA_REF['MANAGE_BOOKING'].format(reservation_no):
                each.click()
                try:
                    self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['INCOMPLETE_PAYMENT_BUTTON_POPUP'])
                    return -1
                except NoSuchElementException as e:
                    pass
                break

        options = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['OPTIONS_LIST'])
        for option in options:

            if option.text.lower() == 'view booking receipt':
                option.click()

                text = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['PANEL_CONTENT']).text

                self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['EXPANSION_PANEL_BUTTON']).click()
                break

        time.sleep(5)

        reservation_no_div = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['RESERVATION_NO'])
        reservation_no_text = reservation_no_div.text
        reservation_no_text_list = reservation_no_text.split(':')
        reservation_no = reservation_no_text_list[1][1:]

        last_updated_div = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['UPDATED_ON'])
        last_updated_text = last_updated_div.text
        last_updated_text_list = last_updated_text.split(':')
        last_updated = last_updated_text_list[1][1:]

        flight_status_div = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['FLIGHT_STATUS'])
        flight_status_text = flight_status_div.text
        flight_status_text_list = flight_status_text.split(':')
        flight_status = flight_status_text_list[1][1:]

        passengers = self.driver.find_elements(By.CLASS_NAME, 'passenger-section')
        passenger_list = []
        for passenger in passengers:
            passenger_list.append(
                {'name': passenger.text}
            )

        flight_list = self.driver.find_elements(By.CLASS_NAME, 'breakdown-list')
        flight_list.pop()
        flight_details = []
        item_details = []
        for each in flight_list:

            item = each.find_element(By.CLASS_NAME, 'trip-item')
            place_details = item.find_element(By.CLASS_NAME, 'item-label').text.split('to')
            sub_item = item.find_elements(By.CLASS_NAME, 'sub-item')

            for sub in sub_item:
                label = sub.find_element(By.CLASS_NAME, 'item-label').text
                price = sub.find_element(By.CLASS_NAME, 'item-price').text
                item_details.append(
                    {
                        'label': label,
                        'price': price
                    }
                )

            price_list = each.find_element(By.CLASS_NAME, 'list-item--payment-fee')
            total_fee = price_list.find_element(By.CLASS_NAME, 'item-price').text.split(' ')

            flight_details.append(
                {
                    'source': place_details[0],
                    'destination': place_details[1],
                    'item': item_details,
                    'total_fee': {
                        'currency': total_fee[0],
                        'value': total_fee[1]
                    },

                }
            )

        total_price_div = self.driver.find_element(By.CLASS_NAME, 'total-price').text
        total_price_div_list = total_price_div.split(' ')
        details = {
            'reservation_no': reservation_no,
            'last_updated_on': last_updated,
            'flight_status': flight_status,
            'passengers_info': passenger_list,
            'flight_details': flight_details,
            'total_price': {
                'currency': total_price_div_list[-1],
                'value': total_price_div_list[-1]
            }
        }

        return details
