from rest_framework import generics, status
from account.authentication import ExpiringTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from utils.restful_response import send_response
from v1.ryanair.models import Airport
from v1.ryanair.serializers import AirportSerializer, FlightSearchSerializer
from v3.ryanair.scripts.ryan_air import RyanairWebsiteAutomation
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
        # driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)
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
                website_url=required_data['website_search_url'],
                adult=required_data.get('adults'),
                teen=required_data.get('teens'),
                child=required_data.get('children'),
                infant=required_data.get('infants'),
            )

            booking_request = {
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
                    booking_request).search_flights(search_url)

                flights_data['cpu_load'] = cpu_load

            except Exception as ex:
                screen_name = "Search"
                error = str(ex)
                # error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)

                return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                     developer_message="Request was failed 2",
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


class SearchFlightUpdatedViewV3(generics.GenericAPIView):

    def post(self, request):

        flight = json.loads(request.body)
        print(flight)
        responseData = {}
        inDate = flight['OriginDestinationInformations'][0]['DepartureDateTime'].split('T')[0]
        outDate = flight['OriginDestinationInformations'][0]['DepartureDateTime'].split('T')[0]
        origin = flight['OriginDestinationInformations'][0]['OriginLocationCode']
        destination = flight['OriginDestinationInformations'][0]['DestinationLocationCode']
        # inDate = request.POST.get('date_in')
        # outDate = request.POST.get('date_out')
        # origin = request.POST.get('origin')
        # destination = request.POST.get('destination')
        inFlight = []
        outFlight = []

        if flight is not None:
            try:
                print(
                    f"https://www.ryanair.com/api/booking/v4/en-gb/availability?ADT={flight['PassengerTypeQuantities'][0]['Quantity']}&CHD={flight['PassengerTypeQuantities'][1]['Quantity']}&DateIn={inDate}&DateOut={outDate}&Destination={destination}&Disc=&INF=0&Origin={origin}&TEEN=0&promoCode=&IncludeConnectingFlights=false&FlexDaysBeforeOut=2&FlexDaysOut=2&FlexDaysBeforeIn=2&FlexDaysIn=2&RoundTrip=true&ToUs=AGREED")
                response = requests.get(
                    f"https://www.ryanair.com/api/booking/v4/en-gb/availability?ADT={flight['PassengerTypeQuantities'][0]['Quantity']}&CHD={flight['PassengerTypeQuantities'][1]['Quantity']}&DateIn={inDate}&DateOut={outDate}&Destination={destination}&Disc=&INF=0&Origin={origin}&TEEN=0&promoCode=&IncludeConnectingFlights=false&FlexDaysBeforeOut=2&FlexDaysOut=2&FlexDaysBeforeIn=2&FlexDaysIn=2&RoundTrip=true&ToUs=AGREED")
                get_fare_values = requests.get(
                    'https://www.ryanair.com/apps/ryanair/i18n.frontend.auth.flightselect.legalfooter.networkerrors.deposit-payment.chatbot.breadcrumbs.en-gb.json').json()

                if response.status_code == 200:
                    data = response.json()

                    for trips in data['trips']:
                        for dates in trips['dates']:
                            flightDate = datetime.datetime.strptime(dates['dateOut'], "%Y-%m-%dT%H:%M:%S.%f").strftime(
                                '%Y-%m-%d')

                            if flightDate == inDate or flightDate == outDate:
                                fare_currency = data['currency']
                                seat_count = dates['flights'][0]['regularFare']['fares'][0]['count']
                                depart_value = data['trips'][0]['dates'][2]['flights'][0]['regularFare']['fares'][0][
                                    'amount']
                                arrival_value = data['trips'][1]['dates'][2]['flights'][0]['regularFare']['fares'][0][
                                    'amount']
                                fare_value = ''

                                for flight in dates['flights']:
                                    if trips['origin'] == origin:
                                        inFlight = flight
                                    elif trips['origin'] == destination:
                                        outFlight = flight

                    print("ksdjfhasdhfashdf")
                    result = {}

                    result['departure_flight_data'] = {
                        "flight_number": inFlight['flightNumber'],
                        "flight_type": "Direct",
                        "origin_airport_name": data['trips'][0]['originName'],
                        "destination_airport_name": data['trips'][0]['destinationName'],
                        "departure_time": datetime.datetime.strptime(inFlight['segments'][0]['time'][0],
                                                                     "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                        "arrival_time": datetime.datetime.strptime(inFlight['segments'][0]['time'][1],
                                                                   "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                        "duration": "Duration " + inFlight['duration']
                    }

                    result["result_id"] = "RT-FL1-" + inFlight['flightNumber'].split(" ")[-1]

                    if outFlight:
                        result["result_id"] = result["result_id"] + "-FL2-" + outFlight['flightNumber'].split(" ")[-1]
                        result['return_flight_data'] = outFlight
                        result['return_flight_data'] = {
                            "flight_number": outFlight['flightNumber'],
                            "flight_type": "Direct",
                            "origin_airport_name": data['trips'][0]['originName'],
                            "destination_airport_name": data['trips'][0]['destinationName'],
                            "departure_time": datetime.datetime.strptime(outFlight['segments'][0]['time'][0],
                                                                         "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                            "arrival_time": datetime.datetime.strptime(outFlight['segments'][0]['time'][1],
                                                                       "%Y-%m-%dT%H:%M:%S.%f").strftime('%H:%M'),
                            "duration": "Duration " + outFlight['duration']
                        }

                    result['fare_types'] = [{
                        "fare_type": get_fare_values['fare-card']['title-v2']['standard'],
                        "fare_desc": get_fare_values['fare-card']['subtitle-standard'],
                        "ancillaries": [
                            {
                                "ancillary_name": get_fare_values['fare-card']['benefit-v2'][
                                    'title-small_bag-standard'],
                                "ancillary_desc": get_fare_values['fare-card']['benefit'][
                                    'description-small_bag-standard']
                            }
                        ],
                        "fare_currency": fare_currency,
                        "fare_value": fare_value,
                        "fare_breakdown": {
                            "departure_flight_info": {
                                "seats_info": {
                                    "adult_seats_info": {
                                        "seat_count": seat_count,
                                        "items_included": [],
                                        "items_description": [],
                                        "fare_info": {
                                            "currency": fare_currency,
                                            "value": depart_value
                                        }
                                    }
                                },
                                "tax_items_info": [],
                                "discounts": []
                            },
                            "arrival_flight_info": {
                                "seats_info": {
                                    "adult_seats_info": {
                                        "seat_count": seat_count,
                                        "items_included": [],
                                        "items_description": [],
                                        "fare_info": {
                                            "currency": fare_currency,
                                            "value": arrival_value
                                        }
                                    }
                                },
                                "tax_items_info": [],
                                "discounts": []
                            },
                            "total_amount_to_pay": {
                                "currency": fare_currency,
                                "value": depart_value + arrival_value
                            }
                        }
                    }]

                    responseData['result'] = [result]

                    return send_response(
                        status=status.HTTP_200_OK,
                        data=responseData,
                        ui_message="Request successful"
                    )
                else:
                    return send_response(
                        status=status.HTTP_400_BAD_REQUEST,
                        data=response.json(),
                        ui_message="Request failed"
                    )

            except Exception as e:
                return send_response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data=str(e),

                    ui_message="Request failed"
                )
