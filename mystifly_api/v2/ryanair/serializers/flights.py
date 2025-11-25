from rest_framework import serializers
    

class FlightSearchUpdatedSerializer(serializers.Serializer):
    adult = serializers.IntegerField(default=1)
    child = serializers.IntegerField(default=0)
    date_in = serializers.DateField(required=False, allow_null=True)
    date_out = serializers.DateField(format="%Y-%m-%d",allow_null=False,required=True)
    destination = serializers.CharField(required=True,max_length=5)
    disc = serializers.IntegerField(default=0)
    infant = serializers.IntegerField(default=0)
    origin = serializers.CharField(required=True,max_length=5)
    teen = serializers.IntegerField(default=0)
    promocode = serializers.CharField(required=False, allow_null=True)
    include_connecting_flights = serializers.BooleanField(default=False)
    flex_days_before_out = serializers.IntegerField(default=2)
    flex_days_out = serializers.IntegerField(default=2)
    flex_days_before_in = serializers.IntegerField(default=2)
    flex_days_in = serializers.IntegerField(default=2)
    round_trip = serializers.BooleanField(default=False)
    to_us = serializers.CharField(default="AGREED",max_length=50)
    
    def validate(self, data):
        passengers = data['adult'] + data['child'] + data['teen']
        if passengers > 25:
            raise serializers.ValidationError(
                {"error": "The maximum number of passengers is 25. If there are more than 25 passengers please use our group booking form."}
            )
        if data['infant'] > 18:
            raise serializers.ValidationError(
                {"error": "Maximum number of infants is 18"}
            )
        if data['date_in']:
            if data['round_trip'] == False:
                raise serializers.ValidationError(
                    {"error": "round_trip field required! because you enter return trip date."}
                )
        if data['round_trip']:
            if data['date_in'] == None:
                raise serializers.ValidationError(
                    {"error": "date_in field required! because you select round_trip."}
                )
        return data