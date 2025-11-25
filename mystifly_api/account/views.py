from rest_framework import generics, status
from utils.restful_response import send_response
from .models import Subscriber
from .serializers import SubscriberSerializer
from .authentication import token_expire_handler


class SubscriberCreateView(generics.CreateAPIView):
    """
    We'll be using this view to generate or retrieve token of subscriber using country_code and mobile number.
    Token will be used in other APIs to identify users.
    """
    serializer_class = SubscriberSerializer

    def create(self, request, *args, **kwargs):
        mobile = request.data.get('mobile')
        country_code = request.data.get('country_code')

        subscriber_obj = Subscriber.objects.filter(country_code=country_code, mobile=mobile).first()
        if subscriber_obj:
            token = subscriber_obj.user.auth_token
            is_expired, token = token_expire_handler(token)
            token = token.key

            return send_response(status=status.HTTP_200_OK,
                                 data={'token': token},
                                 developer_message="Subscriber was already exists")

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            return send_response(status=status.HTTP_201_CREATED,
                                 data={'token': instance.user.auth_token.key},
                                 developer_message="Subscriber created successfully")

        else:
            return send_response(status=status.HTTP_200_OK,
                                 error=serializer.errors,
                                 developer_message="Something went wrong")
