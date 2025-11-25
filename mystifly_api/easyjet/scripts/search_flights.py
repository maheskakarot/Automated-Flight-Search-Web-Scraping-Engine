from .search_scraping import Scrape_flight_data
import json
from easyjet import static_data





class Search_flights:
    def __init__(self,data) :
        
        self.data = data
        self.OriginDestinationInformations = self.data['OriginDestinationInformations']
        self.PassengerTypeQuantities = self.data['PassengerTypeQuantities']
        self.SearchIdentifier = self.data['SearchIdentifier']
        self.airtrip = self.data['TravelPreferences']['AirTripType']

    def search_automation(self):
        self.origin = self.OriginDestinationInformations[0]['Source']
        self.destination = self.OriginDestinationInformations[0]['Destination']
        depature_date = self.OriginDestinationInformations[0]['DepartureDateTime']
        self.adult = self.PassengerTypeQuantities[0]['Quantity']
        self.child = 0
        self.infant = 0
        if len(self.PassengerTypeQuantities)>1:
            if self.PassengerTypeQuantities[1]['Code']==2:
                self.child = self.PassengerTypeQuantities[1]['Quantity']
            if self.PassengerTypeQuantities[1]['Code']==3:
                self.infant = self.PassengerTypeQuantities[1]['Quantity']
            if len(self.PassengerTypeQuantities)>2:
                self.infant = self.PassengerTypeQuantities[2]['Quantity']

        required_data = {
            "origin": self.origin,
            "destination":self.destination,
            "depature_date":depature_date.split("T")[0],
            "adult":self.adult,
            "child":self.child,
            "infant":self.infant,
            "air_trip":self.airtrip,
        }

        if self.airtrip == 2 :
            return_date = self.OriginDestinationInformations[1]['DepartureDateTime']
            required_data['return_date'] = return_date.split("T")[0]


        search_response,cookie,message,logs = Scrape_flight_data.search_scraping(required_data)
        
        if message:
            return message,logs

        Flight_search_result = self.search_flight_mapping(search_response,cookie)
        

        response = {
            "ListFlightSearchResult":Flight_search_result,
            "SearchIdentifier": self.SearchIdentifier,
            "Origin":self.origin,
            "Destination":self.destination,
            "TravelDate":depature_date.split("T")[0],
            "ReturnDate": None,
            "TravelType":self.airtrip,
            "ResultStatus":True,
            "BillingEntity":"SG",
            "SupplierCode":"U2S",
            "IsReissueType":False,
            "IsPrepay":False
        }

        if self.airtrip == 2:
            response["ReturnDate"]= return_date.split("T")[0]

        if Flight_search_result:
            return response,logs
        else:
            return message,logs

    def search_flight_mapping(self,data,cookie):

        flights_data= data['AvailableFlights']
        depature_flights  = []
        return_flights = []
        for flights in flights_data:

            
            flight_response = [{
                "AirlineCode": "U2",
                "OPAirlineCode":"U2",
                "FlightNumber": flights['FlightNumber'],
                "OPFlightNumber": flights['FlightNumber'],
                "DepartureAirport": flights['DepartureIata'],
                "ArrivalAirport": flights['ArrivalIata'],
                "DepartureDateTime":flights['LocalDepartureTime'],
                "ArrivalDateTime": flights['LocalArrivalTime'],
                "BookingClass": "Y",
                "CabinClass": "Y",
                "Duration": "",
                "IsReturn": False,
                "Equipment": "",
                "DepTerminal": "",
                "ArrTerminal": "",
                "StopCount": 0,
                "BookingClassText": "Standard"
                }]
            
            if flights['FlightFares'][0]['Prices']['Adult']['Price'] == 0:
                pass
            else:
                
                if self.adult:
                    adult_fare={"BaseFare": flights['FlightFares'][0]['Prices']['Adult']['Price']-flights['FlightTaxes']['TaxAmount'],"Tax": flights['FlightTaxes']['TaxAmount']}
                    flight_response.append(adult_fare)

                if self.child:
                    child_fare={
                        "childFare": flights['FlightFares'][0]['Prices']['Child']['Price'],
                        "Tax": 0
                        }
                    
                    flight_response.append(child_fare)

                if self.infant:
                    infant_fare={
                        "infantFare": flights['FlightFares'][0]['Prices']['Infant']['Price'],
                        "Tax": 0,
                        }
                    flight_response.append(infant_fare)

                flight_identification=flights['FlightFares'][0]['FlightIdentification']
                segment_id = flights['SegmentId']
                flight_required_data ={
                    "flight_identification":flight_identification,
                    "segment_id":segment_id,
                    "CarrierCode":flights['CarrierCode']

                }
                flight_response.append(flight_required_data)
                
               
                try:
                    airport = static_data.data.filter(airport_code=self.origin)
                    for codes in airport:
                        depature_code=codes.mapping_airport_code
                except Exception as e:
                    pass
                try:
                    dep_airport = static_data.data.filter(airport_code=self.destination)
                    for codes in dep_airport:
                        destination_code=codes.mapping_airport_code
                except Exception as e:
                    pass
                
                dep_airports_list = []   
                arr_airports_list = [] 
                try:
                    dep_airports_obj = static_data.data.filter(mapping_airport_code=depature_code)
                    for airports in dep_airports_obj:
                        dep_airports_list.append(airports.airport_code) 
                except:
                    pass
                try:
                    
                    arr_airports_obj = static_data.data.filter(mapping_airport_code=destination_code)
                    for airports in arr_airports_obj:
                        arr_airports_list.append(airports.airport_code)
                except:
                    pass

                
                if dep_airports_list :
                    for code in dep_airports_list:
                        if flights['DepartureIata']==code:
                            depature_flights.append(flight_response)
                elif flights['DepartureIata']==self.origin:
                    depature_flights.append(flight_response)

                if arr_airports_list:
                    for code in arr_airports_list:
                        if flights['DepartureIata']==code:
                            flight_response[0]['IsReturn']=True
                            return_flights.append(flight_response)
                    
                elif flights['DepartureIata']==self.destination:
                    flight_response[0]['IsReturn']=True
                    return_flights.append(flight_response)

        if self.airtrip == 1:

            flight_result = []

            for dep_flights in depature_flights:

                flight_response_data = [dep_flights[0]]

                search_key_data = {
                    "cookie":cookie,
                    "depature_Carrier_code":dep_flights[-1]["CarrierCode"],
                    "depature_flight_identification":dep_flights[-1]["flight_identification"],
                    "depature_segmentID":dep_flights[-1]['segment_id'],
                    "depature_adult_price":dep_flights[1]['BaseFare']+dep_flights[1]['Tax'],
                    "depature_adult_tax":dep_flights[1]['Tax'],
                    }

                fare_data = []
                adult_fare_data ={
                    "base_fare" : dep_flights[1]['BaseFare'],
                    'total_tax' : dep_flights[1]['Tax'],
                    "pax_id" : 1,
                    "pax_count" : self.adult,
                    }
                
                List_Flight_Fare = self.serach_fare_mapping(adult_fare_data)
                fare_data.append(List_Flight_Fare)
                if self.child :
                    
                    child_fare_data ={
                        "base_fare" : dep_flights[2]['childFare']-dep_flights[2]['Tax'],
                        "total_tax" : dep_flights[2]['Tax'],
                        "pax_id" : 2,
                        "pax_count" : self.child,
                        }
                    
                    search_key_data["depature_child_price"] = dep_flights[2]['childFare']+dep_flights[2]['Tax']
                    search_key_data["depature_child_tax"]=dep_flights[2]['Tax']
                    
                    List_Flight_Fare = self.serach_fare_mapping(child_fare_data)
                    fare_data.append(List_Flight_Fare)

                    if self.infant:
                        infant_fare_data ={
                            "base_fare" : dep_flights[3]['infantFare']-dep_flights[3]['Tax'],
                            "total_tax" : dep_flights[3]['Tax'],
                            "pax_id" : 3,
                            "pax_count" : self.infant,
                            }
                        search_key_data["depature_infant_price"] = dep_flights[3]['infantFare']+dep_flights[3]['Tax']
                        search_key_data["depature_infant_tax"]=dep_flights[3]['Tax']

                        List_Flight_Fare = self.serach_fare_mapping(infant_fare_data)
                        fare_data.append(List_Flight_Fare)
                else:
                    if self.infant:
                        
                        infant_fare_data ={
                            "base_fare" : dep_flights[2]['infantFare']-dep_flights[2]['Tax'],
                            "total_tax" : dep_flights[2]['Tax'],
                            "pax_id" : 1,
                            "pax_count" : self.infant,
                            }
                        
                        search_key_data["depature_infant_price"] = dep_flights[2]['infantFare']+dep_flights[2]['Tax']
                        search_key_data["depature_infant_tax"]=dep_flights[2]['Tax']
                        List_Flight_Fare = self.serach_fare_mapping(infant_fare_data)
                        fare_data.append(List_Flight_Fare)

                
                Flight_dict={
                        "SupplierCurrency":data["DisplayCurrencyCode"],
                        "ValidatingCarrier":"U2",
                        "ListFlightSegmentList":flight_response_data,
                        "ListFlightFare":fare_data,
                        "SearchKey":json.dumps(search_key_data),
                    }
                
                flight_result.append(Flight_dict)
            
                
            return flight_result


        if  self.airtrip == 2:

            Flight_result = []

            for dep_flights in depature_flights:

                for arr_flights in return_flights:

                    if dep_flights[0]["DepartureAirport"]==arr_flights[0]['ArrivalAirport'] and dep_flights[0]['ArrivalAirport'] == arr_flights[0]['DepartureAirport']:
                        flight_response_data = dep_flights[0],arr_flights[0]

                        fare_data = []

                        search_key_data = {
                        "cookie":cookie,
                        "depature_Carrier_code":dep_flights[-1]["CarrierCode"],
                        "arrival_carrier_code":arr_flights[-1]['CarrierCode'],
                        "depature_flight_identification":dep_flights[-1]["flight_identification"],
                        "arrival_flight_identification":arr_flights[-1]["flight_identification"],
                        "depature_segmentID":dep_flights[-1]['segment_id'],
                        "arrival_segmentID":arr_flights[-1]["segment_id"],
                        "depature_adult_price":dep_flights[1]['BaseFare']+dep_flights[1]['Tax'],
                        "arrival_adult_price":arr_flights[1]['BaseFare']+arr_flights[1]['Tax'],
                        "depature_adult_tax":dep_flights[1]['Tax'],
                        "arrival_adult_tax":arr_flights[1]['Tax']
                        }
                
                        adult_fare_data ={
                            "base_fare" : dep_flights[1]['BaseFare']+arr_flights[1]['BaseFare'],
                            'total_tax' : dep_flights[1]['Tax']+arr_flights[1]['Tax'],
                            "pax_id" : 1,
                            "pax_count" : self.adult,
                            }
                        

                        
                        List_Flight_Fare = self.serach_fare_mapping(adult_fare_data)
                        fare_data.append(List_Flight_Fare)
                        if self.child :
                            
                            child_fare_data ={
                                "base_fare" : dep_flights[2]['childFare']+arr_flights[2]['childFare'],
                                "total_tax" : dep_flights[2]['Tax']+arr_flights[2]['Tax'],
                                "pax_id" : 2,
                                "pax_count" : self.child,
                                }
                            search_key_data["depature_child_price"] = dep_flights[2]['childFare']+dep_flights[2]['Tax']
                            search_key_data["arrival_child_price"] = arr_flights[2]['childFare']+arr_flights[2]['Tax']
                            search_key_data["depature_child_tax"]=dep_flights[2]['Tax']
                            search_key_data["arrival_child_tax"]=arr_flights[2]["Tax"]
                            
                            List_Flight_Fare = self.serach_fare_mapping(child_fare_data)
                            fare_data.append(List_Flight_Fare)

                            if self.infant:
                                infant_fare_data ={
                                    "base_fare" : dep_flights[3]['infantFare']+arr_flights[3]['infantFare'],
                                    "total_tax" : dep_flights[3]['Tax']+arr_flights[3]['Tax'],
                                    "pax_id" : 3,
                                    "pax_count" : self.infant,
                                    }
                                search_key_data["depature_infant_price"] = dep_flights[3]['infantFare']+dep_flights[3]['Tax']
                                search_key_data["arrival_child_price"] = dep_flights[3]['infantFare']+dep_flights[3]['Tax']
                                search_key_data["depature_infant_tax"]=dep_flights[3]['Tax']
                                search_key_data["arrival_infant_tax"]=arr_flights[3]["Tax"]
                                List_Flight_Fare = self.serach_fare_mapping(infant_fare_data)
                                fare_data.append(List_Flight_Fare)
                        else:
                            if self.infant:
                                
                                infant_fare_data ={
                                    "base_fare" : dep_flights[2]['infantFare']+arr_flights[2]['infantFare'],
                                    "total_tax" : dep_flights[2]['Tax']+arr_flights[2]['Tax'],
                                    "pax_id" : 3,
                                    "pax_count" : self.infant,
                                    }
                                search_key_data["depature_infant_price"] = dep_flights[2]['infantFare']+dep_flights[2]['Tax']
                                search_key_data["arrival_child_price"] = dep_flights[2]['infantFare']+dep_flights[2]['Tax']
                                search_key_data["depature_infant_tax"]=dep_flights[2]['Tax']
                                search_key_data["arrival_infant_tax"]=arr_flights[2]["Tax"]
                                List_Flight_Fare = self.serach_fare_mapping(infant_fare_data)
                                fare_data.append(List_Flight_Fare)

                        
                        Flight_dict={
                                "SupplierCurrency":data["DisplayCurrencyCode"],
                                "ValidatingCarrier":"U2",
                                "ListFlightSegmentList":flight_response_data,
                                "ListFlightFare":fare_data,
                                "SearchKey":json.dumps(search_key_data),
                            }
                        
                        

                        Flight_result.append(Flight_dict)
              
                    
            return Flight_result


    def serach_fare_mapping(self,fare_data):

        if self.airtrip == 1: 
            bags = [
            f"{self.origin}#{self.destination}#0kg",
          ]
        if self.airtrip == 2:
            bags=[
            f"{self.origin}#{self.destination}#0kg",
            f"{self.destination}#{self.origin}#0kg"
          ]
        List_Flight_Fare =  {
          "BaseFare": round(fare_data["base_fare"],2),
          "Tax": fare_data['total_tax'],
          "PaxTypeId": fare_data["pax_id"],
          "PaxCount": fare_data["pax_count"],
          "FareType": 4,
          "ListAirTax": [
            {
              "TaxAmount": fare_data['total_tax'],
              "TaxCode": "Tax 1"
            }
          ],
          "Baggage": bags,
          "Fee": 0
        }

        
        return List_Flight_Fare
      

        
        
        
        