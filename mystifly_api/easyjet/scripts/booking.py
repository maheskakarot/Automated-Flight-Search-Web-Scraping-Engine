from easyjet.generator import uuid_generator
from datetime import datetime
import json
from easyjet.scripts.booking_scraping import Booking_scraping
import requests
from django.conf import settings
import logging
from datetime import datetime, timedelta
import json
from .decrypt import get_card_details
import requests
from utils.card_maksing import cardmapping



    
class BookingAutomation:
    def booking_automation(self,data):
        passenger_details = data.get('ListPassengers')
        flight_details = data.get('ListFlightSegments')
        total_fare = data.get('TotalFare')
        tolerance_amount = data.get('ToleranceAmount')
        air_trip_type = data.get('AirTripType')
        supplier_ref_no = data.get('SupplierRefNo')
        search_identifier = data.get('SearchIdentifier')
        card_details = data.get('CreditCardInfo')
        mys_card_config = data.get('MysCardConfig')
        book_ref = data.get('BookRef')
        base_currency = data.get('BaseCurrency')
        supplier_code = data.get('SupplierCode')
        account_id = data.get('AccountId')


        ListPassengers = []
        extraservices_amount = 0

        total_req_amount = total_fare+tolerance_amount
        print(total_req_amount,"<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>")

        for pass_details in passenger_details:
            if pass_details['ListExtraServices']:
                amount = pass_details['ListExtraServices'][0]['Amount']
                extraservices_amount += amount

        request_data = {
                "amount": total_fare+extraservices_amount,
                "bookingRef": f"{book_ref}",
                "clientId": "0",
                "currency": base_currency,
                "externalIdentifiers": {
                    "externalIdentifiers1": f"{book_ref}",
                    "externalIdentifiers2": passenger_details[0]['FirstName'],
                    "externalIdentifiers3": flight_details[0]['DepartureDateTime'],
                    "externalIdentifiers4": supplier_code,
                    "externalIdentifiers5":  flight_details[0]['DepartureAirport']+"-"+flight_details[0]['ArrivalAirport']
                },
                "firstName": passenger_details[0]['FirstName'],
                "lastName": passenger_details[0]['LastName'],
                "searchId": search_identifier,
                "virtualAccountId": account_id
            }
        
        
        card_details = get_card_details(mys_card_config,request_data, api="Book")

        message,booking_status,developer_message,pnr,error,email = Booking_scraping.booking_scraping(passenger_details,flight_details,search_identifier,total_req_amount,card_details)
        
        if message == "Proxy Error":
            print("Proxy Changed")
            settings.USE_PACKETSTREAM_PROXY = False
            message,booking_status,developer_message,pnr,error,email = Booking_scraping.booking_scraping(passenger_details,flight_details,search_identifier,total_req_amount,card_details)
            
        
        Expiry_date = card_details['result']['data']['expiryMonth']+card_details['result']['data']['expiryYear']
        print(Expiry_date)
        card_data=cardmapping(card_details['result']['data']['cardNo'],card_details['result']['data']['cvv'],Expiry_date)
        card_details['result']['data']['cardNo']=card_data['card']
        card_details['result']['data']['cvv']=card_data['cvv']
        card_details['result']['data']['expiryYear']=card_data['expiry'][:4]
        print(card_data['expiry'])
        card_details['result']['data']['expiryMonth']=card_data['expiry'][4:6]
        
        for passenger in passenger_details:
            passenger['TicketNumber'] = pnr
            ListPassengers.append(passenger)

        response_data = {}
        IsCashFlow = False
        #ListPassengers = passenger_details
        PNR = pnr
        ListFlightSegments = []
        is_return = False
        for flight_details in flight_details:
            
            details = {
            "AirlineCode": flight_details['AirlineCode'],
            "OPAirlineCode": flight_details['OPAirlineCode'],
            "FlightNumber": flight_details['FlightNumber'],
            "OPFlightNumber": flight_details['OPFlightNumber'],
            "DepartureAirport":flight_details['DepartureAirport'],
            "ArrivalAirport": flight_details['ArrivalAirport'],
            "DepartureDateTime": flight_details['DepartureDateTime'],
            "ArrivalDateTime": flight_details['ArrivalDateTime'],
            "BookingClass":flight_details['BookingClass'],
            "CabinClass": flight_details['CabinClass'],
            "IsReturn": is_return,
            "DepTerminal": flight_details['DepTerminal'],
            "ArrTerminal":flight_details['ArrTerminal'],
            "StopCount": flight_details['StopCount'],
            "AirlinePNR": PNR
            }
            is_return = True
            ListFlightSegments.append(details)

        optional_data = {}  
        response_data = {
            "IsCashFlow" : IsCashFlow,
            "SupplierRefNo": supplier_ref_no,
            "ListPassengers": ListPassengers,
            "PNR": PNR,
            "ListFlightSegments": ListFlightSegments,
            "BookStatus": booking_status,
            "Message": message,
            "OptionalData": optional_data
        }

        if len(pnr):
            data = self.store_booking_details(response_data,search_identifier,email)
        
        return response_data,message,developer_message,booking_status,error, request_data, card_details


    
    def store_booking_details(self,data,search_identifier,email):
        endpoint = 'https://ryanbooking.default-626251809c40d7000131dba0.mystifly.facets.cloud/api/addBookDetails'
        json_data = {
                "search_id":search_identifier,
                "created_by":email,
                "book_response":data,
                "meta_data":"",
                "status":1,
                "supplier_code":"U2S"
            }
        
        response =  requests.post(url=endpoint,
                                    json=json_data)

        return response.text 

