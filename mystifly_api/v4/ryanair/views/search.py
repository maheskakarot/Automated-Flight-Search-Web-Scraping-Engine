from rest_framework import generics, status
from account.authentication import ExpiringTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from utils.restful_response import send_response
from v1.ryanair.serializers import AirportSerializer, FlightSearchSerializer
from v4.ryanair.scripts.ryan_air import RyanairWebsiteAutomation
from account.models import SubscriberSearchHistory
from utils.load_balancer import is_max_cpu_load


class SearchFlightView(generics.CreateAPIView):
    serializer_class = FlightSearchSerializer
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        cpu_load, is_max_load = is_max_cpu_load()
        # if is_max_load:
        #     data = {'cpu_load': cpu_load}
        #     return send_response(
        #         status=status.HTTP_400_BAD_REQUEST,
        #         data=data,
        #         developer_message="Request failed due to maximum cpu load.",
        #         ui_message="Request failed due to maximum cpu load."
        #     )

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
