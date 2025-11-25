from rest_framework import serializers

class FlightSearchSerializer(serializers.Serializer):
    OriginDestinationInformations = serializers.JSONField()
    TravelPreferences = serializers.JSONField()
    PassengerTypeQuantities = serializers.JSONField()
    PricingSourceType = serializers.IntegerField(allow_null=True)
    NearByAirports = serializers.BooleanField()
    BillingEntity = serializers.CharField(allow_blank=True)
    MysCardConfig = serializers.CharField(allow_blank=True)
    MysRedisConfig = serializers.CharField(allow_blank=True)
    MysAzureConfig = serializers.CharField(allow_blank=True)
    SupplierCode = serializers.CharField(allow_blank=True)
    SearchIdentifier = serializers.CharField()
    CurrencyCode = serializers.CharField(allow_blank=True)
    ClientId = serializers.CharField(allow_blank=True, allow_null = True)
    MemberId = serializers.CharField(allow_blank=True, allow_null = True)
    IsLogEnabled = serializers.BooleanField()
    IsClientConfigActive = serializers.BooleanField()


# Reval serializer
class RepriceValidationSerializer(serializers.Serializer):
    ListFlightSearchResult = serializers.ListField()
    ClientConfig = serializers.CharField(allow_blank=True, allow_null=True)
    MysCardConfig = serializers.CharField(allow_blank=True, allow_null=True)
    MysRedisConfig = serializers.CharField(allow_blank=True, allow_null=True)
    MysAzureConfig = serializers.CharField()
    BillingEntity = serializers.CharField()
    CardType = serializers.CharField(allow_blank=True, allow_null=True)
    Nationality = serializers.CharField(allow_blank=True, allow_null=True)
    IsClientConfigActive = serializers.BooleanField()
    SearchIdentifier = serializers.CharField()
    Origin = serializers.CharField()
    Destination = serializers.CharField()
    TravelDate = serializers.CharField()
    ReturnDate = serializers.DateField(required=False)
    TravelType = serializers.IntegerField()
    ResultStatus = serializers.BooleanField()
    SupplierCode = serializers.CharField()
    Message = serializers.CharField(required=False,allow_blank=True, allow_null=True)
    AccountId = serializers.IntegerField()
    AccountNumber = serializers.CharField()


class BookingSerializer(serializers.Serializer):
    
    BillingEntity = serializers.CharField()
    ClientConfig = serializers.CharField(allow_blank=True, allow_null=True)
    MysCardConfig = serializers.CharField()
    MysRedisConfig = serializers.CharField(allow_blank=True, allow_null=True)
    MysAzureConfig = serializers.CharField()
    SupplierRefNo=serializers.CharField(allow_blank=True, allow_null=True)
    ListPassengers = serializers.JSONField()
    ListFlightSegments = serializers.JSONField()
    ListBookFlightFare = serializers.JSONField()
    TotalFare = serializers.FloatField()
    ToleranceAmount = serializers.FloatField()
    SupplierCode = serializers.CharField()
    SearchIdentifier = serializers.CharField()
    IsLCCBlockItin = serializers.BooleanField()
    AccountId = serializers.IntegerField()
    BookRef = serializers.IntegerField()
    AirTripType = serializers.IntegerField()
    Remarks = serializers.JSONField()
    BaseCurrency = serializers.CharField()
    IsPrepay = serializers.BooleanField()
    IsClientConfigActive = serializers.BooleanField()
    PCCDetails = serializers.CharField(allow_null=True)
    AccountNumber = serializers.CharField()






