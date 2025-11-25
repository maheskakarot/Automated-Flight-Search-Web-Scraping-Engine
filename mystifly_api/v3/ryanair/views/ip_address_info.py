from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from account.authentication import ExpiringTokenAuthentication
from utils.restful_response import send_response
from v1.ryanair.helpers.webdriver import reuse_webdriver
from v2.ryanair.scripts.ip_address_info import IpAddressInfo


class IpAddressRetrieve(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)

        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")
        try:
            ip_address = IpAddressInfo(driver).scrap_details()

            return send_response(status=status.HTTP_200_OK,
                                 developer_message="Ip address Retrieve Successful",
                                 data=ip_address)
        except Exception as e:
            return send_response(status=status.HTTP_400_BAD_REQUEST,
                                 developer_message="Ip address Retrieve Unsuccessful",
                                 )
