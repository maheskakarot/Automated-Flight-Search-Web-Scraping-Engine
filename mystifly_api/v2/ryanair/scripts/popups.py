import time
from v1.ryanair.constants.class_names import CLASS_NAMES
from .common import CommonActions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class HandlePopups():
    def __init__(self, driver, request_data):
        self.driver = driver
        self.request_data = request_data
        self.common_actions_objs = CommonActions(self.driver)

    def dismiss_baggages_popup(self):
        self.driver.implicitly_wait(10)
        try:
            self.driver.find_element_by_class_name(CLASS_NAMES['DISMISS_POPUP_BTN']).click()
        except Exception as ex:
            print("dismiss_baggages_popup - ", ex)
        self.driver.implicitly_wait(10)

    def dismiss_crowd_popup(self, fare_type):

        # FPF - Flexi Plus Fare, In Flexi Plus fare this popup is not shown
        if fare_type != "FPF":
            try:
                wait = WebDriverWait(self.driver, 10)
                crowd_popup_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, CLASS_NAMES['DISMISS_CROWD_POPUP_BTN'])))
                crowd_popup_btn.click()
            except Exception as ex:
                print("dismiss_crowd_popup - ", ex)

        return None

    def dismiss_family_seating_popup(self):
        self.driver.implicitly_wait(10)
        for i in range(5):
            try:
                wait = WebDriverWait(self.driver, 10)
                family_seating_cta_btn = wait.until(
                    EC.element_to_be_clickable((By.CLASS_NAME, CLASS_NAMES['FAMILY_SEATING_CTA_BTN'])))
                self.common_actions_objs.scroll_to_element(family_seating_cta_btn)
                family_seating_cta_btn.click()
                break
            except Exception as ex:
                print(ex)
            print("Handling family seating cta", i)
            time.sleep(2)

        self.driver.implicitly_wait(10)

    def selected_wrong_infant_seat(self):
        from .seats_selection import SeatSelection
        seat_selection_instance = SeatSelection(self.driver, self.request_data)
        warning_title = warning_body = None
        try:

            warning_body = self.driver.find_element_by_class_name(CLASS_NAMES['WARNING_BODY']).text
            self.driver.find_element_by_class_name(CLASS_NAMES['SELECT_NEW_SEATS_BTN']).click()
            warning_title = "Issue while selecting seats"
            seat_selection_instance.release_selected_seats()

        except Exception as ex:
            print("Error while closing select new seats btn popup - ", ex)

        return warning_title, warning_body

    def check_active_session(self):
        self.driver.implicitly_wait(1)

        session_active = True
        warning_heading = None
        warning_body = None
        error = {}

        try:

            warning_heading = self.driver.find_element_by_class_name(CLASS_NAMES['SESSION_EXPIRED_HEADING']).text
            warning_body = self.driver.find_element_by_class_name(CLASS_NAMES['SESSION_EXPIRED_BODY']).text
            session_active = False

        except Exception as ex:
            print("Session is not expired")

        self.driver.implicitly_wait(10)

        if not session_active:
            error = {
                'warning_title': warning_heading,
                'warning_body': warning_body
            }

        return error




