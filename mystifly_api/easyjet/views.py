from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework import status
from rest_framework.response import Response
from .serializers import FlightSearchSerializer, RepriceValidationSerializer, BookingSerializer
from easyjet.scripts.booking import BookingAutomation
from easyjet.scripts.revalidation_flights import RepriceValidationAutomation
from .scripts.search_flights import Search_flights
from utils.Azure_blob_manager import API_data,AzureBlob
import json
from django.conf import settings
# from utils.error_logging import send_error_mail,easyjet_error_email
from utils.webdriver_reuse import reuse_webdriver
from easyjet.scripts.booking import BookingAutomation
import json
from utils.api_error_logging import send_error_mail
from utils.webdriver_reuse import reuse_webdriver
from easyjet.models import SearchIdentifier
from easyjet.scripts.easyjet_scraping import Scraping



class FlightSearchView(CreateAPIView):
    serializer_class = FlightSearchSerializer
    azure_obj = AzureBlob()
   
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        azure_data = []

        if serializer.is_valid():
            config = request.data.get('MysAzureConfig')    
            search_identifier = request.data['SearchIdentifier']

            str_data=json.dumps(request.data)
            req_api = API_data(str_data,'Search','U2S','request')
            azure_data.append(req_api)
            is_log_enabled = request.data['IsLogEnabled']

            search_obj = Search_flights(request.data)
            try:
                response,logs = search_obj.search_automation()

                if is_log_enabled :
                    log_data = API_data(str(logs),"Search APIs","U2S","Response")
                    azure_data.append(log_data)


                str_res = json.dumps(response)

                res_api = API_data(str_res,'Search','U2S','response')
                azure_data.append(res_api)

                self.azure_obj.upload_data_to_blob_storage(config, search_identifier, azure_data)

                return Response(response)
            except Exception as e:
                print(e)
                screen_name = 'Easyjet Search API'
                if settings.IS_KIBANA_ENABLED:
                    send_error_mail(search_identifier, screen_name, e)
                res_api = API_data(str(e),'Search','U2S','response')
                azure_data.append(res_api)
                self.azure_obj.upload_data_to_blob_storage(config, request.data.get('SearchIdentifier'), azure_data)
                return Response({
                        "message":"Request failed" ,
                    }, status=status.HTTP_400_BAD_REQUEST)



class RepriceValidationView(CreateAPIView):
    serializer_class = RepriceValidationSerializer
    azure_obj = AzureBlob()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            azure_data = []
            data = serializer.validated_data
            str_data=json.dumps(request.data)
            req_api = API_data(str_data,'Revalidation','U2S','request')
            azure_data.append(req_api)
            config = data.get('MysAzureConfig')
            cache_stored_date_time = data.get("CacheStoredDateTime")
            data["CacheStoredDateTime"] = str(cache_stored_date_time)
            try:
                flight_revalidate_data,card_request,card_response,logs = RepriceValidationAutomation(request.data).revalidation_automation()

                if settings.IS_LOG_ENABLED :
                    log_data = API_data(str(logs),"Revalidation APIs","U2S","Response")
                    azure_data.append(log_data)
                str_res = json.dumps(flight_revalidate_data)
                res_api = API_data(str_res,'Revalidation','U2S','response')
                azure_data.append(res_api)
                if settings.IS_LOG_ENABLED:
                    self.azure_obj.upload_data_to_blob_storage(config, data.get('SearchIdentifier'), azure_data)
                return Response(flight_revalidate_data)
            except Exception as e:
                screen_name = 'Easyjet Revalidation API'
                if settings.IS_KIBANA_ENABLED:
                    send_error_mail(data.get('SearchIdentifier'), screen_name, e)
                res_api = API_data(str(e),'Revalidation','U2S','response')
                azure_data.append(res_api)
                if settings.IS_LOG_ENABLED:
                    self.azure_obj.upload_data_to_blob_storage(config, data.get('SearchIdentifier'), azure_data)
                return Response({
                    "message":"Request failed" 
                }, status=status.HTTP_400_BAD_REQUEST)


