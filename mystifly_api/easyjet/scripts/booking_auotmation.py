import json
from utils.card_maksing import cardmapping
from utils.decrypt import get_card_details
import requests
from utils.Azure_blob_manager import API_data,AzureBlob


class BookingAutomation:
    
    def __init__(self,data):
        self.data = data    
       
    def generate_booking_response(self,message,pnr,pnr_data=None,email=None):
        response = {
        "IsCashFlow": False,
        "SupplierRefNo": self.data['SupplierRefNo'],
        "ListPassengers": self.data['ListPassengers'],
        "PNR": "",
        "ListFlightSegments": "",
        "BookStatus": 1,
        "OptionalData": {}
        }
        flight_response = []
        for flights in self.data['ListFlightSegments']:
                flight_response_map = {
                    "AirlineCode": "U2",
                    "OPAirlineCode": "U2",
                    "FlightNumber": flights['FlightNumber'],
                    "DepartureAirport": flights['DepartureAirport'],
                    "ArrivalAirport": flights['ArrivalAirport'],
                    "DepartureDateTime": flights['DepartureDateTime'],
                    "ArrivalDateTime": flights['ArrivalDateTime'],
                    "BookingClass": flights['BookingClass'],
                    "CabinClass": flights['CabinClass'],
                    "Duration": flights['Duration'],
                    "IsReturn": flights['IsReturn'],
                    "DepTerminal": flights['DepTerminal'],
                    "ArrTerminal": flights['ArrTerminal'],
                    "StopCount": flights['StopCount'],
                    "StopOverSegments": flights['StopOverSegments'],
                    "GroupId": flights['GroupId'],
                    "AirlinePNR": "",
                    "BookingClassText": flights['BookingClassText'],
                    "DepartureTimeZone": flights['DepartureTimeZone']
                    }
                flight_response.append(flight_response_map)
                
        if message:
            message_response = {"Message":message,"BookStatus":2}
            response['ListFlightSegments']=flight_response
            response['BookStatus'] = 2
            response['Message']= message
            return message_response,response
        
        if pnr:
            response['PNR']= pnr
            optional_data = response['OptionalData']
            optional_data['pnr_data'] = pnr_data 
            for data in flight_response:
                data['AirlinePNR'] = pnr
            response["ListFlightSegments"] = flight_response
            response["Message"] = "SUCESSFUL"
            BookingAutomation.store_booking_details(self,response,self.data['SearchIdentifier'],email)
            return "",response
        
    def get_flight_select_data(self):  
        
        flight_data = self.data["ListFlightSegments"]
        depature_data = flight_data[0]["DepartureDateTime"]
        arrival_data = flight_data[0]["ArrivalDateTime"]
        depature_flight = flight_data[0]["DepartureAirport"]
        arrival_flight = flight_data[0]["ArrivalAirport"]
        depature_date = depature_data.split(" ")[0]
        arrival_date = arrival_data.split(" ")[0]
        depature_time =  depature_data.split(" ")[1]
        arrival_time = arrival_data.split(" ")[1]
        
        flight_search_data = {
            "depature_flight":depature_flight,
            "arrival_flight":arrival_flight,
            "depature_date":depature_date,
            "arrival_date":arrival_date,  
            "depature_time":depature_time,
            "arrival_time":arrival_time         
        }
        
        if self.data["AirTripType"]== 2:
            return_depature_data = flight_data[1]["DepartureDateTime"]
            return_arrival_data = flight_data[1]["ArrivalDateTime"]
            return_deptature_date = return_depature_data.split(" ")[0]
            return_arrival_date =  return_arrival_data.split(" ")[0]
            return_arrival_time = return_arrival_data.split(" ")[1]
            return_depature_time = return_depature_data.split(" ")[1]        
            flight_search_data["return_deptature_date"]=return_deptature_date
            flight_search_data["return_arrival_date"]=return_arrival_date
            flight_search_data["return_arrival_time"]=return_arrival_time
            flight_search_data["return_depature_time"]=return_depature_time
            
        
        return flight_search_data
        
    def get_passenger_details(self):
        
        supplier_ref = json.loads(self.data["SupplierRefNo"])
        adult = len(supplier_ref["ids_dict"]["1"])
        child = len(supplier_ref["ids_dict"]["2"])
        infant = len(supplier_ref["ids_dict"]["3"])       
        passengers = {
            "adult":adult,
            "child":child,
            "infant":infant
        }
        
        passenger_details = self.data['ListPassengers']
        return passengers,passenger_details

    def get_required_details(self):
        
        total_amount = self.data["TotalFare"]
        tolerance_amount = self.data["ToleranceAmount"]
        card_config = self.data["MysCardConfig"]
        search_id = self.data["SearchIdentifier"]

        return {
            "total_amount": total_amount,
            "tolerance_amount": tolerance_amount,
            "search_id": search_id,
            "card_config": card_config,
        }

    def card_data_mapping(self,amount):
        card_details = ""
        azure_obj = AzureBlob()
        request_data = {
                "amount":amount,
                "bookingRef": str(self.data["BookRef"]),
                "clientId": "0",
                "currency": self.data["BaseCurrency"],
                "externalIdentifiers": {
                    "externalIdentifiers1": str(self.data["BookRef"]),
                    "externalIdentifiers2": self.data['ListPassengers'][0]['FirstName'],
                    "externalIdentifiers3": self.data['ListFlightSegments'][0]['DepartureDateTime'],
                    "externalIdentifiers4": self.data["ListFlightSegments"][0]["AirlineCode"],
                    "externalIdentifiers5":  self.data['ListFlightSegments'][0]['DepartureAirport']+"-"+self.data['ListFlightSegments'][0]['ArrivalAirport']
                },
                "firstName": self.data['ListPassengers'][0]['FirstName'],
                "lastName": self.data['ListPassengers'][0]['LastName'],
                "searchId": self.data["SearchIdentifier"],
                "virtualAccountId": self.data['AccountId']
            }
        req_api = API_data(str(request_data),'cardbook','U2S','request')
        azure_data = [req_api]
        message = ""
        try:
            card_details = get_card_details(self.data["MysCardConfig"],request_data, api="Book")
            res_api = API_data(str(card_details),'cardbook','U2S','response')
            azure_data.append(res_api)
            azure_obj.upload_data_to_blob_storage(self.data['MysAzureConfig'], self.data['SearchIdentifier'], azure_data)
        except Exception as e:
            res_api = API_data(str(e),'cardbook','U2S','response')
            azure_data.append(res_api)
            azure_obj.upload_data_to_blob_storage(self.data['MysAzureConfig'], self.data['SearchIdentifier'], azure_data)
            return card_details,e

        # Expiry_date = card_details['result']['data']['expiryMonth']+card_details['result']['data']['expiryYear']

        # card_data=cardmapping(card_details['result']['data']['cardNo'],card_details['result']['data']['cvv'],Expiry_date)
        return card_details,message
    
    
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
        # print(json_data)
        response =  requests.post(url=endpoint,
                                    json=json_data)

        
        
        
        
    