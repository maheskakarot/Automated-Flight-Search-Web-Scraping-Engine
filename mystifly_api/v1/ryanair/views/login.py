import ast
from datetime import datetime
from rest_framework import generics, status
from account.authentication import ExpiringTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from v1.ryanair.scripts.common import CommonActions
from v1.ryanair.helpers.webdriver import reuse_webdriver, close_webdriver
from utils.restful_response import send_response
from account.models import AdminCookies
from utils.email_utils import send_email
from account.models import SubscriberSearchHistory
from utils.error_logging import send_completion_mail


class LoginView(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)
        user_email = request.data.get('UserEmail', None)
        user_password = request.data.get('UserPassword', None)

        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")

        history_obj = SubscriberSearchHistory.objects.filter(subscriber=subscriber).last()
        history_obj.current_screen = SubscriberSearchHistory.LOGIN_SCREEN
        history_obj.save()

        admin_cookies_obj = AdminCookies.objects.filter(user_email=user_email).first()

        if admin_cookies_obj:
            cookies = ast.literal_eval(admin_cookies_obj.cookies)
            for cookie in cookies:
                driver.add_cookie(cookie)

        if user_email and user_password:
            CommonActions(driver).login(user_email, user_password)
            # send_completion_mail(driver, "Login View")

            return send_response(status=status.HTTP_200_OK, developer_message="Login Successful")

        else:
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Username or password is missing")


class SubmitConfirmationCode(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)
        confirmation_code = request.data.get('Code', None)

        if confirmation_code:
            CommonActions(driver).submit_confirmation_code(confirmation_code)

            return send_response(status=status.HTTP_200_OK, developer_message="Login successful")

        else:
            return send_response(status=status.HTTP_400_BAD_REQUEST,
                                 developer_message="Confirmation code is missing")
