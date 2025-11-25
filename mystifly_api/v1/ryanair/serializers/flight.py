from rest_framework import serializers
from v1.ryanair.constants.urls import search_url_and_other_req_info, search_url_and_other_req_info_v3


# Flight search serializer
class FlightSearchSerializer(serializers.Serializer):
    OriginDestinationInformations = serializers.JSONField()
    TravelPreferences = serializers.JSONField()
    PassengerTypeQuantities = serializers.JSONField()
    OriginNearByAirports = serializers.BooleanField(default=False)
    DestinationNearByAirports = serializers.BooleanField(default=False)

    # Function will return required data to proceed future with search API
    def get_required_data(self):
        required_data = search_url_and_other_req_info_v3(self.validated_data)
        search_url = None

        adults = required_data.get('adults')
        teens = required_data.get('teens')
        children = required_data.get('children')
        infants = required_data.get('infants')

        total_seats = adults + teens + children + infants

        # Added check if seats count is valid or not
        if total_seats > 9:
            message = "Total seats count should be less than or equal to 9."
            return search_url, message, required_data

        if infants > adults:
            message = "Infants more than adults are not allowed."
            return search_url, message, required_data

        search_url = required_data.get("search_url")
        message = "Url created successfully."
        
        return search_url, message, required_data
