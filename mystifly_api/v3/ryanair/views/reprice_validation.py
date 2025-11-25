from rest_framework import generics, status
from account.authentication import ExpiringTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from utils.restful_response import send_response
from v1.ryanair.helpers.webdriver import reuse_webdriver, update_current_screen, close_webdriver
from v1.ryanair.serializers import RepriceValidationSerializer
from v3.ryanair.scripts.ryan_air import RyanairWebsiteAutomation
from account.models import SubscriberSearchHistory
from v2.ryanair.scripts.common import CommonActions
from utils.error_logging import send_error_mail


class RepriceValidationView(generics.CreateAPIView):
    serializer_class = RepriceValidationSerializer
    authentication_classes = (ExpiringTokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)
        history_obj = SubscriberSearchHistory.objects.filter(subscriber=subscriber).last()

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if is_driver_reused:
                if history_obj.current_screen == SubscriberSearchHistory.REPRICE_SCREEN:
                    CommonActions(driver).edit_flight_button()

                history_obj.current_screen = SubscriberSearchHistory.REPRICE_SCREEN
                history_obj.save()

            else:
                request.data['last_search_url'] = history_obj.url
                driver.get(history_obj.url)
                CommonActions(driver).accept_cookies()
                history_obj.current_screen = SubscriberSearchHistory.REPRICE_SCREEN
                history_obj.save()

            try:
                data, is_verified = RyanairWebsiteAutomation(driver, request.data).reprice_validation()

            except Exception as ex:
                screen_name = "Baggages Selection"
                error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex)

                return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                     developer_message="Request was failed",
                                     ui_message="Request was failed"
                                     )
            if is_verified:
                return send_response(status=status.HTTP_200_OK, data=data,
                                     developer_message="Reprice validation is successful",
                                     ui_message="Reprice validation is successful"
                                     )

            else:
                return send_response(status=status.HTTP_409_CONFLICT, data=data,
                                     developer_message="Reprice validation not success, please try again.",
                                     ui_message="Reprice validation not success, please try again."
                                     )

        return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Request was failed", error=serializer.errors)


class ApiRepriceValidationView(generics.CreateAPIView):
    serializer_class = RepriceValidationSerializer
    authentication_classes = (ExpiringTokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        history_obj = SubscriberSearchHistory.objects.filter(subscriber=subscriber).last()

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():

            history_obj.current_screen = SubscriberSearchHistory.REPRICE_SCREEN
            history_obj.save()
            print(history_obj.url)
            request.data['last_search_url'] = history_obj.url
            request.data['adults'] = history_obj.adult
            request.data['children'] = history_obj.child
            request.data['infants'] = history_obj.infant

            try:
                is_verified, reprice_fare_info, error = RyanairWebsiteAutomation(request.data).reprice_validation()
            except Exception as ex:
                error = str(ex)
                return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                     developer_message="Request was failed",
                                     ui_message="Request was failed"
                                     )
            if is_verified:
                return send_response(status=status.HTTP_200_OK, data=reprice_fare_info,
                                     developer_message="Reprice validation is successful",
                                     ui_message="Reprice validation is successful"
                                     )

            else:
                return send_response(status=status.HTTP_409_CONFLICT, data=reprice_fare_info,
                                     developer_message="Reprice validation not success, please try again.",
                                     ui_message="Reprice validation not success, please try again."
                                     )

        return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Request was failed", error=serializer.errors)