# class BookingAutomation:

#     def __init__(self,data) :
#         self.data = data
#         self.passengers = self.data['ListPassengers']
#         self.total_fare = self.data["TotalFare"]
#         self.tolerance_amount = self.data["ToleranceAmount"]
#         self.account_id = self.data["AccountId"]
#         self.flight_details = self.data["ListFlightSegments"]
#         self.supplier_ref = self.data["SupplierRefNo"]
#         self.airtrip = self.data['AirTripType']


#     def generate_booking_request_response(self):

#         request_data = json.loads(self.supplier_ref) 
#         passenger_ids = request_data["ids_dict"]
#         cookie = request_data["cookie_flight_select"]
#         adults = []
#         child = []
#         infant = []
#         passenger_internal_ids = []
#         total_fare = self.data['TotalFare']+self.tolerance_amount
#         for code,list_passenger in passenger_ids.items():
#             if code == 1:
#                 adults.append(list_passenger)

#             if code == 2:
#                 child.append(list_passenger)

#             if code == 3:
#                 infant.append(list_passenger)

#             for values in list_passenger:
#                 passenger_internal_ids.append(values)

#         passenger_data = []
#         passenger_count = 0
#         self.extra_Service_amount = 0

#         for passenger in self.passengers:
            
#             birth_date = datetime.strptime(passenger['DateOfBirth'], '%Y-%m-%d')
#             depature_date = datetime.strptime(self.flight_details[0]["DepartureDateTime"].split(" ")[0],'%Y-%m-%d') 
#             age = depature_date.year - birth_date.year
#             if age >15:
#                 age_type = 0
                
#             elif age >2 and age < 16:
#                 age_type = 1
#             elif age <2:
#                 age_type = 2
#             if age >= 18:
#                 age=18
#             if passenger['Title'] == 'MSTR':
#                 passenger['Title'] = 'MR'

#             generate_passengers = {
#                     'InternalId': passenger_internal_ids[passenger_count],
#                     'Age': age,
#                     'FirstName': passenger['FirstName'].capitalize(),
#                     'LastName': passenger['LastName'].capitalize(),
#                     'Title': passenger['Title'].capitalize(),
#                     'EjPlusNumber': None,
#                     'SpecialServiceRequestCodes': [],
#                     'Type': age_type,
#                 }
#             passenger_data.append(generate_passengers)

