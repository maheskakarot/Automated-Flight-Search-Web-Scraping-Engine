import copy
import time
from v1.ryanair.constants.class_names import CLASS_NAMES
from v1.ryanair.constants.fares_data import FARE_TYPE_BUTTON_CODES
from v1.ryanair.constants.xpaths import XPATHS
from v1.ryanair.constants.css_selectors import CSS_SELECTORS
from v1.ryanair.constants.data_ref import DATA_REF
from v1.ryanair.constants.reprice import (
    SEATS_INFO_STRUCTURE, PRICE_INFO_STRUCTURE, DISCOUNT_OR_TAX_RESPONSE_STRUCTURE
)


class RyanAirBasket:
    """
    This class contains methods related to website basket/cart.
    """

    def __init__(self, driver, request_data):
        self.driver = driver
        self.request_data = request_data

        # This is to handle currency change issue
        self.handle_currency = False

    def click_on_full_details_button(self, fare_type):
        """
        :working: We are using this function to click on all view full details button in user basket to see hidden info.
        :return: None
        """
        view_full_details_buttons = self.driver.find_elements_by_class_name(CLASS_NAMES['VIEW_FULL_DETAILS'])

        button_number = 0
        for view_full_details_button in view_full_details_buttons:
            button_number += 1

            if (button_number == 1 or button_number == 3) and fare_type == FARE_TYPE_BUTTON_CODES['FAMILY_PLUS_FARE']:
                continue

            time.sleep(0.2)
            view_full_details_button.click()

    def scrape_one_way_basket_items(self):
        """
        :working: We are using this function to scrap data of items selected by user.
        :return: basket_items_info: This will contain data of items selected by user.
        discount_items_info: This will contain data of discounts applied for user.
        """
        basket_items_info = {}
        discount_items_info = []
        tax_items_info = []

        time.sleep(0.5)
        basket_items = self.driver.find_elements_by_class_name(CLASS_NAMES['BASKET_ITEMS'])

        item_number = 0
        if basket_items:
            for basket_item in basket_items:
                basket_item_list = basket_item.text.splitlines()

                item_number += 1

                # ['2 x Adult Value Fare', '£', '35', '.', '98']
                # ['2 x', 'Adult Plus Fare', '£', '115', '.', '16']
                if len(basket_item_list) != 5 and len(basket_item_list) != 6 \
                        and len(basket_item_list) != 3:
                    continue

                # Expected basket item - ['2 x Infant fee', '£', '50', '.', '00']
                if ' x ' in basket_item_list[0]:
                    seat_count, seat_type = basket_item_list[0].split(" x ")

                    fare_info = self.scrape_seat_fare_info(basket_item_list)
                    fare_info = copy.deepcopy(fare_info)

                    items_included, paid_item_data = self.scrape_one_way_items_included(item_number)

                    basket_items_info = self.seat_info(basket_items_info, self.get_seat_type(seat_type), seat_count,
                                                       items_included, fare_info)

                    if paid_item_data:
                        basket_items_info[self.get_seat_type(seat_type)]["paid_item"] = paid_item_data
                        basket_items_info = copy.deepcopy(basket_items_info)

                # Expected basket item - ['2 x', 'Adult Plus Fare', '£', '115', '.', '16']
                elif ' x' in basket_item_list[0]:

                    seat_count = basket_item_list[0].split(" x")[0]
                    seat_type = basket_item_list[1]

                    fare_info = self.scrape_seat_fare_info(basket_item_list)
                    fare_info = copy.deepcopy(fare_info)

                    # items_included, paid_item_data = self.scrape_one_way_items_included(item_number)
                    items_included, paid_item_data = self.scrape_return_trip_included_items(basket_items,
                                                                                            basket_item_list, "VF")

                    basket_items_info = self.seat_info(basket_items_info, self.get_seat_type(seat_type), seat_count,
                                                       items_included, fare_info)

                    if paid_item_data:
                        basket_items_info[self.get_seat_type(seat_type)]["paid_item"] = paid_item_data
                        basket_items_info = copy.deepcopy(basket_items_info)

                # ['basket.tax-dr', '€', '25', '.', '00']
                elif 'tax' in basket_item_list[0].lower():
                    tax_item_info = self.tax_item_response(basket_item_list)

                    tax_item_info = copy.deepcopy(tax_item_info)
                    tax_items_info.append(tax_item_info)

                # Item is of discount type - ['UK APD discount', '-', '£', '26', '.', '00']
                elif 'discount' in basket_item_list[0].lower() or 'saved' in basket_item_list[0].lower():

                    discount_item_info = self.discount_item_response(basket_item_list)

                    discount_item_info = copy.deepcopy(discount_item_info)
                    discount_items_info.append(discount_item_info)

                basket_items_info = copy.deepcopy(basket_items_info)

        return basket_items_info, discount_items_info, tax_items_info

    def scrape_one_way_items_included(self, item_number):
        """
        :param item_number: This is the position of item in user's basket
        :return: included_items: This will contain information related to items included.
        """
        included_items = []
        paid_item_data = {}
        included_items_list = self.driver.find_element_by_xpath(
            XPATHS['CART_ITEM'].format(item_number)).text.splitlines()

        # Expected list - ['1 x', 'Child Plus Fare', '€', '238', '.', '48', 'View full details',
        # '1 x 20kg check-in bag', 'Included', '1 x Free check-in at the airport', 'Included',
        # '1 x Small Bag (40cm x 20cm x 25cm)', 'Included']
        if included_items_list:

            if "1 x Reserved seat" in included_items_list:
                x = included_items_list.index("1 x Reserved seat")

                paid_item_data["name"] = "1 x Reserved seat"
                paid_item_data["price_info"] = PRICE_INFO_STRUCTURE
                paid_item_data["price_info"]["currency"] = included_items_list[x + 1]

                if self.handle_currency:
                    paid_item_data["price_info"]["value"] = float("{}".format(
                        included_items_list[x + 2]).replace(",", ""))

                else:
                    paid_item_data["price_info"]["value"] = float("{}{}{}".format(
                        included_items_list[x + 2],
                        included_items_list[x + 3],
                        included_items_list[x + 4]).replace(",", ""))

            included_items = self.prepare_included_items_list(included_items_list, included_items)

        return included_items, paid_item_data

    def scrape_total_amount_to_pay(self):
        """
        :return: total_pay_response: This will contain information of total amount(currency, amount) which user have to
        pay to continue for booking.
        """
        total_pay_response = PRICE_INFO_STRUCTURE

        time.sleep(0.3)

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

    # TODO: Make this function static as its not using self param.
    def seat_info(self, basket_items_info, seat_type, seat_count, items_included, fare_info):
        """
        :param paid_items_data:
        :param basket_items_info:
        :param seat_type:
        :param seat_count:
        :param items_included:
        :param fare_info:
        :return:
        """
        if seat_type:
            basket_items_info[seat_type] = {}
            basket_items_info[seat_type]["seat_count"] = int(seat_count)
            basket_items_info[seat_type]["items_included"] = items_included
            basket_items_info[seat_type]["items_description"] = []
            basket_items_info[seat_type]["fare_info"] = fare_info

        return basket_items_info

    # TODO: Make this function static as its not using self param.
    def get_seat_type(self, seat_type):
        if "Adult" in seat_type:
            return "adult_seats_info"

        elif "Child" in seat_type:
            return "child_seats_info"

        elif 'Infant' in seat_type:
            return "infants_seats_info"

        elif 'Family Plus' in seat_type:
            return "family_plus_upgrade"

        else:
            return None

    def scrape_return_trip_basket_items(self, fare_type):
        departure_items_info = arrival_items_info = {}
        departure_discount_items_info = arrival_discount_items_info = []
        departure_tax_items_info = arrival_tax_items_info = []

        items = self.driver.find_elements_by_css_selector(CSS_SELECTORS['RETURN_TRIP_PRICE_BREAKDOWN'])

        if len(items) == 2:
            departure_items = items[0]
            arrival_items = items[1]

            departure_items_info, departure_discount_items_info, departure_tax_items_info = self.scrape_cart_items(
                departure_items, fare_type)
            arrival_items_info, arrival_discount_items_info, arrival_tax_items_info = self.scrape_cart_items(
                arrival_items, fare_type)

        basket_data = {
            'departure_items_info': departure_items_info,
            'arrival_items_info': arrival_items_info,
            'departure_discount_items_info': departure_discount_items_info,
            'arrival_discount_items_info': arrival_discount_items_info,
            'departure_tax_items_info': departure_tax_items_info,
            'arrival_tax_items_info': arrival_tax_items_info,
        }

        return basket_data

    def scrape_basket_items(self, fare_type):
        departure_items_info = arrival_items_info = {}
        departure_discount_items_info = arrival_discount_items_info = []
        departure_tax_items_info = arrival_tax_items_info = []

        items = self.driver.find_elements_by_css_selector(CSS_SELECTORS['RETURN_TRIP_PRICE_BREAKDOWN'])

        if len(items) == 2:
            departure_items = items[0]
            arrival_items = items[1]

            departure_items_info, departure_discount_items_info, departure_tax_items_info = self.scrape_cart_items(
                departure_items, fare_type)
            arrival_items_info, arrival_discount_items_info, arrival_tax_items_info = self.scrape_cart_items(
                arrival_items, fare_type)

        elif len(items) == 1:
            departure_items = items[0]

            departure_items_info, departure_discount_items_info, departure_tax_items_info = self.scrape_cart_items(
                departure_items, fare_type)

        basket_data = {
            'departure_items_info': departure_items_info,
            'arrival_items_info': arrival_items_info,
            'departure_discount_items_info': departure_discount_items_info,
            'arrival_discount_items_info': arrival_discount_items_info,
            'departure_tax_items_info': departure_tax_items_info,
            'arrival_tax_items_info': arrival_tax_items_info,
        }

        return basket_data

    def scrape_cart_items(self, cart_items, fare_type):
        basket_items_info = {}
        discount_items_info = []
        tax_items_info = []

        items = cart_items.find_elements_by_class_name(CLASS_NAMES['BASKET_ITEMS'])

        for item in items:
            item_list = item.text.splitlines()

            if 'discount' in item_list[0].lower() or 'saved' in item_list[0].lower():
                discount_item_info = self.discount_item_response(item_list)
                discount_item_info = copy.deepcopy(discount_item_info)
                discount_items_info.append(discount_item_info)

            elif 'tax' in item_list[0].lower():
                tax_item_info = self.tax_item_response(item_list)

                tax_item_info = copy.deepcopy(tax_item_info)
                tax_items_info.append(tax_item_info)

            else:
                seat_count, seat_type = self.extract_seats_count(item_list)
                fare_info = self.scrape_seat_fare_info(item_list)
                fare_info = copy.deepcopy(fare_info)

                items_included, paid_item_data = self.scrape_included_items(cart_items, item_list, fare_type)

                basket_items_info = self.seat_info(basket_items_info, self.get_seat_type(seat_type), seat_count,
                                                   items_included, fare_info)

                if paid_item_data:
                    basket_items_info[self.get_seat_type(seat_type)]["paid_item"] = paid_item_data
                    basket_items_info = copy.deepcopy(basket_items_info)

            basket_items_info = copy.deepcopy(basket_items_info)

        return basket_items_info, discount_items_info, tax_items_info

    # TODO: Make this function static as its not using self param.
    def scrape_included_items(self, departure_items, parent_item_list, fare_type):
        included_items = []
        paid_item_data = {}

        adult_conditions = [
            'Adult' in parent_item_list[0],
            'Adult' in parent_item_list[1],
        ]

        child_conditions = [
            'Child' in parent_item_list[0],
            'Child' in parent_item_list[1]
        ]

        family_upgrade_conditions = [
            'Family' in parent_item_list[1]
        ]

        if not any(adult_conditions + child_conditions + family_upgrade_conditions):
            return included_items, paid_item_data

        sub_items = departure_items.find_elements_by_css_selector(CSS_SELECTORS['CART_ITEMS'])

        for sub_item in sub_items:

            if any(adult_conditions):
                data_ref = 'ADULT'

            elif any(child_conditions):
                data_ref = 'CHILD'

            else:
                data_ref = 'FAMILY_UPGRADE'

            if sub_item.get_attribute('data-ref') == DATA_REF['BASE_DATA_REF'] + DATA_REF[fare_type][data_ref]:
                included_items_list = sub_item.text.splitlines()

                if "1 x Reserved seat" in included_items_list:
                    x = included_items_list.index("1 x Reserved seat")

                    if included_items_list[x + 1] == "Included":
                        continue

                    paid_item_data["name"] = "1 x Reserved seat"
                    paid_item_data["price_info"] = PRICE_INFO_STRUCTURE
                    paid_item_data["price_info"]["currency"] = included_items_list[x + 1]

                    if self.handle_currency:
                        paid_item_data["price_info"]["value"] = float("{}".format(
                            included_items_list[x + 2]).replace(",", ""))

                    else:
                        paid_item_data["price_info"]["value"] = float("{}{}{}".format(
                            included_items_list[x + 2],
                            included_items_list[x + 3],
                            included_items_list[x + 4]).replace(",", ""))

                included_items = self.prepare_included_items_list(included_items_list, included_items)

        return included_items, paid_item_data

    def prepare_included_items_list(self, included_items_list, included_items):
        included_items_indexes = [i for i in range(len(included_items_list)) if
                                  included_items_list[i] == "Included"]

        for included_items_index in included_items_indexes:
            item = included_items_list[included_items_index - 1]

            if " & " in item:
                items = item.split(" & ")
                included_items += items
            else:
                included_items.append(item)

        return included_items

    # TODO: Make this function static as its not using self param.
    def scrape_seat_fare_info(self, parent_item_list):
        price_info = PRICE_INFO_STRUCTURE
        currency = value = None

        if len(parent_item_list) == 5:
            currency = parent_item_list[1]
            value = float(
                "{}{}{}".format(parent_item_list[2], parent_item_list[3], parent_item_list[4]).replace(",", ""))

        elif len(parent_item_list) == 6:
            currency = parent_item_list[2]
            value = float(
                "{}{}{}".format(parent_item_list[3], parent_item_list[4], parent_item_list[5]).replace(",", ""))

        elif len(parent_item_list) == 3:
            self.handle_currency = True
            currency = parent_item_list[1]
            value = float("{}".format(parent_item_list[2]).replace(",", ""))

        elif len(parent_item_list) == 4:
            self.handle_currency = True
            currency = parent_item_list[2]
            value = float("{}".format(parent_item_list[3]).replace(",", ""))

        price_info['currency'] = currency
        price_info['value'] = value

        return price_info

    # TODO: Make this function static as its not using self param.
    def extract_seats_count(self, parent_item_list):
        seat_count = seat_type = None
        print(parent_item_list)

        # ['1 x Adult Value Fare', 'Ft', '11,715']
        # ['1 x Adult Value Fare', '$', '15', '.', '56']
        if len(parent_item_list) == 5 or len(parent_item_list) == 3:
            seat_count, seat_type = parent_item_list[0].split(" x ")

        elif len(parent_item_list) == 6 or len(parent_item_list) == 4:
            seat_count = parent_item_list[0].split(" x")[0]
            seat_type = parent_item_list[1]

        return seat_count, seat_type

    # TODO: Make this function static as its not using self param.
    def discount_item_response(self, parent_item_list):
        discount_item_info = DISCOUNT_OR_TAX_RESPONSE_STRUCTURE
        discount_item_info['name'] = parent_item_list[0]
        discount_item_info['price_info'] = PRICE_INFO_STRUCTURE
        discount_item_info['price_info']['currency'] = parent_item_list[2]

        if self.handle_currency:
            discount_item_info['price_info']['value'] = float("{}".format(parent_item_list[3]).replace(",", ""))

        else:
            discount_item_info['price_info']['value'] = float("{}{}{}".format(parent_item_list[3],
                                                                              parent_item_list[4],
                                                                              parent_item_list[5]).replace(",", ""))

        return discount_item_info

    def tax_item_response(self, parent_item_list):
        tax_item_info = DISCOUNT_OR_TAX_RESPONSE_STRUCTURE
        tax_item_info['name'] = parent_item_list[0]
        tax_item_info['price_info'] = PRICE_INFO_STRUCTURE
        tax_item_info['price_info']['currency'] = parent_item_list[1]
        if self.handle_currency:
            tax_item_info['price_info']['value'] = float("{}".format(parent_item_list[2]).replace(",", ""))

        else:
            tax_item_info['price_info']['value'] = float("{}{}{}".format(parent_item_list[2],
                                                                         parent_item_list[3],
                                                                         parent_item_list[4]).replace(",", ""))

        return tax_item_info
