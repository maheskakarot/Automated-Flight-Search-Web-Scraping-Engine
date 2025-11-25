from datetime import datetime
from rest_framework import generics, status
from account.authentication import ExpiringTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from v1.ryanair.helpers.webdriver import reuse_webdriver, close_webdriver
from v1.ryanair.serializers import PaymentSerializer
from utils.restful_response import send_response
from v1.ryanair.scripts.ryan_air import RyanairWebsiteAutomation
from account.models import SubscriberSearchHistory
from v1.ryanair.scripts.popups import HandlePopups
from utils.error_logging import send_completion_mail
from utils.error_logging import send_error_mail

class PaymentView(generics.CreateAPIView):
    serializer_class = PaymentSerializer
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)

        serializer = PaymentSerializer(data=request.data)

        if serializer.is_valid():
            history_obj = SubscriberSearchHistory.objects.filter(subscriber=subscriber).last()
            if history_obj.current_screen == SubscriberSearchHistory.PAYMENT_SCREEN:
                driver.refresh()
                driver.execute_script("window.scrollTo(0, 0)")

            else:
                history_obj.current_screen = SubscriberSearchHistory.PAYMENT_SCREEN
                history_obj.save()

            # Check if session is active or not
            error = HandlePopups(driver, {}).check_active_session()

            if len(error):
                screen_name = "Initiate payment"
                ex = repr(error)
                send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)
                return send_response(status=status.HTTP_400_BAD_REQUEST,
                                     error=error,
                                     developer_message="Error while initiating payment",
                                     ui_message="Error while initiating payment")

            is_payment_complete, reservation_number, errors, error_title, error_content = RyanairWebsiteAutomation(
                driver, request.data).complete_payment()

            # send_completion_mail(driver, "Payment Complete")

            if not is_payment_complete:
                error = {
                    "validation_error": errors,
                    "error_title": error_title,
                    "error_content": error_content
                }
                screen_name = "Initiate payment"
                ex = repr(error)
                send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)

                return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                     developer_message="Payment failed",
                                     ui_message="Payment failed")

            data = {
                'reservation_number': reservation_number
            }

            return send_response(status=status.HTTP_200_OK, data=data, developer_message="Payment successful")

        else:
            screen_name = "Initiate payment"
            ex = "Request data is not valid"
            send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)
            return send_response(status=status.HTTP_400_BAD_REQUEST, error=serializer.errors,
                                 developer_message="Request data is not valid",
                                 ui_message="Request data is not valid")
