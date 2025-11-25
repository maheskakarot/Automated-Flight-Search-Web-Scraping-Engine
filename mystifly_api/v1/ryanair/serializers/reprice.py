from rest_framework import serializers


class RepriceValidationSerializer(serializers.Serializer):
    ResultId = serializers.CharField(max_length=255)
    FareDetails = serializers.JSONField()
