from rest_framework import serializers


class InitiateBookingSerializer(serializers.Serializer):
    ResultId = serializers.CharField(max_length=255)
    PassengersDetails = serializers.JSONField()
    FareDetails = serializers.JSONField()
    Address = serializers.CharField()
    City = serializers.CharField()
    Country = serializers.CharField()
    PostCode = serializers.CharField()
    CountryCode = serializers.CharField()
    ContactNumber = serializers.CharField()
