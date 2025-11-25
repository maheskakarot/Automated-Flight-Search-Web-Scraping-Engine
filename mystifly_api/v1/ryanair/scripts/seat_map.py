from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from v1.ryanair.constants.class_names import CLASS_NAMES


class SeatMap:

    def __init__(self, driver):
        self.driver = driver
        self.price = ''
        self.currency = ''

    def get_seat_map(self):



        seat_map = {}
        total_row = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['TOTAL_SEAT_ROW'])
        price_dic = {}
        seat_price_category_list = ['EXTRA_LEG_PRICE', 'PRIORITY_PRICE', 'STANDARD_PRICE']
        seat_category_list = ['EXTRA_LEG_SEAT', 'PRIORITY_SEAT', 'STANDARD_SEAT']
        seat_price_map = {
            'EXTRA_LEG_SEAT': 'EXTRA_LEG_PRICE',
            'PRIORITY_SEAT': 'PRIORITY_PRICE',
            'STANDARD_SEAT': 'STANDARD_PRICE'
        }
        for each_row in total_row:
            self.scrap_seat_price(each_row, price_dic, seat_price_category_list)

            total_seat_div = each_row.find_element(By.CLASS_NAME, CLASS_NAMES['TOTAL_SEATS'])
            self.create_seat_map(seat_category_list, seat_map, price_dic, total_seat_div, seat_price_map)

        return seat_map

    def update_seat_number(self, seat_number):
        seat_type = ''

        if 'A' in seat_number:
            seat_number += "(W)"
            seat_type = 'window'

        elif 'B' in seat_number:
            seat_number += "(M)"
            seat_type = 'middle'

        elif 'C' in seat_number:
            seat_number += "(A)"
            seat_type = 'aisle'

        elif 'D' in seat_number:
            seat_number += "(A)"

            seat_type = 'aisle'

        elif 'E' in seat_number:
            seat_number += "(M)"
            seat_type = 'middle'

        elif 'F' in seat_number:
            seat_number += "(W)"
            seat_type = 'window'

        return seat_number, seat_type

    def scrap_seat_price(self, each_row, price_dic, seat_category_list):

        for seat_category in seat_category_list:
            try:
                price_tag = each_row.find_element(By.CLASS_NAME, CLASS_NAMES[seat_category]).text
                price_list = price_tag.split('\n')
                if len(price_list) == 3:
                    self.price = price_list[2]
                    self.currency = price_list[1]
                elif len(price_list) == 2:
                    self.price = price_list[1]
                    self.currency = price_list[0]
                elif len(price_list) == 1:
                    self.price = None
                    self.currency = None
            except NoSuchElementException:
                pass

            price_dic[seat_category] = {
                'price': self.price,
                'currency': self.currency
            }

    def create_seat_map(self, category_list, seat_map, price_dic, total_seat_div, seat_price_map):

        for category in category_list:
            try:
                standard_seat = total_seat_div.find_elements(By.CLASS_NAME, CLASS_NAMES[category])
                for each_seat in standard_seat:
                    seat_number = each_seat.get_attribute('id').split("-")[1]
                    seat_number, seat_type = self.update_seat_number(seat_number)
                    seat_map[seat_number] = {
                        'value': price_dic[seat_price_map[category]]['price'],
                        'currency': price_dic[seat_price_map[category]]['currency'], 'type': seat_type
                    }
            except NoSuchElementException:
                pass
