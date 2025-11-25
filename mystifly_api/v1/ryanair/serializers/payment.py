from rest_framework import serializers


class PaymentSerializer(serializers.Serializer):
    ResultId = serializers.CharField(max_length=255)
    CountryCode = serializers.CharField()
    ContactNumber = serializers.CharField()
    CreditCardInfo = serializers.JSONField()
    AddressInfo = serializers.JSONField()
    FareDetails = serializers.JSONField()
