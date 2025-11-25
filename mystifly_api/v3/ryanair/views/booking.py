from datetime import datetime
from rest_framework import generics, status
from account.authentication import ExpiringTokenAuthentication
from account.models import SubscriberSearchHistory
from rest_framework.permissions import IsAuthenticated
from utils.restful_response import send_response
from utils.email_utils import send_email
from utils.error_logging import send_error_mail
from v1.ryanair.serializers import InitiateBookingSerializer
from v1.ryanair.helpers.webdriver import reuse_webdriver, close_webdriver
from v2.ryanair.helpers.fast_track import check_valid_request
from v2.ryanair.scripts.ryan_air import RyanairWebsiteAutomation
from v2.ryanair.scripts.common import CommonActions
from v2.ryanair.scripts.popups import HandlePopups
from utils.error_logging import send_completion_mail
from v2.ryanair.helpers.baggages import validate_baggages_select_payload


class InitiateBooking(generics.CreateAPIView):
    serializer_class = InitiateBookingSerializer
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)
        history_obj = SubscriberSearchHistory.objects.filter(subscriber=subscriber).last()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user_last_screen = history_obj.current_screen
            if is_driver_reused and (user_last_screen == SubscriberSearchHistory.INITIATE_BOOKING or
                                     user_last_screen == SubscriberSearchHistory.SEAT_SELECTION_SCREEN):
                driver.back()

            if not is_driver_reused:
                driver.get(history_obj.url)
                CommonActions(driver).accept_cookies()

            try:
                # Check if session is active or not
                error = HandlePopups(driver, {}).check_active_session()

                if len(error):
                    return send_response(status=status.HTTP_400_BAD_REQUEST,
                                         error=error,
                                         developer_message="Error while initiating booking",
                                         ui_message="Error while initiating booking")

                response_data, is_initiated = RyanairWebsiteAutomation(driver, request.data).initiate_booking(
                    is_driver_reused, subscriber, user_last_screen
                )

                history_obj.current_screen = SubscriberSearchHistory.INITIATE_BOOKING
                history_obj.save()

                # send_completion_mail(driver, "Initiate Booking Complete")
                return send_response(status=status.HTTP_200_OK, data=response_data)

            except Exception as ex:
                screen_name = "Initiate Booking"
                error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)

                return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                     developer_message="Request was failed",
                                     ui_message="Request was failed"
                                     )

        else:

            return send_response(status=status.HTTP_400_BAD_REQUEST, error=serializer.errors)


class SeatSelection(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)

        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")

        try:
            # Check if session is active or not
            error = HandlePopups(driver, {}).check_active_session()

            if len(error):
                return send_response(status=status.HTTP_400_BAD_REQUEST,
                                     error=error,
                                     developer_message="Error while selecting seats",
                                     ui_message="Error while selecting seats")

            history_obj = SubscriberSearchHistory.objects.filter(subscriber=subscriber).last()
            history_obj.current_screen = SubscriberSearchHistory.SEAT_SELECTION_SCREEN
            history_obj.save()

            is_selected, seat_map, any_warning, warning_title, warning_body = \
                RyanairWebsiteAutomation(driver, request.data).seat_selection(subscriber)

            if not is_selected or any_warning:
                # send_completion_mail(driver, "Seat Selection Warning")

                error = {
                    'warning_title': warning_title,
                    'warning_body': warning_body
                }

                return send_response(status=status.HTTP_400_BAD_REQUEST,
                                     error=error,
                                     developer_message="Error while selecting seats",
                                     ui_message="Error while selecting seats")

            # send_completion_mail(driver, "Seat Selection Complete")

            data = {
                'SeatMap': seat_map
            }

            return send_response(status=status.HTTP_200_OK, data=data,
                                 developer_message="Seat selected successfully",
                                 ui_message="Seat selected successfully"
                                 )

        except Exception as ex:
            screen_name = "Seat Selection"
            error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)

        return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                             developer_message="Request was failed",
                             ui_message="Request was failed"
                             )


