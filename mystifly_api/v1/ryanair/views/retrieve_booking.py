from rest_framework import generics, status
from account.authentication import ExpiringTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from selenium.webdriver.common.by import By
from v1.ryanair.constants.urls import RYANAIR_HOME_URL
from v1.ryanair.constants.xpaths import XPATHS
from v1.ryanair.helpers.webdriver import reuse_webdriver
from v1.ryanair.scripts.common import CommonActions
from v1.ryanair.scripts.retrieve_booking import RetrieveBooking
from utils.restful_response import send_response


class RetrieveBookingLoginView(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)

        driver.get(RYANAIR_HOME_URL)
        CommonActions(driver).accept_cookies()
        user_email = request.data.get('UserEmail', None)
        user_password = request.data.get('UserPassword', None)

        if user_email and user_password:
            CommonActions(driver).load_cookies_into_driver(user_email)
            driver.find_element(By.XPATH, XPATHS['HEADER_LOGIN_BUTTON']).click()
            CommonActions(driver).login(user_email, user_password)

            return send_response(status=status.HTTP_200_OK, developer_message="Login Successful")

        else:
            return send_response(status=status.HTTP_400_BAD_REQUEST,
                                 developer_message="Username or password is missing")


class RetrieveBookingView(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)

        if is_driver_reused:
            reservation_number = request.data.get('ReservationNumber', None)
            retrieve_booking = {}

            if reservation_number:
                upcoming_details = RetrieveBooking(driver).retrieve_upcoming_booking(reservation_number)
                retrieve_booking['upcoming_trips'] = upcoming_details

                return send_response(status=status.HTTP_200_OK, developer_message="Retrieve Successful",
                                     data=retrieve_booking)

            upcoming_details = RetrieveBooking(driver).retrieve_upcoming_booking(reservation_number)
            past_trip_details = RetrieveBooking(driver).retrieve_past_trip(reservation_number)

            retrieve_booking['upcoming_trips'] = upcoming_details
            retrieve_booking['past_trips'] = past_trip_details

            return send_response(status=status.HTTP_200_OK, developer_message="Retrieve Successful",
                                 data=retrieve_booking)

        else:
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")
