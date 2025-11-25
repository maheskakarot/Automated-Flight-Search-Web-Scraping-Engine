from rest_framework import serializers
from v1.ryanair.models import Airport


class AirportSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()

    class Meta:
        model = Airport
        fields = ('id', 'name', 'country', 'code')

    def get_country(self, obj):
        return obj.country.name

