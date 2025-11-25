import time
from rest_framework import generics, status
from account.authentication import ExpiringTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from selenium.webdriver.common.by import By
from v1.ryanair.scripts.common import CommonActions
from v1.ryanair.helpers.webdriver import reuse_webdriver, close_webdriver
from utils.restful_response import send_response
from utils.error_logging import send_completion_mail
from v1.ryanair.constants.urls import RYANAIR_HOME_URL
from v1.ryanair.constants.xpaths import XPATHS
from account.models import AdminCookies


class LoginView(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)
        user_email = request.data.get('UserEmail', None)
        user_password = request.data.get('UserPassword', None)

        driver.get(RYANAIR_HOME_URL)
        CommonActions(driver).accept_cookies()

        if user_email and user_password:
            driver.find_element(By.XPATH, XPATHS['HEADER_LOGIN_BUTTON']).click()
            CommonActions(driver).login(user_email, user_password)
            # send_completion_mail(driver, "Login View")

            return send_response(status=status.HTTP_200_OK, developer_message="OTP Sent Successful")

        else:
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Username or password is missing")


class SubmitConfirmationCode(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)
        user_email = request.data.get('UserEmail', None)
        confirmation_code = request.data.get('Code', None)

        if confirmation_code:
            CommonActions(driver).submit_confirmation_code(confirmation_code)
            time.sleep(2)
            cookies = str(driver.get_cookies())
            instance, is_created = AdminCookies.objects.get_or_create(user_email=user_email)
            instance.cookies = cookies
            instance.save()

            return send_response(status=status.HTTP_200_OK, developer_message="Login successful")

        else:
            return send_response(status=status.HTTP_400_BAD_REQUEST,
                                 developer_message="Confirmation code is missing")
