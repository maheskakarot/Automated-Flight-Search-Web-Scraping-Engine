import time
from v1.ryanair.constants.class_names import CLASS_NAMES
from v1.ryanair.constants.xpaths import XPATHS
from v1.ryanair.constants.data_ref import DATA_REF
from .common import CommonActions


class FastTrack:

    def __init__(self, driver, booking_request):
        self.driver = driver
        self.booking_request = booking_request
        self.common_actions_obj = CommonActions(self.driver)

    def add_fastrack(self):
        fastrack_info = self.booking_request.get("FastTrackInfo", {})

        if fastrack_info:
            departure_flight_info = fastrack_info.get("DepartureFlight", {})
            arrival_flight_info = fastrack_info.get("ArrivalFlight", {})

            self.add_fastrack_in_trip(departure_flight_info, flight_type="Departure",
                                      data_ref=DATA_REF['DEPT_FAST_TRACK'])

            self.add_fastrack_in_trip(arrival_flight_info, flight_type="Arrival",
                                      data_ref=DATA_REF['ARVL_FAST_TRACK'])

    def add_fastrack_in_trip(self, flight_info, flight_type, data_ref):
        if flight_info:
            add_to_all = flight_info.get('AddToAll', False)

            if add_to_all:
                self.fastrack_all_passengers(flight_type=flight_type)

            else:
                passengers_info = flight_info.get('PassengersInfo', [])

                if passengers_info:
                    add_per_passenger_btn = self.driver.find_element_by_class_name(CLASS_NAMES['ADD_PER_PASSENGER_BTN'])
                    self.common_actions_obj.scroll_to_element(add_per_passenger_btn)
                    add_per_passenger_btn.click()
                    time.sleep(2)
                    self.add_fastrack_passenger_wise(passengers_info, data_ref)

                done_btn = self.driver.find_element_by_class_name(CLASS_NAMES['DONE_BTN'])
                done_btn.click()

    def get_target_div_element(self, target_data_ref):
        target_element = None
        elements = self.driver.find_elements_by_class_name(CLASS_NAMES['BASE_CLASS'])

        for element in elements:
            data_ref = element.get_attribute("data-ref")
            if data_ref == target_data_ref:
                target_element = element
                break

        return target_element

    # Will add fast track for all passengers for selected flight type
    def fastrack_all_passengers(self, flight_type="Departure"):
        fast_track_cards = self.driver.find_elements_by_class_name(CLASS_NAMES['FAST_TRACK_CARD'])

        if flight_type == "Departure":
            card = fast_track_cards[0]

        else:
            card = fast_track_cards[1]

        card.find_element_by_class_name(CLASS_NAMES['ADD_ALL_BTN']).click()

    def add_fastrack_passenger_wise(self, passengers_info, data_ref):
        div_constant = 1
        if data_ref == DATA_REF['ARVL_FAST_TRACK']:
            div_constant = 2
        i = 2
        for passenger_info in passengers_info:
            if passenger_info["AddFastTrack"]:
                target_div_element = self.get_target_div_element(data_ref)
                passenger_elements = target_div_element.find_elements_by_class_name(CLASS_NAMES['PASSENGER_ITEM'])

                for passenger_element in passenger_elements:
                    passenger_name = passenger_element.text.splitlines()[1]
                    if passenger_info["Name"].lower() in passenger_name.lower():
                        add_button = passenger_element.find_element_by_xpath(
                            XPATHS['FAST_TRACK_ADD_BTN'].format(div_constant, i))
                        add_button.click()
                        time.sleep(1.5)
                        i += 1
                        break

    def retrieve_fast_track_info(self):
        fast_track_info = []
        fast_track_cards = self.driver.find_elements_by_class_name(CLASS_NAMES['FAST_TRACK_CARD'])

        for fast_track_card in fast_track_cards:
            is_available = True
            included = False
            message = "Fast track is available."

            item_list = fast_track_card.text.splitlines()
            card = item_list[0]

            if "Not available" in item_list:
                is_available = False
                message = "Fast track is not available."
                data = {
                    "Card": card,
                    "PriceInfo": {
                        "currency": None,
                        "value": None,
                    },
                    "IsAvailable": is_available,
                    "Included": included,
                    "message": message,
                }

            elif "Included with Flexi Plus" in item_list:
                is_available = False
                included = True
                message = "Fast track is already included."

                data = {
                    "Card": card,
                    "PriceInfo": {
                        "currency": None,
                        "value": None,
                    },
                    "IsAvailable": is_available,
                    "Included": included,
                    "message": message,
                }

            else:
                currency = item_list[3]

                if len(item_list) == 8:
                    value = float("{}{}{}".format(item_list[4], item_list[5], item_list[6]).replace(",", ""))

                else:
                    value = float("{}".format(item_list[4]).replace(",", ""))

                data = {
                    "Card": card,
                    "PriceInfo": {
                        "currency": currency,
                        "value": value,
                    },
                    "IsAvailable": is_available,
                    "Included": included,
                    "message": message,
                }

            fast_track_info.append(data)

        return fast_track_info


