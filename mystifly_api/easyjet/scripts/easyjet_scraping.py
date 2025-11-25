import time
from datetime import datetime
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from easyjet.config import XPATH, CSS_SELECTORS, WEBSITE
from django.conf import settings
import requests
from utils.error_logging import easyjet_error_email
from redis import Redis
from rediscluster import RedisCluster
from custom_logger.models import Email_model
from utils.easyjet_web_driver import WebDriver
from easyjet.scripts.booking_auotmation import BookingAutomation


class Scraping:
        
    def flight_selection_scraping(self,data):
        try:
            flight_search_data = BookingAutomation(data).get_flight_select_data()
            self.depature_date = flight_search_data['depature_date']
            self.search_identifier = data["SearchIdentifier"]
            self.required_data = BookingAutomation(data).get_required_details()
            self.driver = WebDriver().driver
            self.driver.get(WEBSITE["easyjet"])
            
            self.driver.find_element(By.CSS_SELECTOR,'[aria-label="Close consent Widget"]').click()
            screen_width = self.driver.execute_script("return window.screen.width;")
            screen_height = self.driver.execute_script("return window.screen.height;")
            self.driver.set_window_size(screen_width/2, screen_height)
            if data["AirTripType"] ==1:
                self.driver.find_element(By.CSS_SELECTOR,'[for="one-way"]').click()
            self.driver.find_element(By.CSS_SELECTOR,'[name="origin"]').clear()
            self.driver.find_element(By.CSS_SELECTOR,'[name="origin"]').send_keys(flight_search_data["depature_flight"])
            self.driver.find_element(By.CSS_SELECTOR,'[class="ui-autocomplete ui-front ui-menu ui-widget ui-widget-content ui-corner-all"]').click()
            time.sleep(0.5)
            self.driver.find_element(By.CSS_SELECTOR,'[aria-label="To Airport"]').clear()
            self.driver.find_element(By.CSS_SELECTOR,'[aria-label="To Airport"]').send_keys(flight_search_data["arrival_flight"])
            element_pass = self.driver.find_elements(By.CSS_SELECTOR,'[class="passenger-type"]')
            element_pass[0].click()
            passenger_data,self.passenger_details = BookingAutomation(data).get_passenger_details()
            add_passenger = self.driver.find_elements(By.CSS_SELECTOR,'[class="quantity-button-add"]')
            if passenger_data["adult"] : 
                for _ in range(passenger_data["adult"]-1):
                    add_passenger[0].click()

            if passenger_data["child"]:
                for _ in range(passenger_data["child"]):
                    add_passenger[1].click()

            if passenger_data["infant"]:
                for _ in range(passenger_data["infant"]):
                    add_passenger[2].click()


            self.driver.find_element(By.CLASS_NAME,"outbound-date-picker").click()
            time.sleep(1)
            try:
                element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-date="{flight_search_data["depature_date"]}"]')))
                element.click()
            except:
                time.sleep(2)
                element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-date="{flight_search_data["depature_date"]}"]')))
                element.click()

            if data["AirTripType"] ==2:
                element = self.driver.find_elements(By.CSS_SELECTOR, f'[data-date="{flight_search_data["return_deptature_date"]}"]')
                ActionChains(self.driver).move_to_element(element[1]).pause(2).click().perform()

            time.sleep(0.5)

            self.driver.find_element(By.CSS_SELECTOR,'[ej-click-event="SubmitFlightSearch()"]').click()
            self.driver.maximize_window()
            try:
                time.sleep(2)
                self.driver.find_element(By.XPATH, '//div[@class="drawer-button"]/button[contains(text(), "OK, continue")]').click()
            except Exception:
                pass
            try:
                if passenger_data["infant"]:
                    time.sleep(1)
                    self.driver.find_element(By.XPATH, '//div[@class="drawer-button"]/button[contains(text(), "OK, continue")]').click()
            except:
                pass

            return ""
        except Exception as e:
            if settings.IS_KIBANA_ENABLED:
                easyjet_error_email(self.driver,self.search_identifier,"Easyjet Homepage",e,)
            self.driver.quit()    
            return "Failed in Homepage"            
    def select_flights(self,flight_search_data,data): 
        try:   
            depature_time = flight_search_data["depature_time"][:5]
            arrival_time = flight_search_data["arrival_time"][:5]
            
            # Switch to the new tab
            window_handles = self.driver.window_handles
            if len(window_handles) > 1:
                self.driver.switch_to.window(window_handles[1])
            
            depature_date = int(flight_search_data["depature_date"][8::])
            time.sleep(2.5)
            flight_data = self.driver.find_elements(By.CSS_SELECTOR,'[ng-repeat="day in Days"]')
            dep_time,arr_time = "",""
            for flights_info in flight_data:
                flights = (flights_info.text.splitlines())
                for flight_data in flights:
                    if flight_data == depature_time:
                        dep_time = flight_data
                    elif flight_data == arrival_time:
                        arr_time = flight_data
                if dep_time:
                    if depature_date == int(flights[1][:2]) and depature_time == dep_time and arrival_time == arr_time:
                        flights_info.find_element(
                            'xpath',
                            f'//h4//span[contains(text(), "{flights[1]}")]//..//following-sibling::div//span[@class="flight-grid-flight-header"]//span[contains(text(), "{dep_time}")]',
                        ).click()

                    if data["AirTripType"] == 2: 
                        return_dep_time,return_arr_time ="",""
                        return_date = int(flight_search_data["return_deptature_date"][8::])
                        for flight_data in flights:
                            if return_date==int(flights[1][:2]) and  flight_search_data['return_depature_time'][:5]==flight_data:
                                return_dep_time =  flight_search_data['return_depature_time'][:5]
                            elif return_date==int(flights[1][:2]) and flight_search_data['return_arrival_time'][:5] == flight_data:
                                return_arr_time =  flight_search_data['return_arrival_time'][:5]


                        time.sleep(3)
                        if return_dep_time:
                            
                            if return_date == int(flights[1][:2]) and flight_search_data['return_depature_time'][:5] == return_dep_time and flight_search_data['return_arrival_time'][:5] == return_arr_time:
                                flights_info.find_element(
                                    'xpath',
                                    f'//h4//span[contains(text(), "{flights[1]}")]//..//following-sibling::div//span[@class="flight-grid-flight-header"]//span[contains(text(), "{return_dep_time}")]',
                                ).click()
            return ""
        except Exception as e:
            if settings.IS_KIBANA_ENABLED:
                easyjet_error_email(self.driver,data['SearchIdentifier'],"Easyjet Flight Selection",e,)
            self.driver.quit()
            return "Failed in Selecting Flights"             
    def scrape_extra_services(self):
        
        try:
            self.extra_service_amount = 0

            for passengers in self.passenger_details:
                if  passengers['ListExtraServices']:
                    if self.extra_service_amount == 0:
                        self.driver.get(WEBSITE["bags"])
                    time.sleep(5)
                    kgs = passengers['ListExtraServices'][0]["ServiceDetails"].split(' ')[0]
                    self.driver.find_element(By.CSS_SELECTOR,f'[aria-label="Add a {kgs} bag"]').click()
                    self.extra_service_amount += passengers['ListExtraServices'][0]["Amount"]

                    
                    time.sleep(2)
            return ""
        except Exception as e:
            if settings.IS_KIBANA_ENABLED:
                easyjet_error_email(self.driver,self.search_identifier,"Easyjet Extra Services",e,)
            self.driver.quit() 
            return "Failed in selecting bags"        
    def login_website(self):
        try:
            self.driver.get('https://www.easyjet.com/en/buy/checkout')
            email_password = Scraping.get_email_password(self)
            # email_password = {'email': "hijaxop@finmail.com",
            #                   "password":"Hijaxop@123"}
            try:
                time.sleep(2)
                self.driver.find_element(By.CSS_SELECTOR,'[name="email"]').send_keys(email_password['email'])
                self.driver.find_element(By.CSS_SELECTOR,'[name="password"]').send_keys(email_password['password'])
                time.sleep(3)
                self.driver.find_element(By.CSS_SELECTOR,'[id="signin-login"]').click()
            except Exception:
                time.sleep(2)
                self.driver.find_element(By.CSS_SELECTOR,'[aria-label="Please enter your email address"]').send_keys(email_password['email'])
                self.driver.find_element(By.CSS_SELECTOR,'[name="existing-password"]').send_keys(email_password['password'])
                time.sleep(3)
                self.driver.find_element(By.CSS_SELECTOR,'[id="existing-customer-sign-in"]').click()
                            
            message = ""
            return message,email_password["email"]
        except Exception as e:
            if settings.IS_KIBANA_ENABLED:
                easyjet_error_email(self.driver,self.search_identifier,"Login Page",e)
            self.driver.quit() 
            message = "Failed in Login Page"
            return message,email_password["email"]
    def enter_passenger_details(self):
        try:
            time.sleep(3)
            try:
                self.driver.find_element(By.CSS_SELECTOR,'[value="4|LEIS|"]').click()
            except:
                time.sleep(5)
                self.driver.find_element(By.CSS_SELECTOR,'[value="4|LEIS|"]').click()
            time.sleep(0.5)
            adult,child,infant = 1,1,1
            for passengers in self.passenger_details:       
                dob = passengers['DateOfBirth']
                age = Scraping.calculate_age(self,dob)
                first_name=passengers["FirstName"]
                last_name = passengers['LastName']
                if passengers['Title'] == "MSTR":
                    passengers['Title']= "Mr"
                if age >= 16:
                    name = "adult"
                    Scraping.select_passenger(self,name,passengers['Title'],first_name,last_name,age,adult)
                    adult+=1
                elif age >= 2 and age <16:
                    if passengers['Title'] == "Ms":
                        passengers['Title']= "Miss"
                    name = "child"
                    Scraping.select_passenger(self,name,passengers['Title'],first_name,last_name,age,child)
                    child +=1
                elif age < 2:    
                    fname = self.driver.find_element(By.ID,f"firstname-textbox-infant-{infant}")
                    fname.send_keys(first_name)
                    l_name=self.driver.find_element(By.ID,f"lastname-textbox-infant-{infant}")
                    l_name.send_keys(last_name)
                    infant +=1
            time.sleep(2)    
            self.driver.find_element(By.XPATH,"//input[contains(@ng-model, 'InsuranceNudgeCtrl.HasInsurance') and @name='has-insurance-yes']").click()  
            time.sleep(2)
            self.driver.find_element(By.XPATH,"//div[4]/button[@aria-label='Save changes to this section and continue']").click()
            return ""
        except Exception as e:
            if settings.IS_KIBANA_ENABLED:
                easyjet_error_email(self.driver,self.search_identifier,"Easyjet Passenger Details",e,)
            self.driver.quit() 
            return "Failed in Entering Passenger Details"
    def compare_fare_price(self,data):
        time.sleep(3)
        try:
            basket_amount = ''
            while not basket_amount:
                basket_amount = self.driver.find_element(By.CSS_SELECTOR,'[ej-price="GetTotalPrice()"]').text
            if "£" in basket_amount:
                basket_amount = basket_amount[1::]
                if len(basket_amount.split(".")[0])>3:
                    splited_amount = basket_amount.split(",")
                    basket_amount = splited_amount[0]+splited_amount[1]
                    
            if '€' in basket_amount:
                basket_amount = basket_amount[:-2]
                if len(basket_amount.split(".")[0])>3:
                    splited_amount = basket_amount.split(",")
                    basket_amount = splited_amount[0]+splited_amount[1]

            self.basket_amount = float(basket_amount)
            
            total_amount = data['TotalFare']
            tolerance_amount = data['ToleranceAmount']

            
            if (total_amount+tolerance_amount) < (self.basket_amount-self.extra_service_amount):
                self.driver.quit()
                return "Failed because of price change"
            time.sleep(1)
            self.driver.find_element('xpath', '//label[@for="payment-page-terms-checkbox"]//span[contains(@class, "checkbox")]').click()
            self.driver.find_element(By.XPATH,'//button[contains(@aria-label, "Continue to payment")]').click()
            return ""
        except Exception as e:
            if settings.IS_KIBANA_ENABLED:
                easyjet_error_email(self.driver,self.search_identifier,"Easyjet Price Compare",e,)
            self.driver.quit() 
            return "Failed in Price comparison and Selecting Insurance Cover"                 
    def payment(self,data):
        
        try:
            card_details,message = BookingAutomation(data).card_data_mapping(self.basket_amount)
          
            if message :
                error = "Failed in Card Services"
                if settings.IS_KIBANA_ENABLED:
                    easyjet_error_email(self.driver,self.search_identifier,"Easyjet Payment",e,)
                self.driver.quit()
                return error
          
            card_number = int(card_details['result']['data']['cardNo'])
            expiry_month = int(card_details['result']['data']['expiryMonth'])
            expiry_year = int("20"+card_details['result']['data']['expiryYear'][2:])
            cvv = int(card_details['result']['data']['cvv'])
            #Testing Card Details
            # card_number = 4532690215905388 
            # expiry_month=2
            # expiry_year=2024
            # cvv = 234
            self.driver.find_element(By.CSS_SELECTOR,'[id="card-details-card-number"]').send_keys(card_number)
            self.driver.find_element(By.ID,"card-details-card-holders-name").send_keys(self.passenger_details[0]["FirstName"]) 
            exp_mont = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "card-details-expiry-date-month")))
            exp_year = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "card-details-expiry-date-year")))
            exp_mont.find_element(By.CSS_SELECTOR,f'option[value="{expiry_month}"]').click()
            exp_year.find_element(By.CSS_SELECTOR,f'option[label="{expiry_year}"]').click()
            try:
                time.sleep(1)
                self.driver.find_element(By.ID,"card-details-security-number").send_keys(cvv)
            except:
                pass
            time.sleep(1)
            self.driver.find_element(By.CSS_SELECTOR,'[aria-label="Pay now, with obligation to pay"]').click()
            message = ""
            return message
        except Exception as e:
            print(e)
            if settings.IS_KIBANA_ENABLED:
                easyjet_error_email(self.driver,self.search_identifier,"Easyjet Payment",e,)
            self.driver.quit() 
            message = "Failed in Payment"
            return message
    def get_pnr(self):
        time.sleep(10)
        pnr_data,pnr="",""
        try:
            wait = WebDriverWait(self.driver, 10)
            try:
                while len(pnr_data) != 5:
                    data = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '[class="title-bar-data notranslate centered-container"]')))
                    pnr_data = data.text
                    # pnr_data = "Your booking K583DML is confirmed"
                    pnr_data =pnr_data.split(" ")
                pnr = pnr_data[2]
                print(pnr)
            except:
                    data = wait.until(EC.visibility_of_element_located((By.XPATH, '*//div/div/h1/@class="title-bar-data notranslate centered-container"')))
                    pnr_data = data.text
                    pnr = pnr_data.split(" ")[2]
            return "",pnr,pnr_data
        except Exception as e:
            if settings.IS_KIBANA_ENABLED:
                easyjet_error_email(self.driver,self.search_identifier,"Easyjet PNR Page",e,)
            self.driver.quit() 
            return "Failed in Scraping PNR",pnr,pnr_data            
    def get_email_password(self):        
        startup_nodes = settings.REDIS_CLUSTER_NODES
        #production redis
        if settings.IS_PRODUCTION :
            r = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)
        #dev_redis
        else:
            r = Redis(host="10.10.0.4",port=6379,db=0)
        key = 'EASYJET_EMAIL_LIST'
        email_list = r.exists(key)
        if not email_list:
            objects = Email_model.objects.all().filter(Airline_code="U2S")
            for object in objects:
                d = {'email': object.email, 'password': object.password}
                r.rpush(key, json.dumps(d))

        current_email =json.loads(r.rpop(key))

        r.lpush(key, json.dumps(current_email))

        return current_email                
    def calculate_age(self,dob):
        birth_date = dob
        depature_date = self.depature_date
        depature_obj = datetime.strptime(depature_date, "%Y-%m-%d")
        birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d")  
        age_timedelta = depature_obj - birth_date_obj

        return age_timedelta.days // 365    
    def select_passenger(self,type,title,first_name,last_name,age,adult_count):
        title_parent=self.driver.find_element(By.ID,f"title-dropdown-{type}-{adult_count}")
        title_parent.find_element(By.CSS_SELECTOR,f'option[value="string:{title}"]').click()        
        f_name=self.driver.find_element(By.ID,f"firstname-textbox-{type}-{adult_count}")
        f_name.clear()
        f_name.send_keys(first_name)
        l_name=self.driver.find_element(By.ID,f"lastname-textbox-{type}-{adult_count}")
        l_name.clear()
        l_name.send_keys(last_name)
        age_parent=self.driver.find_element(By.ID,f"age-dropdown-{type}-{adult_count}")
        if age>=18:
            age_parent.find_element(By.CSS_SELECTOR,'option[value="number:18"]').click()

        else:
            age_parent.find_element(By.CSS_SELECTOR,f'option[value="number:{age}"]').click()

        adult_count +=1


    def call_scraping_functions(self,data):
        pnr = ""
        
        message = Scraping.flight_selection_scraping(self,data)
        if message:
            message_response,response=BookingAutomation(data).generate_booking_response(message,pnr)
            return message_response,response
        flight_search_data = BookingAutomation(data).get_flight_select_data()
        
        message = Scraping.select_flights(self,flight_search_data,data)
        if message:
            message_response,response=BookingAutomation(data).generate_booking_response(message,pnr)
            return message_response,response
        
        message = Scraping.scrape_extra_services(self)
        if message:
            message_response,response=BookingAutomation(data).generate_booking_response(message,pnr)
            return message_response,response
        
        message,email = Scraping.login_website(self)
        if message:
            message_response,response=BookingAutomation(data).generate_booking_response(message,pnr)
            return message_response,response
        
        message = Scraping.enter_passenger_details(self)
        if message:
            message_response,response=BookingAutomation(data).generate_booking_response(message,pnr)
            return message_response,response
        
        message = Scraping.compare_fare_price(self,data)
        if message:
            message_response,response=BookingAutomation(data).generate_booking_response(message,pnr)
            return message_response,response
        
        message = Scraping.payment(self,data)
        if message:
            message_response,response=BookingAutomation(data).generate_booking_response(str(message),pnr)
            return message_response,response
        
        message,pnr,pnr_data = Scraping.get_pnr(self)
        if message:
            message_response,response=BookingAutomation(data).generate_booking_response(message,pnr)
            return message_response,response
    
        message_response,response=BookingAutomation(data).generate_booking_response(message,pnr,pnr_data=pnr_data,email=email)
        
        
        return message_response,response