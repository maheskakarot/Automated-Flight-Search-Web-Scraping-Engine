import uuid
import requests
from easyjet.config import headers
import json
from .decrypt import MystiflyEncryption, get_card_details
from datetime import datetime
from django.conf import settings
from utils.proxy import get_proxy
from utils.Azure_blob_manager import API_data,AzureBlob

def cal_duration(arrival_timing, departure_timing ):
    # First timing
    t1 = datetime.strptime(departure_timing, '%Y-%m-%d %H:%M:%S')
    # Second timing
    t2 = datetime.strptime(arrival_timing, '%Y-%m-%d %H:%M:%S')
    # Calculate duration
    t = t2 - t1
    duration_str = f"{t.seconds // 3600:02d}:{(t.seconds // 60) % 60:02d}"
    return duration_str

class RepriceValidationAutomation:
    def __init__(self, request_data):
        self.data = request_data
        self.base_currency_type = self.data.get('ListFlightSearchResult', [])[0].get('SupplierCurrency', 'GBP')
        self.travel_type = self.data.get('TravelType', '1')
        self.arrival_loc = self.data.get('ListFlightSearchResult', [])[0].get('ListFlightSegmentList', '')[0].get('ArrivalAirport', '')
        self.dep_flight_number = self.data.get('ListFlightSearchResult', [])[0].get('ListFlightSegmentList', '')[0].get('FlightNumber')
        self.extra_data = self.data.get('ListFlightSearchResult', [])[0].get('SearchKey', {})
        self.extra_json_data = json.loads(self.extra_data)
        self.dep_carriercode = self.extra_json_data.get('depature_Carrier_code', '')
        self.cookies_dict = self.extra_json_data.get('cookie', '')
        self.departure_loc = self.data.get('ListFlightSearchResult', [])[0].get('ListFlightSegmentList', '')[0].get('DepartureAirport', '')
        self.depature_time = self.data.get('ListFlightSearchResult', [])[0].get('ListFlightSegmentList', [])[0].get('DepartureDateTime', '').replace('T', ' ')
        self.arrival_time = self.data.get('ListFlightSearchResult', [])[0].get('ListFlightSegmentList', [])[0].get('ArrivalDateTime', '').replace('T', ' ')
        self.baggage = []
        self.one_way_bag = self.departure_loc+'#'+self.arrival_loc+"#0kg"
        self.baggage.append(self.one_way_bag)
        self.departure_segment_id = self.extra_json_data.get('depature_segmentID', '') 
        self.depature_flightiden = self.extra_json_data.get('depature_flight_identification', '')
        self.departue_adult_price = self.extra_json_data.get('depature_adult_price', '')
        if self.departue_adult_price:
            self.dep_adult_price_dict = self.pass_price_details(self.departue_adult_price)
        else:
            self.dep_adult_price_dict = None
        self.departue_child_price = self.extra_json_data.get('depature_child_price', '')
        if self.departue_child_price:
            self.dep_child_price_dict = self.pass_price_details(self.departue_child_price)
        else:
            self.dep_child_price_dict = None
        self.departue_infant_price = self.extra_json_data.get('depature_infant_price', '')
        if self.departue_infant_price:
            self.dep_infant_price_dict = self.pass_price_details(self.departue_infant_price)
        else:
            self.dep_infant_price_dict = None
        self.departure_tax_price = self.extra_json_data.get('depature_adult_tax', '')
        self.dep_internal_id = self.generate_uuid(1)
        self.outbound_slot = self.trip_details(self.dep_internal_id, self.arrival_loc, 
                self.dep_carriercode, self.departure_loc, self.dep_flight_number, self.depature_time, 
                self.arrival_time, self.departure_segment_id, self.departue_adult_price, self.depature_flightiden, 
                self.departure_tax_price, self.dep_adult_price_dict, self.dep_child_price_dict, self.dep_infant_price_dict)
        self.bags_api_url = 'https://www.easyjet.com/ejrebooking/api/v71/funnel/getbasketflightscharges?IncludeSeatCharges=false'
        if self.travel_type == 2:
            self_return_bag = self.arrival_loc+'#'+self.departure_loc+"#0kg"
            self.baggage.append(self_return_bag)
            self.arr_carriercode = self.extra_json_data.get('arrival_carrier_code', '')
            self.arr_flight_number = self.data.get('ListFlightSearchResult', [])[0].get('ListFlightSegmentList', '')[1].get('FlightNumber')
            self.arr_departure_time = self.data.get('ListFlightSearchResult', [])[0].get('ListFlightSegmentList', [])[1].get('DepartureDateTime', '').replace('T', ' ')
            self.arr_arrival_time = self.data.get('ListFlightSearchResult', [])[0].get('ListFlightSegmentList', [])[1].get('ArrivalDateTime', '').replace('T', ' ')
            self.return_date = self.arr_arrival_time.split(' ')[0]
            self.arr_segment_id = self.extra_json_data.get('arrival_segmentID', '')
            self.arr_adult_price = self.extra_json_data.get('arrival_adult_price', '')
            if self.arr_adult_price:
                self.arr_adult_price_dict = self.pass_price_details(self.arr_adult_price)
            else:
                self.arr_adult_price_dict = None
            self.arr_child_price = self.extra_json_data.get('arrival_child_price', '')
            if self.arr_child_price:
                self.arr_child_price_dict = self.pass_price_details(self.arr_child_price)
            else:
                self.arr_child_price_dict = None
            self.arr_infant_price = self.extra_json_data.get('arrival_infant_price', '')
            if self.arr_infant_price:
                self.arr_infant_price_dict = self.pass_price_details(self.arr_infant_price)
            else:
                self.arr_infant_price_dict = None
            self.arr_adult_tax = self.extra_json_data.get('arrival_adult_tax', '')
            self.arr_flightiden = self.extra_json_data.get('arrival_flight_identification', '')
            self.arr_internal_id = self.generate_uuid(1)
            self.return_slot = self.trip_details(self.arr_internal_id, self.departure_loc, 
                self.arr_carriercode, self.arrival_loc, self.arr_flight_number, self.arr_departure_time, 
                self.arr_arrival_time, self.arr_segment_id, self.arr_adult_price, self.arr_flightiden, 
                self.arr_adult_tax, self.arr_adult_price_dict, self.arr_child_price_dict, self.arr_infant_price_dict)
        else:
            self.return_slot = None
            self.return_date = None
        self.revalidation_api_url = 'https://www.easyjet.com/ejrebooking/api/v71/funnel/setbasketflights'
        self.my_scard_config = self.data.get('MysCardConfig')

    def pass_price_details(self, fare_details):
        price_dict_details = {
            "PriceWithCreditCard": fare_details,
            "PriceWithDebitCard": fare_details,
            "Price": fare_details
            }
        return price_dict_details

    def trip_details(self, arr_internal_id, departure_loc, 
                arr_carriercode, arrival_loc, arr_flight_number, arr_departure_time, 
                arr_arrival_time, arr_segment_id, arr_adult_price,arr_flightiden, 
                arr_adult_tax, arr_adult_price_dict, arr_child_price_dict, arr_infant_price_dict):
        trip_details_dict = {
                "Flight": {
                    "InternalId": ''.join(arr_internal_id),
                    "ArrivalIata": departure_loc,
                    "CarrierCode": arr_carriercode,
                    "DepartureIata": arrival_loc,
                    "FlightNumber": arr_flight_number,
                    "LocalDepartureTime": arr_departure_time,
                    "LocalArrivalTime": arr_arrival_time,
                    "SegmentId": arr_segment_id,
                    "FlightFares": [
                        {
                            "FareType": "Standard",
                            "Prices": {
                                "Adult": arr_adult_price_dict,
                                "Child": arr_child_price_dict,
                                "Infant": arr_infant_price_dict
                            },
                            "FlightIdentification": arr_flightiden 
                        }
                    ],
                    "DisruptionCode": None,
                    "BasePrice": arr_adult_price,
                    "FlightTaxes": {
                        "TaxAmount": arr_adult_tax,
                        "ApplyApdRules": False
                    }
                }
            }
        return trip_details_dict
    
    def revalidation_automation(self):
        ids_dict = self.ids_generation_fare_details()
        result = self.trip_revalidation(self.base_currency_type, ids_dict, self.outbound_slot, self.return_slot)
        return result

    def trip_revalidation(self, base_currency_type, ids_dict, outbound_slot, return_slot):
        json_data = {
        "BasketInitialization": {
        "LanguageCode": "EN",
        "CurrencyCode": base_currency_type,
        "WebsiteRegionCode": "en",
        "AdultIds": ids_dict[1],
        "ChildIds": ids_dict[2],
        "InfantIds": ids_dict[3]
    },
    "JourneyPairs": [
        {
            "Id": 1,
            "IsPrimaryPair": True,
            "BaseCurrency": base_currency_type,
            "OutboundSlot": outbound_slot,
            "ReturnSlot": return_slot,
        }
    ],
    "FareType": "Standard",
    }   
        proxy = get_proxy()
        # proxies = {
        # "http"  : "http://" + proxy[0],
        # }
        for ip in proxy:
            proxies = {
                "http"  : "http://" + ip,
            }
            request_res = requests.post(self.revalidation_api_url, headers=headers, cookies = self.cookies_dict, json=json_data,proxies=proxies)
            if request_res.status_code == 200:
                break        

        logs = {
            "revalidation_api":{
                "url":self.revalidation_api_url,
                "body":json_data,
                "stauts":request_res.status_code,
                "text":request_res.text
            }
        }

        if request_res.status_code == 200:
            if return_slot == None:
                arrival_internal_ids = ''
            else:
                arrival_internal_ids = return_slot.get('Flight', {}).get('InternalId', '')
            coo_dict = {}
            coo_body  = request_res.cookies
            for co_bo in coo_body:
                coo_dict[co_bo.name] = co_bo.value
            extra_values = {'ids_dict':ids_dict, 'cookie_flight_select':coo_dict, 'departure_internal_id':outbound_slot.get('Flight', {}).get('InternalId', ''),
                'arrival_internal_id': arrival_internal_ids}
            extra_services = []
            if self.travel_type == 1:
                luggage_dict = {}
                lugg_cook = {}
                bags_res = requests.get(self.bags_api_url, cookies = coo_dict,proxies=proxies)

                logs["bag_api"] = {
                        "url":self.bags_api_url,
                        "stauts":bags_res.status_code,
                        "text":bags_res.text
                    }
            
                lugg_cookie_body = bags_res.cookies
                for lu_co_body in lugg_cookie_body:
                    lugg_cook[lu_co_body.name] = lu_co_body.value
                extra_values.update({'cookie_bags':lugg_cook})
                try:
                    bags_info = json.loads(bags_res.text)
                    for bag_det in bags_info:
                        bag_det.pop('SegmentId')
                        bag_keys = bag_det.keys()
                        for bag_key in bag_keys:
                            bag_type = bag_det.get(bag_key, {}).get('ChargeCode', '')
                            bag_price = bag_det.get(bag_key, {}).get('Amount', '')
                            luggage_dict.update({bag_type:bag_price})
                    kg_15_hold = luggage_dict.get('SmallHoldLuggage', '')
                    if kg_15_hold:
                        kg_15_hold_dict = self.bag_details('15kg hold bag', kg_15_hold)
                        extra_services.append(kg_15_hold_dict)
                    kg_23_hold = luggage_dict.get('HoldLuggage', '')
                    if kg_23_hold:
                        kg_23_hold_dict = self.bag_details('23kg hold bag', kg_23_hold)
                        extra_services.append(kg_23_hold_dict)
                    extra_hold = luggage_dict.get('HoldLuggageExcessWeight', '')
                    kg_26_hold = kg_23_hold + extra_hold
                    if kg_26_hold:
                        kg_26_hold_dict = self.bag_details('26kg hold bag', round(kg_26_hold, 2))
                        extra_services.append(kg_26_hold_dict)
                except:
                    bags_info = {}
            revalidation_key_values = json.dumps(extra_values)
            
            fare_details_input = []
            fare_data_input = self.data.get('ListFlightSearchResult')[0].get('ListFlightFare')
            for fare_det in fare_data_input:
                fare_details_data = {
                    "BaseFare": fare_det.get('BaseFare', ''),
                    "Tax": fare_det.get('Tax'),
                    "PaxTypeId": fare_det.get('PaxTypeId'),
                    "PaxCount": fare_det.get('PaxCount'),
                    "FareType": fare_det.get('FareType') ,
                    "ListAirTax": fare_det.get('ListAirTax'),
                    "Baggage": self.baggage,
                    "Fee": 0
                }
                fare_details_input.append(fare_details_data)
            data = {
                "SupplierCurrency": self.base_currency_type,
                "ValidatingCarrier": self.data.get('ListFlightSearchResult')[0].get('ValidatingCarrier'),
                "ListFlightSegmentList": self.data.get('ListFlightSearchResult')[0].get('ListFlightSegmentList'),
                "ListFlightFare": fare_details_input, 
                "RevalidationKey": revalidation_key_values,
                "ListExtraServices" : extra_services,
                "ListFareRule": []
            }
            card_request_data = {
                                "airlineCode": "U2",
                                "billingEntity": self.data.get('BillingEntity'),
                                "currencyCode": self.base_currency_type,
                                "destination": self.data.get('Destination'),
                                "origin": self.data.get('Origin'),
                                "supplierCode": "U2S"
                            }
            azure_obj = AzureBlob()
            card_req_api = API_data(str(card_request_data),'cardsearch','U2S','request')
            azure_data = [card_req_api]
            flight_data = {}
            try:
                card_response_data = get_card_details(self.my_scard_config, card_request_data, api="Search")
                card_res = API_data(str(card_response_data),'cardsearch','U2S','response')
                azure_data.append(card_res)
                azure_obj.upload_data_to_blob_storage(self.data['MysAzureConfig'], self.data['SearchIdentifier'], azure_data)
            except Exception as e:
                card_response_data = e
                card_res = API_data(str(e),'cardsearch','U2S','response')
                azure_data.append(card_res)
                azure_obj.upload_data_to_blob_storage(self.data['MysAzureConfig'], self.data['SearchIdentifier'], azure_data)
                message = "Failed in Card Services"
                response = {
                "message":message
            }
                return response,card_request_data,card_response_data,logs
            
            flight_data['ListFlightSearchResult'] = [data]
            flight_data['SearchIdentifier'] = self.data.get('SearchIdentifier')
            flight_data['Origin'] = self.departure_loc
            flight_data['Destination'] = self.arrival_loc
            flight_data['TravelDate'] = self.depature_time.split(' ')[0]
            flight_data['ReturnDate'] = self.return_date
            flight_data['TravelType'] = self.data.get('TravelType')
            flight_data['ResultStatus'] = True
            flight_data['BillingEntity'] = self.data.get('BillingEntity') 
            flight_data['SupplierCode'] = self.data.get('SupplierCode')
            flight_data['AccountId'] = card_response_data['result']['data']['cardList'][0]['accountId']
            flight_data['CardType'] = card_response_data['result']['data']['cardList'][0]['cardType']
            flight_data['IsReissueType'] = False
            flight_data['IsPrepay'] = False
            
            return flight_data,card_request_data,card_response_data,logs
        
        else:
            message = "Failed to scrape data from website"

            response = {
                "message":message
            }
            return response,card_request_data,card_response_data,logs

    def ids_generation_fare_details(self):
        ids_dict = {1:[], 2:[], 3:[]}
        pass_count_list = self.data.get('ListFlightSearchResult', [])
        for pass_count in pass_count_list:
            pass_count_num = pass_count.get('ListFlightFare', []) 
            for each_pass_count in pass_count_num:
                count_pass = each_pass_count.get('PaxCount', '')
                pass_type = each_pass_count.get('PaxTypeId', '')
                ids_list = self.generate_uuid(count_pass)
                ids_dict.update({pass_type: ids_list})
        return ids_dict

    def generate_uuid(self, total_ids_generate):
        ids_list = []
        for id_generate in range(0, total_ids_generate):
            generated_uuid = uuid.uuid4()
            uuid_str = str(generated_uuid)
            ids_list.append(uuid_str)
        return ids_list
    
    def price_info(self, base_fare):
        base_fare_dict = {
            'PriceWithCreditCard': base_fare,
            'PriceWithDebitCard': base_fare,
            'Price': base_fare,
            }
        return base_fare_dict
    
    def bag_details(self, weight, price_amount):
        bag_details = {
            "Type": 1,
            "ServiceDetails":weight,
            "Amount":price_amount,
            "ExtraServiceKey":"",
            "IsInBound": False
        }
        return bag_details