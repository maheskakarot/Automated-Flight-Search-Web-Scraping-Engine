import time

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from account.authentication import ExpiringTokenAuthentication
from utils.error_logging import send_error_mail
from v1.ryanair.helpers.webdriver import reuse_webdriver

from v2.ryanair.scripts.reissuance import Reissuance
from utils.restful_response import send_response


class ReissuanceFlightSearchView(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)
        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")

        source = request.data.get('source', None)
        destination = request.data.get('destination', None)
        journey_date = request.data.get('date', None)
        reservation_number = request.data.get('reservation_no', None)

        try:
            if source and destination and journey_date and reservation_number:

                flight_list = Reissuance(driver).flight_search(source, destination, journey_date, reservation_number)

                if flight_list == -1:
                    return send_response(status=status.HTTP_400_BAD_REQUEST,
                                         developer_message="Payment is not done completely")

                return send_response(status=status.HTTP_200_OK, developer_message="Search Successful", data=flight_list)

            else:
                return send_response(status=status.HTTP_400_BAD_REQUEST,
                                     developer_message="Parameters are missing")
        except Exception as ex:
            screen_name = "Reissuance Flight Search View"
            error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)

            return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                 developer_message="Request was failed",
                                 ui_message="Request was failed"
                                 )


class ReissuancePriceVariationView(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)
        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")

        flight_no = request.data.get('flight_no', None)

        try:
            if flight_no:

                cart_details = Reissuance(driver).select_flight_find_fare_difference(flight_no)

                return send_response(status=status.HTTP_200_OK, developer_message="Price Difference", data=cart_details)

            else:
                return send_response(status=status.HTTP_400_BAD_REQUEST,
                                     developer_message="Selected Flight details missing")
        except Exception as ex:
            screen_name = "Reissuance Price Variation"
            error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)

            return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                 developer_message="Request was failed",
                                 ui_message="Request was failed"
                                 )


class ReissuanceInitiatePaymentView(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)
        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")

        card_detail = request.data.get('CardDetails', None)
        address_1 = request.data.get('AddressLineFirst', None)
        address_2 = request.data.get('AddressLineSecond', None)
        city = request.data.get('City', None)
        state = request.data.get('State', None)
        country = request.data.get('Country', None)
        pincode = request.data.get('PostCode', None)

        try:
            if card_detail and (address_1 or address_2) and city and country:

                payment_status = Reissuance(driver).initiate_payment(card_detail, address_1, address_2, pincode, city,
                                                                     state,
                                                                     country)

                if payment_status == -1:
                    return send_response(status=status.HTTP_400_BAD_REQUEST,
                                         developer_message="Error while initiating payment",
                                         ui_message="Error while initiating payment")
                else:
                    return send_response(status=status.HTTP_200_OK, developer_message="Payment Successful", )

            else:
                return send_response(status=status.HTTP_400_BAD_REQUEST,
                                     developer_message="Data Missing")
        except Exception as ex:
            screen_name = "Reissuance Initiate Payment"
            error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)

            return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                 developer_message="Request was failed",
                                 ui_message="Request was failed"
                                 )


class ReissuancePrintReceiptView(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)
        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")

        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")
        try:
            reservation_number = request.data.get('reservation_no', None)

            if reservation_number:

                booking_details = Reissuance(driver).print_receipt(reservation_number)

                if booking_details == -1:
                    return send_response(status=status.HTTP_400_BAD_REQUEST,
                                         developer_message="Payment is not done completely")

                return send_response(status=status.HTTP_200_OK, developer_message="Print Receipt Successful",
                                     data=booking_details)

            else:
                return send_response(status=status.HTTP_400_BAD_REQUEST,
                                     developer_message="Parameters are missing")
        except Exception as ex:
            screen_name = "Reissuance Print Receipt"
            error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)

            return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                 developer_message="Request was failed",
                                 ui_message="Request was failed"
                                 )
