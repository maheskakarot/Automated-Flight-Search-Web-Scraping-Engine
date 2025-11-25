from datetime import datetime
from rest_framework import generics, status
from account.authentication import ExpiringTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from v1.ryanair.scripts.common import CommonActions
from v1.ryanair.serializers import InitiateBookingSerializer
from account.models import SubscriberSearchHistory
from v1.ryanair.helpers.webdriver import reuse_webdriver, close_webdriver
from v1.ryanair.scripts.ryan_air import RyanairWebsiteAutomation
from utils.restful_response import send_response
from utils.email_utils import send_email
from utils.error_logging import send_error_mail
from v1.ryanair.scripts.popups import HandlePopups
from utils.error_logging import send_completion_mail


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
                error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex)

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

            is_selected, seat_map, any_warning, warning_title, warning_body = RyanairWebsiteAutomation(driver, request.data).seat_selection(subscriber)

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

            # send_completion_mail(driver, "Seat Selection")

            response_data = {
                'SeatMap': seat_map
            }

            return send_response(status=status.HTTP_200_OK, data=response_data,
                                 developer_message="Seat selected successfully",
                                 ui_message="Seat selected successfully"
                                 )

        except Exception as ex:
            screen_name = "Seat Selection"
            error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex)

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
            error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex)

        return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                             developer_message="Request was failed",
                             ui_message="Request was failed"
                             )