class BookingFlightView(CreateAPIView):
    serializer_class = BookingSerializer
    azure_obj = AzureBlob()
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)   
        if serializer.is_valid():
            data = serializer.validated_data
            config = data.get('MysAzureConfig')
            str_data=json.dumps(data)
            req_api = API_data(str_data,'booking','U2S','request')
            azure_data = [req_api]
            try:
                message_response,response = Scraping.call_scraping_functions(self,data)
                if message_response:
                    res_api = API_data(str(response),'booking','U2S','response')
                    azure_data.append(res_api)
                    if settings.IS_LOG_ENABLED:
                        self.azure_obj.upload_data_to_blob_storage(config, data.get('SearchIdentifier'), azure_data)
                    return Response(message_response,status=status.HTTP_400_BAD_REQUEST)
                else:
                    res_api = API_data(str(response),'booking','U2S','response')
                    azure_data.append(res_api)
                    if settings.IS_LOG_ENABLED:
                        self.azure_obj.upload_data_to_blob_storage(config, data.get('SearchIdentifier'), azure_data)
                    return Response(response)
            except Exception as e:
                print(e)
                res_api = API_data(str(e),'booking','U2S','response')
                azure_data.append(res_api)
                if settings.IS_LOG_ENABLED:
                    self.azure_obj.upload_data_to_blob_storage(config, data.get('SearchIdentifier'), azure_data)
                return Response({
                    "Message":"Request Failed",
                    "BookStatus":2
                },status=status.HTTP_400_BAD_REQUEST)

            
            # try:
            #     response,message,developer_message,booking_status,error, card_request_data, card_details = BookingAutomation().booking_automation(data)

            #     res_api = API_data(str(card_request_data),'cardbook','U2S','request')

            #     azure_data.append(res_api)
            #     res_api = API_data(str(card_details),'cardbook','U2S','response')

            #     azure_data.append(res_api)                

            #     str_res = json.dumps(response)



            # except Exception as e:
            #     print(e)
            #     screen_name = "Booking"
            #     easyjet_error_email(driver, search, screen_name, e,request_data=None)
            #     print("mail sent >>>>")                
            #     err_msg = str(e)
            #     print(err_msg)
            #     err_api = API_data(err_msg, 'booking', 'U2S', 'response')
            #     azure_data.append(err_api)
            #     self.azure_obj.upload_data_to_blob_storage(config, data.get('SearchIdentifier'), azure_data)
            #     return Response({"message":"Request was failed"},
            #                      status=status.HTTP_400_BAD_REQUEST)
            # if error:
            #     response['Message']=developer_message
            #     str_res = json.dumps(response)
            #     book_err_api = API_data(str_res, 'booking', 'U2S', 'response')
            #     azure_data.append(book_err_api)
            #     self.azure_obj.upload_data_to_blob_storage(config, data.get('SearchIdentifier'), azure_data)
            #     data ={
            #         "Message":message,
            #         "BookStatus":booking_status
            #     }
            #     return Response(data,status=status.HTTP_400_BAD_REQUEST)



            # if booking_status==2:
            #     response['Message']=developer_message
            #     str_res = json.dumps(response)
            #     book_err_api = API_data(str_res, 'booking', 'U2S', 'response')
            #     azure_data.append(book_err_api)
            #     self.azure_obj.upload_data_to_blob_storage(config, data.get('SearchIdentifier'), azure_data)
            #     data ={
            #         "Message":message,
            #         "BookStatus":booking_status
            #     }
            #     return Response(data,status=status.HTTP_400_BAD_REQUEST)

            # res_api = API_data(str_res,'booking','U2S','response')
            # azure_data.append(res_api)
            # self.azure_obj.upload_data_to_blob_storage(config,data.get('SearchIdentifier'),azure_data)

            # return Response(response)






