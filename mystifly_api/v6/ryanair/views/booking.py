from rest_framework import generics
from v6.ryanair.serializers.booking import BookingSerializer
from django.http import JsonResponse
from django.conf import settings
from v6.ryanair.scripts.booking import BookingAutomation
from rest_framework.permissions import IsAuthenticated
from account.authentication import ExpiringTokenAuthentication
from utils.api_error_logging import send_error_mail

class BookingAPIView(generics.CreateAPIView):
    serializer_class = BookingSerializer
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        try:
            obj = BookingAutomation(request)
            response = obj.booking()
            return JsonResponse(response)
        except Exception as E:
            if settings.IS_KIBANA_ENABLED:
                send_error_mail(request.data['SearchIdentifier'], 'ryanair booking API', str(E), request_data=None)
            print(E)
            return JsonResponse({'message': 'Booking failed',
                                 'Exception': str(E)})

