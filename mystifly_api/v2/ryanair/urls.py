from django.urls import path

from v2.ryanair.views.equipments import EquipmentRetrieve, EquipmentSelection
from v1.ryanair.views import AirportSearchView, PaymentView, RetrieveBookingLoginView, RetrieveBookingView
from v2.ryanair.views import BaggagesSelection, SeatSelection, RetrieveFastTrackInfoView, AddFastTrackView, \
    InitiateBooking, BaggagesInfoView, SelectBaggagesView, RepriceValidationView, LoginView, SubmitConfirmationCode, \
    SearchFlightView
from v2.ryanair.views.search import SearchFlightUpdatedView 
from v2.ryanair.views.ip_address_info import IpAddressRetrieve
from v2.ryanair.views.reissuance import ReissuanceFlightSearchView, ReissuancePriceVariationView, \
    ReissuanceInitiatePaymentView, ReissuancePrintReceiptView

urlpatterns = [
    path('search/airport', AirportSearchView.as_view(), name="airport_search_api"),
    path('search/flights', SearchFlightView.as_view(), name="flight_search_api"),
    path('search/flights/new', SearchFlightUpdatedView.as_view(),name="flight_search_updated_api"),
    path('reprice/validation', RepriceValidationView.as_view(), name="reprice_validation"),
    path('booking/initiate', InitiateBooking.as_view(), name="booking_initiate"),
    path('booking/seat-selection', SeatSelection.as_view(), name="seat_selection"),
    path('booking/baggages-selection', BaggagesSelection.as_view(), name="baggages_selection"),
    path('booking/baggages/list', BaggagesInfoView.as_view(), name="baggages_info"),
    path('booking/baggages/select', SelectBaggagesView.as_view(), name="baggages_select"),
    path('booking/fast-track/list', RetrieveFastTrackInfoView.as_view(), name="fast_track_info"),
    path('booking/fast-track/add', AddFastTrackView.as_view(), name="fast_track_add"),
    path('login', LoginView.as_view(), name="login"),
    path('login/submit-code', SubmitConfirmationCode.as_view(), name="submit_confirmation_code"),
    path('payment/initiate', PaymentView.as_view(), name="payment_initiate"),
    path('retrieve_booking/login', RetrieveBookingLoginView.as_view(), name="retrieve_booking_login"),
    path('retrieve_booking', RetrieveBookingView.as_view(), name="retrieve_booking"),
    path('reissuance/change_flight/search', ReissuanceFlightSearchView.as_view(), name="reissuance_search_flight"),
    path('reissuance/change_flight/price_difference', ReissuancePriceVariationView.as_view(), name="reissuance_price_difference"),
    path('equipments/retrieve', EquipmentRetrieve.as_view(), name="Equipment Retrieve"),
    path('reissuance/change_flight/initiate_payment', ReissuanceInitiatePaymentView.as_view(), name="reissuance_initiate_payment"),
    path('reissuance/change_flight/print_receipt', ReissuancePrintReceiptView.as_view(), name="reissuance_print_receipt_view"),

    path('equipments/selection', EquipmentSelection.as_view(), name="Equipment Selection"),
    path('ipaddress', IpAddressRetrieve.as_view(), name="Ip Address Retrieval"),


]