# class RepriceValidationView(CreateAPIView):
#     serializer_class = RepriceValidationSerializer
#     azure_obj = AzureBlob()

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         if serializer.is_valid():
#             azure_data = []
#             data = serializer.validated_data
#             str_data=json.dumps(request.data)
#             req_api = API_data(str_data,'Revalidation','U2S','request')
#             azure_data.append(req_api)
#             config = data.get('MysAzureConfig')
#             cache_stored_date_time = data.get("CacheStoredDateTime")
#             data["CacheStoredDateTime"] = str(cache_stored_date_time)
#             try:
#                 flight_revalidate_data,card_request,card_response,logs = RepriceValidationAutomation(request.data).revalidation_automation()

#                 if settings.IS_LOG_ENABLED :
#                     log_data = API_data(str(logs),"Revalidation APIs","U2S","Response")
#                     azure_data.append(log_data)

#                 card_req_api = API_data(str(card_request),'cardsearch','U2S','request')
#                 card_res_api = API_data(str(card_response),'cardsearch','U2S','response')
#                 azure_data.append(card_req_api)
#                 azure_data.append(card_res_api)

#                 str_res = json.dumps(flight_revalidate_data)
#                 res_api = API_data(str_res,'Revalidation','U2S','response')
#                 azure_data.append(res_api)
#                 self.azure_obj.upload_data_to_blob_storage(config, data.get('SearchIdentifier'), azure_data)
#                 return Response(flight_revalidate_data)
#             except Exception as e:
#                 screen_name = 'Easyjet Revalidation API'
#                 if settings.IS_KIBANA_ENABLED:
#                     easyjet_error_email(data.get('SearchIdentifier'), screen_name, e)
#                 res_api = API_data(str(e),'Revalidation','U2S','response')
#                 azure_data.append(res_api)
#                 self.azure_obj.upload_data_to_blob_storage(config, data.get('SearchIdentifier'), azure_data)
#                 return Response({
#                     "message":"Request failed" 
#                 }, status=status.HTTP_400_BAD_REQUEST)

# class BookingView(CreateAPIView):
#     serializer_class = BookingSerializer
#     azure_obj = AzureBlob()
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         azure_data = []

#         if serializer.is_valid():
#             str_data=json.dumps(request.data)
#             req_api = API_data(str_data,'Booking','U2S','request')
#             azure_data.append(req_api)
#             config = request.data["MysAzureConfig"]
#             search_id = request.data['SearchIdentifier']
#             # try:
#             booking_obj = BookingAutomation(request.data)
#             response,card_details,card_request_data,logs,message = booking_obj.generate_booking_request_response()

#             if settings.IS_LOG_ENABLED :
#                 log_data = API_data(str(logs),"Booking APIs","U2S","Response")
#                 azure_data.append(log_data)
#                 str_res = json.dumps(response)
#             if len(card_request_data):
#                 card_req_api = API_data(str(card_request_data),'cardbook','U2S','request')
#                 card_res_api = API_data(str(card_details),'cardbook','U2S','response')
#                 azure_data.append(card_req_api)
#                 azure_data.append(card_res_api)
#             res_api = API_data(str_res,'Booking','U2S','response')
#             azure_data.append(res_api)
#             self.azure_obj.upload_data_to_blob_storage(config, search_id, azure_data)
#             if response["BookStatus"] == 2:

#                 return Response({
#                     "Message":message,
#                     "BookStatus" : response["BookStatus"]
#                 })

#             return Response(response)
                
#             # except Exception as e:
#             #     print(e)
#             #     screen_name = 'Easyjet Booking API'
#             #     if settings.IS_KIBANA_ENABLED:
#             #         easyjet_error_email(request.data.get('SearchIdentifier'), screen_name, e)
#             #     res_api = API_data(str(e),'Booking','U2S','response')
#             #     azure_data.append(res_api)
#             #     self.azure_obj.upload_data_to_blob_storage(config, search_id, azure_data)

#             #     return Response({
#             #         "message":"Request failed" 
#             #     }, status=status.HTTP_400_BAD_REQUEST)
            
            
            
