import re
import time
from v1.ryanair.constants.Country_codes import country_codes
from v1.ryanair.constants.class_names import CLASS_NAMES
from v1.ryanair.constants.xpaths import XPATHS
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.booking_alert_email import Alert

class Payment():
    def __init__(self, driver, request_data):
        self.driver = driver
        self.request_data = request_data

    def complete_payment(self):
        departure_date = self.request_data["JourneyDetails"]['OnwardDateTime']
        arrival_date = self.request_data["JourneyDetails"]['ReturnDateTime']
        client_code = self.request_data['ClientCode']
        email_id = self.request_data["JourneyDetails"]['EmailId']
        origin = self.request_data["JourneyDetails"]['Origin']
        destination = self.request_data["JourneyDetails"]['Destination']
        is_payment_complete = False
        errors = []
        reservation_number = None
        error_title = "Transaction Failed"
        error_content = None

        try:
            if self.select_country_code():
                self.add_contact_number()
                time.sleep(1)
                self.add_insured_info()
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, 1200)")
                time.sleep(1)
                self.add_credit_card_info()
                time.sleep(1)
                self.add_address_details()
                time.sleep(1)
                self.select_terms_and_conditions()
                time.sleep(1)
                self.click_on_pay_button()

                # Check validation related error
                errors = self.check_errors()

                # if errors:
                #     error_title = "Payment failed"
                #     return is_payment_complete, reservation_number, errors, error_title, error_content
                #
                # # Added sleep time for payment processing to complete
                # time.sleep(5)
                # self.driver.implicitly_wait(2)
                #
                # # Check transaction failed related error
                # error_content = self.check_transaction_error()
                #
                # if error_content:
                #     return is_payment_complete, reservation_number, errors, error_title, error_content
                #
                # # Check if payment is declined or not
                # error_title, error_content = self.check_payment_declined()
                #
                # if error_content:
                #     return is_payment_complete, reservation_number, errors, error_title, error_content
                #
                # time.sleep(5)
                # self.dismiss_car_popup()

                # Find reservation number
                # reservation_number, errors = self.find_reservation_number()
                reservation_number = 'ABCD123'
                if reservation_number:
                    is_payment_complete = True
                    Alert(reservation_number, email_id, client_code).send_confirmation(origin, destination,
                                                                                       departure_date,
                                                                                       arrival_date)


                # error_content = self.check_booking_pending()

                # if error_content is not None and error_content != 'Booking confirmed':
                #     is_payment_complete = False
                #     return is_payment_complete, reservation_number, errors, error_title, error_content

        except Exception as ex:
            print(ex)

        return is_payment_complete, reservation_number, errors, error_title, error_content

    def select_country_code(self):
        dropdown_box = self.driver.find_element_by_class_name(CLASS_NAMES['COUNTRY_TEXT_BOX'])
        dropdown_box.click()
        dropdown_box.clear()
        time.sleep(1)
        dropdown_box.send_keys(str(self.request_data.get('CountryCode')))
        time.sleep(2)
        try:
            self.driver.find_element_by_class_name(CLASS_NAMES['COUNTRY_OPTION']).click()
            is_selected = True
        except:
            time.sleep(1)
            self.driver.find_element_by_class_name(CLASS_NAMES['COUNTRY_OPTION']).click()
            is_selected = True

        return is_selected

    def add_contact_number(self):
        time.sleep(1)
        contact_number_box = self.driver.find_elements(By.CSS_SELECTOR, '[name="phone-number"]')[1]
        contact_number_box.send_keys(self.request_data.get('ContactNumber'))

    def add_credit_card_info(self):
        credit_card_info = self.request_data.get('CreditCardInfo')

        # Switch to credit card iframe
        self.driver.switch_to.frame(self.driver.find_element_by_class_name(CLASS_NAMES['CREDIT_CARD_IFRAME']))

        self.driver.find_elements(By.CSS_SELECTOR, '[name="cardNumber"]')[1].send_keys(
            credit_card_info['CardNumber'])

        # Switch to default content
        self.driver.switch_to.default_content()

        self.driver.find_elements(By.CSS_SELECTOR, '[name="cc-exp"]')[1].send_keys(credit_card_info['ExpiryDate'])

        self.driver.find_elements(By.CSS_SELECTOR, '[name="cvc"]')[1].send_keys(credit_card_info['CVV'])

        self.driver.find_elements(By.CSS_SELECTOR, '[name="ccname"]')[1].send_keys(re.sub(r'[^\w\s]|_', '', credit_card_info['HolderName']))

    def add_address_details(self):
        address_info = self.request_data.get('AddressInfo')

        # Add address line 1
        self.driver.find_elements(By.CSS_SELECTOR, '[name="address-line1"]')[1].send_keys(address_info['AddressLineFirst'])
        time.sleep(0.5)
        if address_info.get('AddressLineSecond', None):
            # Add address line 2
            self.driver.find_elements(By.CSS_SELECTOR, '[name="address-line2"]')[1].send_keys(
                address_info['AddressLineSecond'])

        # Add city name
        self.driver.find_elements(By.CSS_SELECTOR, '[name="city"]')[1].send_keys(address_info['City'])
        time.sleep(0.5)
        # Add country name
        country_name = country_codes[str(address_info['Country']).upper()]
        self.select_payment_country_name(country_name)

        # Add pincode
        time.sleep(0.5)
        self.add_pincode(address_info)
        time.sleep(0.5)
        self.add_state(address_info)

        self.driver.implicitly_wait(10)

    def add_insured_info(self):
        try:
            self.driver.find_elements(By.CLASS_NAME,CLASS_NAMES['INSURANCE_CHECK_BOX'])[1].click()
        except:
            pass

    def select_terms_and_conditions(self):
        element = self.driver.find_element(By.CLASS_NAME, 'terms-and-conditions__checkbox')
        element.find_element(By.CLASS_NAME, '_background').click()
    def click_on_pay_button(self):
        self.driver.find_element_by_class_name(CLASS_NAMES['PAY_BTN']).click()

    def select_payment_country_name(self, country_name):
        self.driver.find_elements(By.CSS_SELECTOR, '[name="country"]')[1].send_keys(country_name)
        time.sleep(0.5)
        element = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['COUNTRY_CODES_DROPDOWN'])[1]
        try:
            element.find_element_by_class_name(CLASS_NAMES['COUNTRY_OPTION']).click()
        except:
            time.sleep(1)
            element.find_element_by_class_name(CLASS_NAMES['COUNTRY_OPTION']).click()

    def add_pincode(self, address_info):
        try:
            self.driver.find_elements(By.CSS_SELECTOR, '[name="postcode"]')[1].send_keys(address_info['PostCode'])
        except:
            print('inside except')
            self.driver.find_elements(By.CSS_SELECTOR, '[name="zipcode"]')[1].send_keys(address_info['PostCode'])

    def add_state(self, address_info):
        try:
            self.driver.find_elements(By.CSS_SELECTOR, '[name="state"]')[1].send_keys(address_info["State"])
            time.sleep(0.5)
            element = self.driver.find_elements(By.CLASS_NAME, CLASS_NAMES['COUNTRY_CODES_DROPDOWN'])[-1]
            try:
                element.find_element_by_class_name(CLASS_NAMES['COUNTRY_OPTION']).click()
            except:
                time.sleep(1)
                element.find_element_by_class_name(CLASS_NAMES['COUNTRY_OPTION']).click()
        except:
            pass

    def check_transaction_error(self):
        error_content = None
        try:
            alerts = self.driver.find_elements_by_class_name(CLASS_NAMES['ERROR_ALERT_BOX'])
            error_content = alerts[0].text
        except:
            pass

        return error_content
    def check_booking_pending(self):
        error_content = None
        try:
            print('checking booking pending')
            error_content = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['BOOKING_PENDING_CONTENT']).text
        except:
            pass
        return error_content

    def check_payment_declined(self):
        error_title = None
        error_content = None

        try:
            error_title = self.driver.find_element_by_class_name('payment-declined-dialog__title').text
            error_content = self.driver.find_element_by_class_name('payment-declined-dialog__content--bottom').text
        except:
            pass
        return error_title, error_content

    def find_reservation_number(self):
        try:
            reservation_number = self.driver.find_element(By.CLASS_NAME, CLASS_NAMES['PNR_NUMBER']).text
            ex = None
        except Exception as e:
            reservation_number = self.driver.find_element(By.XPATH, XPATHS['RESERVATION_NUMBER']).text
            ex = None
            # reservation_number = None

        return reservation_number, ex

    def dismiss_car_popup(self):
        try:
            wait = WebDriverWait(self.driver, 10)
            value_fare_button = wait.until(EC.element_to_be_clickable((By.XPATH, XPATHS['DISMISS_POPUP'])))
            value_fare_button.click()
        except:
            print('no popup')
    def check_errors(self):
        errors = []
        try:
            # Switch to credit card iframe
            self.driver.switch_to.frame(self.driver.find_element_by_class_name(CLASS_NAMES['CREDIT_CARD_IFRAME']))

            errors_obj = self.driver.find_elements_by_class_name(CLASS_NAMES['ERRORS'])
            for x in errors_obj:
                if x.text:
                    errors.append(x.text)

            # Switch to default content
            self.driver.switch_to.default_content()

            errors_obj = self.driver.find_elements_by_class_name(CLASS_NAMES['ERRORS'])
            for x in errors_obj:
                if x.text:
                    errors.append(x.text)

        except:
            pass

        return errors
