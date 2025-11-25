from rest_framework import generics, status
from account.authentication import ExpiringTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from utils.restful_response import send_response
from v1.ryanair.models import Airport
from v1.ryanair.serializers import AirportSerializer, FlightSearchSerializer
from v2.ryanair.scripts.ryan_air import RyanairWebsiteAutomation
from v2.ryanair.serializers.flights import FlightSearchUpdatedSerializer
from v1.ryanair.helpers.webdriver import reuse_webdriver, close_webdriver
from account.models import SubscriberSearchHistory
from utils.error_logging import send_error_mail
from utils.load_balancer import is_max_cpu_load
import requests
import json
import datetime

class AirportSearchView(generics.ListAPIView):
    serializer_class = AirportSerializer
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Airport.objects.all()
        country_name = self.request.GET.get('country_name', '')
        airport_name = self.request.GET.get('airport_name', '')
        airport_code = self.request.GET.get('airport_code', '')
        queryset = queryset.filter(
            country__name__icontains=country_name,
            name__icontains=airport_name,
            code__icontains=airport_code)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return send_response(
            status=status.HTTP_200_OK,
            data=serializer.data,
            developer_message="Request was successful."
        )


class SearchFlightView(generics.CreateAPIView):
    serializer_class = FlightSearchSerializer
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        cpu_load, is_max_load = is_max_cpu_load()
        if is_max_load:
            data = {'cpu_load': cpu_load}
            return send_response(
                status=status.HTTP_400_BAD_REQUEST,
                data=data,
                developer_message="Request failed due to maximum cpu load.",
                ui_message="Request failed due to maximum cpu load."
            )

        subscriber = request.user.subscriber
        serializer = self.get_serializer(data=request.data)

        # TODO: Add user specific driver info
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)
        last_history_obj = SubscriberSearchHistory.objects.filter(subscriber=subscriber).last()

        if serializer.is_valid():
            search_url, message, required_data = serializer.get_required_data()

            if not search_url:
                return send_response(
                    status=status.HTTP_400_BAD_REQUEST,
                    developer_message=message,
                    ui_message=message,
                )

            SubscriberSearchHistory.objects.create(
                subscriber=subscriber,
                url=search_url,
                adult=required_data.get('adults'),
                teen=required_data.get('teens'),
                child=required_data.get('children'),
                infant=required_data.get('infants'),
            )

            booking_request = {
                'is_driver_reused': is_driver_reused,
                'last_history_obj': last_history_obj,
                'isReturn': required_data.get('isReturn'),
                'adults': required_data.get('adults'),
                'children': required_data.get('children'),
                'infants': required_data.get('infants'),
                'page': request.data.get('page', 1),
                'pageSize': request.data.get('pageSize', 10),
                'isPaginated': request.data.get('isPaginated', False),
                'OriginNearByAirports': request.data.get('OriginNearByAirports', False),
                'DestinationNearByAirports': request.data.get('DestinationNearByAirports', False)
            }

            try:
                flights_data, message = RyanairWebsiteAutomation(
                    driver, booking_request
                ).search_flights(search_url)

                flights_data['cpu_load'] = cpu_load

            except Exception as ex:
                screen_name = "Search"
                error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)

                return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                     developer_message="Request was failed",
                                     ui_message="Request was failed"
                                     )

            if len(flights_data):
                return send_response(
                    status=status.HTTP_200_OK,
                    data=flights_data,
                    ui_message=message,
                    developer_message=message
                )

            return send_response(
                status=status.HTTP_200_OK,
                data=flights_data,
                ui_message=message,
                developer_message=message
            )

        return send_response(
            status=status.HTTP_400_BAD_REQUEST,
            error=serializer.errors,
            ui_message="Request failed",
            developer_message="Request failed"
        )

