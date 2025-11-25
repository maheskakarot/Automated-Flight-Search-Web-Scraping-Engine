from rest_framework import serializers
from account.models import Subscriber, User
from rest_framework.authtoken.models import Token


class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        fields = ('country_code', 'mobile')

    def create(self, validated_data):
        mobile = validated_data.get('mobile')
        country_code = validated_data.get('country_code')
        user = User.objects.create(username=mobile, user_type=User.SUBSCRIBER)
        token = Token.objects.create(user=user)
        subscriber = Subscriber.objects.create(
            user=user,
            country_code=country_code,
            mobile=mobile
        )
        return subscriber
