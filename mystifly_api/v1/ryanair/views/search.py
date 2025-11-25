from rest_framework import generics, status
from account.authentication import ExpiringTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from utils.restful_response import send_response
from v1.ryanair.models import Airport
from v1.ryanair.serializers import AirportSerializer, FlightSearchSerializer
from v1.ryanair.scripts.ryan_air import RyanairWebsiteAutomation
from v1.ryanair.helpers.webdriver import reuse_webdriver, close_webdriver
from account.models import SubscriberSearchHistory
from utils.error_logging import send_error_mail


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

            except Exception as ex:
                screen_name = "Search"
                error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex)

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