class SearchFlightUpdatedView(generics.GenericAPIView):
    serializer_class = FlightSearchUpdatedSerializer

    def post(self,request):
        data = request.data
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        flight = serializer.data
        responseData = {}
        inDate = request.POST.get('date_in')
        outDate = request.POST.get('date_out')
        origin = request.POST.get('origin')
        destination = request.POST.get('destination')
        inFlight = [];
        outFlight = [];

        
        if flight is not None:
            date_in = "" if flight['date_in'] is None else flight['date_in']
            promocode = "" if flight['promocode'] is None else flight['promocode']

            try:
                response = requests.get(
                    f"""https://www.ryanair.com/api/booking/v4/en-gb/availability?ADT={flight['adult']}&CHD={flight['child']}&DateIn={date_in}&DateOut={flight['date_out']}&Destination={flight['destination']}&Disc={flight['disc']}&INF={flight['infant']}&Origin={flight['origin']}&TEEN={flight['teen']}&promoCode={promocode}&IncludeConnectingFlights={str(flight['include_connecting_flights']).lower()}&FlexDaysBeforeOut={flight['flex_days_before_out']}&FlexDaysOut={flight['flex_days_out']}&FlexDaysBeforeIn={flight['flex_days_before_in']}&FlexDaysIn={flight['flex_days_in']}&RoundTrip={str(flight['round_trip']).lower()}&ToUs={flight['to_us']}""")
                
                # print(response.json())
                if response.status_code == 200:
                    data=response.json(),
                    # data = json.loads(data[0])
                    # print((data[0]['trips']))
                    for trips in data[0]['trips']:
                        for dates in trips['dates']:
                            flightDate = datetime.datetime.strptime(dates['dateOut'], "%Y-%m-%dT%H:%M:%S.%f").strftime('%Y-%m-%d')
                            # print(dates)
                            if flightDate == inDate or flightDate == outDate:
                                
                                for flight in dates['flights']:
                                    # print(flight)
                                    if trips['origin'] == origin:
                                        inFlight = flight
                                    elif trips['origin'] == destination:
                                        outFlight = flight

                    # print("In Flight \n")
                    # print(inFlight)
                    # print("out flight \n")
                    # print(outFlight)
                                        
                    responseData['termsOfUse'] = data[0]['termsOfUse']
                    responseData["total_pages"] = 1
                    responseData["count"] = 2
                    responseData["page_size"] = 1
                    responseData["next_page"] = ''
                    responseData["prev_page"] = ''
                    result = {};

#                   "departure_flight_data": {
#                     "flight_number": "RK 3846",
#                     "flight_type": "Direct",
#                     "origin_airport_name": "London Stansted",
#                     "destination_airport_name": "Bucharest",
#                     "departure_time": "06:40",
#                     "arrival_time": "11:40",
#                     "duration": "Duration 3h"
#                   },

                    result['departure_flight_data'] = { 
                        "flight_number": inFlight['flightNumber'],
                        "flight_type": "Direct",
                        "origin_airport_name": data[0]['trips'][0]['originName'],
                        "destination_airport_name": data[0]['trips'][0]['destinationName'],
                        "departure_time": datetime.datetime.strptime(inFlight['segments'][0]['time'][0], "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                        "arrival_time": datetime.datetime.strptime(inFlight['segments'][0]['time'][1], "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                        "duration": "Duration "+inFlight['duration']
                        }
                    
                    result["result_id"] = "RT-FL1-"+inFlight['flightNumber'].split(" ")[-1]
                    if outFlight != []:
                        result["result_id"] = result["result_id"] +"-FL2-"+outFlight['flightNumber'].split(" ")[-1]
                        result['return_flight_data'] = outFlight
                        result['return_flight_data'] = { 
                            "flight_number": outFlight['flightNumber'],
                            "flight_type": "Direct",
                            "origin_airport_name": data[0]['trips'][0]['originName'],
                            "destination_airport_name": data[0]['trips'][0]['destinationName'],
                            "departure_time": datetime.datetime.strptime(outFlight['segments'][0]['time'][0], "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                            "arrival_time": datetime.datetime.strptime(outFlight['segments'][0]['time'][1], "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                            "duration": "Duration "+outFlight['duration']
                        }

                    result['fare_types'] = []
                    responseData['result'] = [result]
                    return send_response(
                        status=status.HTTP_200_OK,
                        data= responseData, #json.dumps(responseData),
                        ui_message = "Request successful"
                        # print(data);
                        # response['result_id'] = serializer.
                    )
                else:
                    return send_response(
                        status=status.HTTP_400_BAD_REQUEST,
                        data=response.json(),
                        ui_message = "Request was failed"
                    )

            except Exception as e:
                return send_response(
                        status=status.HTTP_400_BAD_REQUEST,
                        data=str(e),
                        
                        ui_message = "Request was failed"
                    )