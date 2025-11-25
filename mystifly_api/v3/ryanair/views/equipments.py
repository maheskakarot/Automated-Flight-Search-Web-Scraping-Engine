import os
import sys

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from account.authentication import ExpiringTokenAuthentication
from utils.error_logging import send_error_mail
from utils.restful_response import send_response
from v1.ryanair.helpers.webdriver import reuse_webdriver
from v2.ryanair.scripts.equipments import Equipments
from v2.ryanair.helpers.equipments import validate_equipments_select_payload


class EquipmentRetrieve(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)

        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")
        try:
            equipment_details = Equipments(driver, request.data).retrieve_equipment_details()
            if len(equipment_details) != 0:
                return send_response(status=status.HTTP_200_OK,
                                     developer_message="Equipment Details Retrieve Successful",
                                     data=equipment_details)
            else:
                return send_response(status=status.HTTP_400_BAD_REQUEST,
                                     developer_message="Equipment Details Retrieve Unsuccessful",
                                     )
        except Exception as ex:
            screen_name = "Equipment Retrieve"
            error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)
            return send_response(status=status.HTTP_400_BAD_REQUEST,
                                 developer_message="Equipment Details Retrieve Unsuccessful",
                                 )


# class EquipmentSelection(generics.CreateAPIView):
#     authentication_classes = (ExpiringTokenAuthentication,)
#     permission_classes = (IsAuthenticated,)
#
#     def create(self, request, *args, **kwargs):
#
#         subscriber = request.user.subscriber
#         driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)
#
#         equipments_names = ["bike", "ski", "large sports", "music equipment", "baby equipment", "golf", "other sports"]
#
#         if not is_driver_reused:
#             driver.close()
#             return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")
#
#         data = request.data.get('Equipments', None)
#         if data:
#             for each in data:
#                 if each['Name'].lower() not in equipments_names:
#                     return send_response(status=status.HTTP_400_BAD_REQUEST,
#                                          developer_message="Wrong equipments name passed",
#                                          )
#                 try:
#                     status_code = Equipments(driver).make_equipment_selection(each['Name'], each['PassengerList'])
#                     if status_code == 0:
#                         return send_response(status=status.HTTP_400_BAD_REQUEST,
#                                              developer_message="Count is more than 2",
#                                              )
#                     elif status_code == -1:
#                         return send_response(status=status.HTTP_400_BAD_REQUEST,
#                                              developer_message="Parameters is missing",
#                                              )
#                 except Exception as e:
#                     screen_name = "Equipment Selection"
#                     error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, e, request.data)
#                     return send_response(status=status.HTTP_400_BAD_REQUEST,
#                                          developer_message="Equipment Selection Unsuccessful",
#                                          )
#
#             return send_response(status=status.HTTP_200_OK, developer_message="Equipment Selection Successful",
#                                  )
#
#         else:
#             return send_response(status=status.HTTP_400_BAD_REQUEST,
#                                  developer_message="Parameters are missing")
#

class EquipmentSelection(generics.CreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):

        subscriber = request.user.subscriber
        driver, is_driver_reused, webdriver_obj = reuse_webdriver(subscriber)

        message = validate_equipments_select_payload(request.data)

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

        if not is_driver_reused:
            driver.close()
            return send_response(status=status.HTTP_400_BAD_REQUEST, developer_message="Unable to reuse driver")

        try:
            Equipments(driver, request.data).select_equipments()
            return send_response(status=status.HTTP_200_OK,
                                 developer_message="Equipment Selection Successful",
                                 )

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

            screen_name = "Equipment Selection"
            error = send_error_mail(driver, subscriber, webdriver_obj, screen_name, ex, request.data)
            return send_response(status=status.HTTP_400_BAD_REQUEST, error=error,
                                 developer_message="Equipment Selection Unsuccessful",
                                 )
