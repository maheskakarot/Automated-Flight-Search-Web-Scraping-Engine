import time
import copy
from selenium.webdriver.common.action_chains import ActionChains
from v1.ryanair.constants.xpaths import XPATHS
from v1.ryanair.constants.class_names import CLASS_NAMES
from v1.ryanair.constants.reprice import PRICE_INFO_STRUCTURE
from v1.ryanair.constants.css_selectors import CSS_SELECTORS
from v1.ryanair.constants.cookies import COOKIES
from v1.ryanair.constants.data_ref import DATA_REF
from .basket import RyanAirBasket


class CommonActions:
    def __init__(self, driver):
        self.driver = driver

    def login(self, user_email, user_password):
        """
        This function will be used to log in to ryanair website
        """
        is_logged_in = False
        try:
            self.driver.find_element_by_xpath(XPATHS['EMAIL_FIELD']).send_keys(user_email)
            self.driver.find_element_by_xpath(XPATHS['PASSWORD_FIELD']).send_keys(user_password)
            self.driver.find_element_by_xpath(XPATHS['SIGN_IN_BUTTON']).click()
            is_logged_in = True

            # TODO: Read confirmation code from user inbox and submit to website part is left.

        except Exception as ex:
            print(ex)
            # TODO: Add alert here

        return is_logged_in

    def submit_confirmation_code(self, code):
        self.driver.find_element_by_xpath(XPATHS['CONFIRMATION_CODE_SUBMIT_BOX']).send_keys(code)
        self.driver.find_element_by_class_name(CLASS_NAMES['VERIFY_BTN']).click()

    def accept_cookies(self):
        """
        This function will be used to close the popup of cookies arrived when we visit the website for the first time.
        """
        is_clicked = False
        try:
            self.driver.find_element_by_xpath(XPATHS['AGREE_COOKIE_BUTTON']).click()
            is_clicked = True

        except Exception as ex:
            print(ex)
            # TODO: Add alert here

        return is_clicked

    def edit_flight_button(self):
        """
        This function will be used to click on "Edit Flight" button on flights search result page to minimise the fare
        distribution screen.
        """
        self.driver.find_elements_by_class_name(CLASS_NAMES['EDIT_FLIGHT_BUTTON'])[0].click()
        time.sleep(0.3)
        return None

    def scroll_to_element(self, element):
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()

    def click_on_login_later_button(self):
        self.driver.find_element_by_class_name(CLASS_NAMES['LOGIN_LATER']).click()

    def click_on_continue_flow_button(self):
        self.driver.find_element_by_class_name(CLASS_NAMES['CONTINUE_FLOW_BUTTON']).click()

    def click_on_continue_button(self):
        self.driver.implicitly_wait(10)
        element = self.driver.find_element_by_class_name(CLASS_NAMES['CONTINUE_YELLOW_GRADIENT_BUTTON'])
        self.scroll_to_element(element)
        element.click()
        self.driver.implicitly_wait(10)

    def click_on_container_cta(self):
        self.driver.find_element_by_class_name(CLASS_NAMES['APP_CONTAINER_CTA']).click()

    def click_on_checkout_button(self):
        self.driver.implicitly_wait(15)
        self.driver.find_element_by_class_name(CLASS_NAMES['CHECKOUT_BTN']).click()

    def click_on_cart_button(self, sleep=True):
        self.driver.find_element_by_class_name(CLASS_NAMES['CART_BTN_2']).click()

    def scrape_cart_items(self, is_return_trip, fare_type, response_data):
        ryanair_basket_obj = RyanAirBasket(self.driver, request_data={})
        self.click_on_cart_button()
        ryanair_basket_obj.click_on_full_details_button(fare_type)

        if is_return_trip:
            basket_data = ryanair_basket_obj.scrape_basket_items(fare_type)

        else:
            basket_data = ryanair_basket_obj.scrape_basket_items(fare_type)

        print("Responses")

        response_data['CartItems']['DepartureFlightInfo'] = {}
        response_data['CartItems']['ArrivalFlightInfo'] = {}
        response_data['CartItems']['DepartureFlightInfo']['SeatsInfo'] = basket_data['departure_items_info']
        response_data['CartItems']['DepartureFlightInfo']['DiscountsInfo'] = basket_data[
            'departure_discount_items_info']
        response_data['CartItems']['DepartureFlightInfo']['TaxInfo'] = basket_data['departure_tax_items_info']
        response_data['CartItems']['DepartureFlightInfo']['FastTrackInfo'] = basket_data['departure_fast_track_info']
        response_data['CartItems']['DepartureFlightInfo']['AdditionalSeatsInfo'] = basket_data[
            'departure_additional_seat_info']
        response_data['CartItems']['DepartureFlightInfo']['PaidItemsInfo'] = basket_data['departure_paid_items_data']
        response_data['CartItems']['DepartureFlightInfo']['Extras'] = basket_data['departure_extras']

        if is_return_trip:
            response_data['CartItems']['ArrivalFlightInfo']['SeatsInfo'] = basket_data['arrival_items_info']
            response_data['CartItems']['ArrivalFlightInfo']['DiscountsInfo'] = basket_data[
                'arrival_discount_items_info']
            response_data['CartItems']['ArrivalFlightInfo']['TaxInfo'] = basket_data['arrival_tax_items_info']
            response_data['CartItems']['ArrivalFlightInfo']['FastTrackInfo'] = basket_data['arrival_fast_track_info']
            response_data['CartItems']['ArrivalFlightInfo']['AdditionalSeatsInfo'] = basket_data[
                'arrival_additional_seat_info']
            response_data['CartItems']['ArrivalFlightInfo']['PaidItemsInfo'] = basket_data['arrival_paid_items_data']
            response_data['CartItems']['ArrivalFlightInfo']['Extras'] = basket_data['arrival_extras']

        response_data['CartItems']['TotalAmountToPay'] = self.scrape_total_amount_to_pay()

        self.click_on_cart_button(sleep=True)

        return response_data

    def scrape_one_way_cart_items(self):
        from .basket import RyanAirBasket

        ryan_air_basket_obj = RyanAirBasket(self.driver, request_data={})

        basket_items_info = {}
        discount_items_info = []
        tax_items_info = []

        time.sleep(2)
        basket_items = self.driver.find_elements_by_class_name(CLASS_NAMES['BASKET_ITEMS'])

        item_number = 0
        if basket_items:
            for basket_item in basket_items:
                basket_item_list = basket_item.text.splitlines()
                print(basket_item_list)

                item_number += 1

                # ['2 x Adult Value Fare', '£', '35', '.', '98']
                # ['2 x', 'Adult Plus Fare', '£', '115', '.', '16']
                if len(basket_item_list) != 5 and len(basket_item_list) != 6 \
                        and len(basket_item_list) != 3:
                    continue

                # Expected basket item - ['2 x Infant fee', '£', '50', '.', '00']
                if ' x ' in basket_item_list[0]:
                    seat_count, seat_type = basket_item_list[0].split(" x ")

                    fare_info = ryan_air_basket_obj.scrape_seat_fare_info(basket_item_list)
                    fare_info = copy.deepcopy(fare_info)

                    items_included, paid_item_data = ryan_air_basket_obj.scrape_one_way_items_included(item_number)

                    basket_items_info = ryan_air_basket_obj.seat_info(basket_items_info,
                                                                      ryan_air_basket_obj.get_seat_type(seat_type),
                                                                      seat_count, items_included, fare_info)

                    if paid_item_data:
                        basket_items_info[ryan_air_basket_obj.get_seat_type(seat_type)]["paid_item"] = paid_item_data
                        basket_items_info = copy.deepcopy(basket_items_info)

                # Expected basket item - ['2 x', 'Adult Plus Fare', '£', '115', '.', '16']
                elif ' x' in basket_item_list[0]:

                    seat_count = basket_item_list[0].split(" x")[0]
                    seat_type = basket_item_list[1]

                    fare_info = ryan_air_basket_obj.scrape_seat_fare_info(basket_item_list)
                    fare_info = copy.deepcopy(fare_info)

                    items_included, paid_item_data = ryan_air_basket_obj.scrape_one_way_items_included(item_number)

                    basket_items_info = ryan_air_basket_obj.seat_info(basket_items_info,
                                                                      ryan_air_basket_obj.get_seat_type(seat_type),
                                                                      seat_count, items_included, fare_info)

                    if paid_item_data:
                        basket_items_info[ryan_air_basket_obj.get_seat_type(seat_type)]["paid_item"] = paid_item_data
                        basket_items_info = copy.deepcopy(basket_items_info)

                # ['basket.tax-dr', '€', '25', '.', '00']
                elif 'tax' in basket_item_list[0]:
                    tax_item_info = ryan_air_basket_obj.tax_item_response(basket_item_list)

                    tax_item_info = copy.deepcopy(tax_item_info)
                    tax_items_info.append(tax_item_info)

                # Item is of discount type - ['UK APD discount', '-', '£', '26', '.', '00']
                elif 'discount' in basket_item_list[0] or 'saved' in basket_item_list[0]:

                    discount_item_info = ryan_air_basket_obj.discount_item_response(basket_item_list)

                    discount_item_info = copy.deepcopy(discount_item_info)
                    discount_items_info.append(discount_item_info)

                basket_items_info = copy.deepcopy(basket_items_info)

        return basket_items_info, discount_items_info, tax_items_info

    def scrape_return_trip_basket_items(self, fare_type):
        from .basket import RyanAirBasket

        ryan_air_basket_obj = RyanAirBasket(self.driver, request_data={})

        departure_items_info = arrival_items_info = {}
        departure_discount_items_info = arrival_discount_items_info = []
        departure_tax_items_info = arrival_tax_items_info = []
        departure_fast_track_info = arrival_fast_track_info = []

        items = self.driver.find_elements_by_css_selector(CSS_SELECTORS['RETURN_TRIP_PRICE_BREAKDOWN'])

        if len(items) == 2:
            departure_items = items[0]
            arrival_items = items[1]

            departure_items_info, departure_discount_items_info, departure_tax_items_info, departure_fast_track_info = ryan_air_basket_obj.scrape_cart_items(
                departure_items, fare_type)
            arrival_items_info, arrival_discount_items_info, arrival_tax_items_info, arrival_fast_track_info = ryan_air_basket_obj.scrape_cart_items(
                arrival_items, fare_type)

        basket_data = {
            'departure_items_info': departure_items_info,
            'arrival_items_info': arrival_items_info,
            'departure_discount_items_info': departure_discount_items_info,
            'departure_fast_track_info': departure_fast_track_info,
            'arrival_discount_items_info': arrival_discount_items_info,
            'departure_tax_items_info': departure_tax_items_info,
            'arrival_tax_items_info': arrival_tax_items_info,
            'arrival_fast_track_info': arrival_fast_track_info,
        }

        return basket_data

    def scrape_total_amount_to_pay(self):
        """
        :return: total_pay_response: This will contain information of total amount(currency, amount) which user have to
        pay to continue for booking.
        """
        total_pay_response = PRICE_INFO_STRUCTURE
        total_pay = self.driver.find_element_by_class_name(CLASS_NAMES['TOTAL_PAY'])

        total_pay_item_list = total_pay.text.splitlines()

        # Expected sample list - ['Total to pay', '£', '26', '.', '99']
        if len(total_pay_item_list) == 5:
            total_pay_response['currency'] = total_pay_item_list[1]
            total_pay_response['value'] = float("{}{}{}".format(total_pay_item_list[2], total_pay_item_list[3],
                                                                total_pay_item_list[4]).replace(",", ""))

        elif len(total_pay_item_list) == 3:
            total_pay_response['currency'] = total_pay_item_list[1]
            total_pay_response['value'] = float("{}".format(total_pay_item_list[2]).replace(",", ""))

        return total_pay_response

    def load_cookies_into_driver(self, useremail):
        cookies = COOKIES[useremail]
        for cookie in cookies:
            self.driver.add_cookie(cookie)

        return self.driver

    def keep_session_alive(self):
        self.driver.implicitly_wait(2)
        elements = self.driver.find_elements_by_class_name(CLASS_NAMES['KEEP_ALIVE_BTN'])
        for element in elements:
            if element.get_attribute('data-ref') == DATA_REF['KEEP_ALIVE']:
                element.click()
        self.driver.implicitly_wait(10)

    def close_small_popup_box(self):
        self.driver.implicitly_wait(2)
        try:
            self.driver.find_element_by_class_name("counter-tooltip__icon-close").click()
        except Exception as ex:
            print(ex)
        self.driver.implicitly_wait(10)

    def close_baggages_warning_box(self):
        self.driver.implicitly_wait(2)
        try:
            print("Button")
            btn = self.driver.find_element_by_xpath(XPATHS['CLOSE_WARNING_BTN'])
            btn.click()
            print("clicked")
        except Exception as ex:
            print(ex)
        self.driver.implicitly_wait(10)