#             extra_service = passenger["ListExtraServices"]
#             bags_json_payload = []
#             if extra_service:
              
#                 for bags in extra_service:
#                     self.extra_Service_amount += bags["Amount"]
#                     if bags["ServiceDetails"]=="15kg hold bag":
#                         bags_data = {
#                                 "ChargeCode": "LUS",
#                                 "Type": "SmallHoldBag",
#                                 "ExcessWeightSteps": 0
#                             }
#                     if bags["ServiceDetails"]=="23kg hold bag":
#                         bags_data = {
#                             "ChargeCode": "LUG",
#                             "Type": "StandardHoldBag",
#                             "ExcessWeightSteps": 0
#                         }
#                     if bags["ServiceDetails"]=="26kg hold bag":
#                         bags_data = {
#                         "ChargeCode": "WGT1",
#                         "Type": "StandardHoldBag",
#                         "ExcessWeightSteps": 1
#                     }

#                     product_id = uuid_generator()
#                     generate_payload = {
#                         "ChargeCode": bags_data["ChargeCode"],
#                         "IncludedInFare": False,
#                         "PassengerInternalId": passenger_internal_ids[passenger_count],
#                         "Benefits": [],
#                         'Price': bags["Amount"],
#                         "Data": {
#                             "ExcessWeightSteps": 0,
#                             "IsIncludedInFare": False,
#                             "PassengerInternalId": passenger_internal_ids[passenger_count],
#                             "Quantity": 1,
#                             "TotalPrice": bags["Amount"],
#                             "TotalPriceWithCreditCard": bags["Amount"],
#                             "TotalWeight": int(bags["ServiceDetails"][:2]),
#                             "Type": bags_data["Type"]
#                         },
#                     'ProductInternalId': product_id,
#                 }
#                     passenger_count+=1
#                     bags_json_payload.append(generate_payload)
#         data,booking_status,self.email,logs,card_details,card_data,card_request_data = Booking_scraping.booking_scraping(self,passenger_data,bags_json_payload,cookie,total_fare)

#         if booking_status == 1:
#             pnr = data
#         List_passenger_data= []
        
        
#         if booking_status == 2:

#             for passengers in self.passengers:
#                 passengers['TicketNumber'] = []
#                 List_passenger_data.append(passengers)
        
#             self.flight_details[0]["AirlinePNR"]=""

#             if self.data["AirTripType"]==2:
#                self.flight_details[1]["AirlinePNR"]=""

#             PNR =  ""

#             message = data
        
#         if booking_status == 1:
           
#            for passengers in self.passengers:
#                 passengers['TicketNumber'] = [data]
#                 List_passenger_data.append(passengers)

#            self.flight_details[0]["AirlinePNR"]=data

#            if self.data["AirTripType"]==2:
#                self.flight_details[1]["AirlinePNR"]=data
 


#         response = {
#             "IsCashFlow": False,
#             "SupplierRefNo": self.data['SupplierRefNo'],
#             "ListPassengers": List_passenger_data,
#             "PNR": PNR,
#             "ListFlightSegments": self.flight_details,
#             "BookStatus": booking_status,
#             "Message": message,
#             "OptionalData": {}
#         }
        
#         if booking_status == 1:
#             response["PNR"] = pnr
#             response["Message"] = "SUCCESS"
#             

        
#         if len(card_details):
#             card_details['result']['data']['cardNo']=card_data['card']
#             card_details['result']['data']['cvv']=card_data['cvv']
#             card_details['result']['data']['expiryYear']=card_data['expiry'][:4]
#             card_details['result']['data']['expiryMonth']=card_data['expiry'][4:6]
    
#         return response,card_details,card_request_data,logs,message
    


    
    
    
