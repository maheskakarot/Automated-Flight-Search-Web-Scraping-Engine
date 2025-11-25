import requests
from utils.decrypt import get_card_details
from utils.card_maksing import cardmapping
from rediscluster import RedisCluster
from custom_logger.models import Email_model
import json
import re
from django.conf import settings
from utils.proxy import get_proxy
from redis import Redis
from easyjet.generator import uuid_generator

class Booking_scraping:
    def booking_scraping(self,passenger_data,bags_json_payload,cookie,total_fare):
        message = ""
        booking_status = 2
        card_request =""
        card_details = ""
        card_data = ""

        passenger_name = passenger_data[0]['FirstName']

        email_details = Booking_scraping.get_email_password(self)

        email = email_details['email']
        pasword = email_details['password']

        XSRF = cookie['RBK-XSRF']

        logs = {}
        
        proxy = get_proxy()
        
        proxies = {
        "http"  : "http://" + proxy[0],
         }


        headers = {
                'ADRUM': 'isAjax:true',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json;charset=UTF-8',
                'Origin': 'https://www.easyjet.com',
                'Referer': 'https://www.easyjet.com/en/buy/bags',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                'X-RBK-XSRF': XSRF,
                'X-Requested-With': 'XMLHttpRequest',
                'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'x-b2b-misc': '',
            }

        json_data = {
            'Products': bags_json_payload,
            'RemoveSimilarProducts': False,
        }

        ''' Selecting Bags'''

        if bags_json_payload:

            response = requests.post(
                'https://www.easyjet.com/ejrebooking/api/v70/funnel/addproducts',
                cookies=cookie,
                headers=headers,
                json=json_data,
                proxies=proxies
            )

            logs['add_bags_api'] = {
            "add_bags_api":{
                "url":'https://www.easyjet.com/ejrebooking/api/v70/funnel/addproducts',
                "body":json_data,
                "stauts":response.status_code,
                "text":response.text
            }
        }

            if response.status_code != 200 :
                message = "Failed in Selecting Bags"

                booking_status = 2
                return message,booking_status,email,logs,card_details,card_data,card_request

            cookie.update(response.cookies.get_dict())

        '''Getting Anti Forgery Token'''

        response = requests.get('https://www.easyjet.com/api/account/v4/antiforgerytoken', headers=headers,cookies=cookie,proxies=proxies)

        logs["anti_forgery_api"] = {
                "url":"https://www.easyjet.com/api/account/v4/antiforgerytoken",
                "stauts":response.status_code,
                "text":response.text
        }


        if response.status_code != 200 :
            message = "Failed in getting Forgery Token"
            booking_status=2
            return message,booking_status,email,logs,card_details,card_data,card_request
        cookie.update(response.cookies.get_dict())

        anti = cookie["DA-Antiforgery-C"]

        headers["X-DA-Antiforgery"] = anti

        
        json_data = {
            'emailAddress': email,
            'password': pasword,
            'keepMeSignedIn': False,
            'cultureCode': 'en-GB',
            'languageCode': 'en',
        }

        '''Login API'''

        response = requests.post('https://www.easyjet.com/api/account/v4/Authenticate/member', headers=headers, json=json_data,cookies=cookie,proxies=proxies)

        logs["login_api"] = {
                "url":'https://www.easyjet.com/api/account/v4/Authenticate/member',
                "body":json_data,
                "stauts":response.status_code,
                "text":response.text
            }

        if response.status_code != 200 :
            message = "Failed in Login"
            booking_status = 2
            return message,booking_status,email,logs,card_details,card_data,card_request
        cookie.update(response.cookies.get_dict())

        json_data = {
            'ReasonForTravelCode': '4|LEIS|',
        }

        del headers["X-DA-Antiforgery"]

        '''Selecting Liesure'''

        response = requests.post(
            'https://www.easyjet.com/ejrebooking/api/v70/funnel/changereasonfortravel',
            headers=headers,
            json=json_data,
            cookies=cookie,
            proxies=proxies
        )


        logs["travel_reason_api"] = {
                "url":'https://www.easyjet.com/ejrebooking/api/v70/funnel/changereasonfortravel',
                "body":json_data,
                "stauts":response.status_code,
                "text":response.text
            }

        if response.status_code != 200 :
            message = 'Failed in selecting reason'
            booking_status = 2
            return message,booking_status,email,logs,card_details,card_data,card_request
        cookie.update(response.cookies.get_dict())

        json_data = {
            'Updates': passenger_data,
        }

        '''Updating Passenger Details'''

        response = requests.post(
            'https://www.easyjet.com/ejrebooking/api/v70/funnel/updatepassengerdetails',
            cookies=cookie,
            headers=headers,
            json=json_data,
            proxies=proxies
        )

        logs["passenger_api"] = {
                "url":'https://www.easyjet.com/ejrebooking/api/v70/funnel/updatepassengerdetails',
                "body":json_data,
                "stauts":response.status_code,
                "text":response.text
            }

        if response.status_code != 200 :
            message = "Failed in Updating Passenger details"
            booking_status = 2
            return message,booking_status,email,logs,card_details,card_data,card_request
        cookie.update(response.cookies.get_dict())

        '''Member Details'''

        response = requests.get(
            'https://www.easyjet.com/ejrebooking/api/v70/funnel/getbasketwithmemberdetails',
                    cookies=cookie,
                    headers=headers,
                    proxies=proxies
                )
        
        logs["member_details_api"] = {
                "url":'https://www.easyjet.com/ejrebooking/api/v70/funnel/getbasketwithmemberdetails',
                "stauts":response.status_code,
                "text":response.text
            }
        
        cookie.update(response.cookies.get_dict())
        if response.status_code != 200 :
            message = "Failed in get Member details"
            booking_status = 2
            return message,booking_status,email,logs,card_details,card_data,card_request
        
        basket_data = response.json()
        adults,child,infant = 0,0,0
        for passengers in passenger_data:
            if passengers["Type"] == 0:
                adults +=1
            elif passengers["Type"] == 1:
                child +=1
            elif passengers['Type'] == 2:
                infant += 1
                
        adult_price = basket_data['JourneyPairs'][0]['OutboundSlot']['Flight']['FlightFares'][0]['Prices']['Adult']['Price']
        total_price = adult_price*adults
        if child :
            child_price = basket_data['JourneyPairs'][0]['OutboundSlot']['Flight']['FlightFares'][0]['Prices']['Child']['Price']
            total_child = child_price * child
            total_price += total_child
        if infant :
            infant_price = basket_data['JourneyPairs'][0]['OutboundSlot']['Flight']['FlightFares'][0]['Prices']['Infant']['Price']
            total_infant = infant_price * infant
            total_price += total_infant
            
        bags_amount = 0
        for bags in bags_json_payload:
            bags_amount += bags["Price"]
            
        total = float(round(total_price+bags_amount,2))
        
        if total_price > total_fare:
            message = "Failed because of price change"
            return message,booking_status,email,logs,card_details,card_data,card_request
        
        card_details,card_data,card_request = Booking_scraping.card_data_mapping(self,total)

        card_num = card_details['result']['data']['cardNo']
        cvv = card_details['result']['data']['cvv']
        exp_month = card_details['result']['data']['expiryMonth']
        exp_year = card_details['result']['data']['expiryYear']
        card_type = card_details['result']['data']['cardType'].lower()
        card_account_type = card_details['result']['data']['cardAccountType']
    

        if card_account_type == "Credit":
            is_creditcard = True
        else:
            is_creditcard = False

        if card_type == "american axpress":
            code = "AX"

        elif card_type == "mastercard":
            code = "MC"

        elif card_type == "diners club":
            code = "DC"

        elif card_type == "visa":
            code = "VI"

        elif card_type == "american express":
            code = "AX"

        elif card_type == "uatp":
            code = "TP"

        elif card_type == "airplus":
            code = "TP"
            is_creditcard = True
            cvv = ''

        visa_re_pattern = "^(40|41|42|43|44|45|46|47|48|49)"
        if re.match(visa_re_pattern,str(card_num)) :
            code = "DL"
            is_creditcard = False

        amex_re_pattern = "^(34|37)"
        if re.match(amex_re_pattern,str(card_num)) :
            code = "AX"


        masterCard_pattern = "^(22|23|24|25|26|27|51|52|53|54|55|561|581|674)"
        if re.match(masterCard_pattern,str(card_num)) :
            code = "MC"

        dc_pattern =  "^(36|60|64|65)"
        if re.match(dc_pattern,str(card_num)):
            code = "DC"
             
        uatp_pattern = "^(10|11|12|13|14|15|16|17|18|19)"
        if re.match(uatp_pattern,str(card_num)):
            code = "TP"
            cvv = ''
            is_creditcard = True
        debit_mastercard_pattern = "^(675|676|677|670|671|673|679|678)"
        if re.match(debit_mastercard_pattern,str(card_num)):
            code = "DM"
         
        json_data = {
            "PaymentMethod": 0,
            "PaymentCard": {
                "PaymentCard": str(card_num),
                "PaymentCard": int(exp_month),
                "ExpirationYear": int(exp_year),
                "ExpirationYear": None,
                "NameOnCard": passenger_name,
                "SecurityCode": cvv,
                "IsCreditCard": is_creditcard,
                "CardVendorCode": code,
                "SavePaymentCard": False,
                "UseSavedPaymentCard": False,
            },
            "ApplePayPayment": None,
            "AllowDuplicateBooking": False,
            "DisplayedTotalBasketPrice": {
                "PriceWithCreditCard": total,
                "PriceWithDebitCard": total,
                "Price": total,
            },
            "AddNewMember": False,
            "AddNewMemberPassword": None,
            "CultureCode": "en-GB",
            "ExcludeSavedCardSecurityData": False,
            "ThreeDS2Parameters": {
                "SecureId": None,
                "BrowserData": {
                    "ColourDepth": 24,
                    "JavaEnabled": False,
                    "JavaScriptEnabled": True,
                    "Language": "en-GB",
                    "ScreenHeight": 720,
                    "ScreenWidth": 1280,
                    "TimeZoneOffset": -330,
                },
                "PaymentParameters": {
                    "ChallengeNotificationUrl": "https://www.easyjet.com/ejrebooking/api/v70/threeds2/challengenotification",
                    "CustomerServiceUrl": "https://www.easyjet.com/en/help/contact",
                },
                "FingerprintingParameters": None,
                "ChallengeParameters": None,
            },
            "Voucher": None,
        }

        '''Payment'''
        method = "POST"
        
        for ip in proxy:
            proxies = {
                "http"  : "http://" + ip,
            }
            
            response = requests.post(
            'https://www.easyjet.com/ejrebooking/api/v70/funnel/finalize',
            cookies=cookie,
            headers=headers,
            json=json_data,
            proxies=proxies
        )
            if response.status_code != 403:
                break
                

        
    
        logs["payment_api"] = {
                "url":'https://www.easyjet.com/ejrebooking/api/v70/funnel/finalize',
                "body":json_data,
                "stauts":response.status_code,
                "text":response.text
            }
        
        payment_uuid = uuid_generator()
        cookie.update(response.cookies.get_dict())
        
        # payment_res = requests.get(url=f"https://www.easyjet.com/en/buy/payment?sc_itemid={payment_uuid}",
        #                            cookies=cookie,
        #                            headers=headers)
        # cookie.update(payment_res.cookies.get_dict())

        if response.status_code == 502 :
            message = "Wrong Card Details entered"
            booking_status = 2
            return message,booking_status,email,logs,card_details,card_data,card_request
        
        
        """PNR Scraping"""

        response = requests.get('https://www.easyjet.com/ejrebooking/api/v70/funnel/getbasket', cookies=cookie, headers=headers,proxies=proxies)
        logs["pnr_api"] = {
                "url":'https://www.easyjet.com/ejrebooking/api/v70/funnel/getbasket',
                "stauts":response.status_code,
                "text":response.text
            }

        if response.status_code != 200 :
            message = f"{response.status_code} Failed in PNR API"
            return message,booking_status,email,logs,card_details,card_data,card_request
        
        booking_data = response.json()

        pnr = booking_data['BookingReference']
        if len(pnr):
            booking_status = 1


        return pnr,booking_status,email,logs,card_details,card_data,card_request
        

    def card_data_mapping(self,amount):

        request_data = {
                "amount":amount,
                "bookingRef": str(self.data["BookRef"]),
                "clientId": "0",
                "currency": self.data["BaseCurrency"],
                "externalIdentifiers": {
                    "externalIdentifiers1": str(self.data["BookRef"]),
                    "externalIdentifiers2": self.passengers[0]['FirstName'],
                    "externalIdentifiers3": self.flight_details[0]['DepartureDateTime'],
                    "externalIdentifiers4": self.data["SupplierCode"],
                    "externalIdentifiers5":  self.flight_details[0]['DepartureAirport']+"-"+self.flight_details[0]['ArrivalAirport']
                },
                "firstName": self.passengers[0]['FirstName'],
                "lastName": self.passengers[0]['LastName'],
                "searchId": self.data["SearchIdentifier"],
                "virtualAccountId": self.account_id
            }
        
        
        card_details = get_card_details(self.data["MysCardConfig"],request_data, api="Book")

        # Expiry_date = card_details['result']['data']['expiryMonth']+card_details['result']['data']['expiryYear']

        # card_data=cardmapping(card_details['result']['data']['cardNo'],card_details['result']['data']['cvv'],Expiry_date)
        # card_data['nameOnCard'] = card_details['result']['data']['nameOnCard']
        # card_data['Credit']=  card_details['result']['data']['Credit']
        # card_data['referenceNumber']=card_details['result']['data']['referenceNumber']
        # card_data['vendorId']=  card_details['result']['data']['vendorId']
        # card_data['vpaID']=  card_details['result']['data']['vpaID']
        # card_data['accountNo']=  card_details['result']['data']['accountNo']
        card_data = card_details
        

        return card_details,card_data,request_data


    def get_email_password(self):
        startup_nodes = settings.REDIS_CLUSTER_NODES
        #production redis
        r = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)
        #dev_redis
        # r = Redis(host="10.10.0.4",port=6379,db=0)
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

    def generate_curl_command(self,method, url, headers=None, data=None):
        curl_command = f'curl -X {method} {url}'
        if headers:
            for key, value in headers.items():
                curl_command += f" -H '{key}: {value}'"
        if data:
            data_str = str(data).replace("'", r"\'")
            curl_command += f" -d '{data_str}'"

        return curl_command