class BaggagesSelection(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)

        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")

        try:
            history_obj = SubscriberSearchHistory.objects.filter(subscriber=subscriber).last()
            history_obj.current_screen = SubscriberSearchHistory.BAGGAGES_SCREEN
            history_obj.save()

            error = HandlePopups(driver, {}).check_active_session()

            if len(error):
                return send_response(status=status.HTTP_400_BAD_REQUEST,
                                     error=error,
                                     developer_message="Error while selecting baggages",
                                     ui_message="Error while selecting baggages")

            response_data = RyanairWebsiteAutomation(driver, request.data).baggages_selection(is_driver_reused)

            # send_completion_mail(driver, "Baggages Selection")
            return send_response(status=status.HTTP_200_OK, data=response_data)

        except Exception as ex:
            screen_name = "Baggages Selection"
            error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)

            return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                 developer_message="Request was failed",
                                 ui_message="Request was failed"
                                 )


class RetrieveFastTrackInfoView(generics.ListAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)

        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")

        fast_track_info = RyanairWebsiteAutomation(driver, request.data).retrieve_fast_track_info()
        # send_completion_mail(driver, "Fast track retrieve")

        return send_response(status=status.HTTP_200_OK, data=fast_track_info,
                             developer_message="Request was successful",
                             ui_message="Request was successful",
                             )


class AddFastTrackView(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)

        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")

        try:
            departure_valid, arrival_valid = check_valid_request(request.data)

            if not departure_valid:
                error = {
                    "message": "Please check departure flight data, You can't add fast track to Child without adult."
                }
                return send_response(
                    status=status.HTTP_400_BAD_REQUEST,
                    error=error,
                    ui_message="Request failed",
                    developer_message="Request failed",
                )

            if not arrival_valid:
                error = {
                    "message": "Please check arrival flight data, You can't add fast track to Child without adult."
                }
                return send_response(
                    status=status.HTTP_400_BAD_REQUEST,
                    error=error,
                    ui_message="Request failed",
                    developer_message="Request failed",
                )

            response_data = RyanairWebsiteAutomation(driver, request.data).add_fast_track_to_flights()

            # send_completion_mail(driver, "Fast Track Added")

            data = response_data

            return send_response(status=status.HTTP_200_OK, data=data,
                                 ui_message="Request was successful",
                                 developer_message="Request was successful"
                                 )

        except Exception as ex:
            screen_name = "Fast Track Selection"
            error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)

            return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                 developer_message="Request was failed",
                                 ui_message="Request was failed"
                                 )


class BaggagesInfoView(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)

        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")

        try:
            data = RyanairWebsiteAutomation(driver, request.data).scrape_baggages_data()
            # send_completion_mail(driver, "Baggages List")

            return send_response(status=status.HTTP_200_OK, data=data,
                                 developer_message="Request was successful",
                                 ui_message="Request was successful",
                                 )

        except Exception as ex:
            screen_name = "Baggage Retrieve"
            error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)

            return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                 developer_message="Request was failed",
                                 ui_message="Request was failed"
                                 )


class SelectBaggagesView(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        message = validate_baggages_select_payload(self.request.data)
        if message:
            error = {
                'message': message
            }
            return send_response(
                status=status.HTTP_400_BAD_REQUEST,
                error=error,
                ui_message="Request Failed",
                developer_message="Request Failed"
            )
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)

        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")

        try:
            data = RyanairWebsiteAutomation(driver, request.data).select_baggages()
            # send_completion_mail(driver, "Baggages Select")

            return send_response(status=status.HTTP_200_OK, data=data,
                                 developer_message="Request was successful",
                                 ui_message="Request was successful",
                                 )
        except Exception as ex:
            screen_name = "Baggage Select"
            error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)

            return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                 developer_message="Request was failed",
                                 ui_message="Request was failed"
                                 )
