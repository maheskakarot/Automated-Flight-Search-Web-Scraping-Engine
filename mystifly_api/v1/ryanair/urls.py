from django.urls import path
from v1.ryanair.views import AirportSearchView, SearchFlightView, RepriceValidationView, InitiateBooking, \
    SeatSelection, BaggagesSelection, LoginView, SubmitConfirmationCode, PaymentView
from v1.ryanair.views.retrieve_booking import RetrieveBookingLoginView, RetrieveBookingView

urlpatterns = [
    path('search/airport', AirportSearchView.as_view(), name="airport_search_api"),
    path('search/flights', SearchFlightView.as_view(), name="flight_search_api"),
    path('reprice/validation', RepriceValidationView.as_view(), name="reprice_validation"),
    path('booking/initiate', InitiateBooking.as_view(), name="booking_initiate"),
    path('booking/seat-selection', SeatSelection.as_view(), name="seat_selection"),
    path('booking/baggages-selection', BaggagesSelection.as_view(), name="baggages_selection"),
    path('login', LoginView.as_view(), name="login"),
    path('login/submit-code', SubmitConfirmationCode.as_view(), name="submit_confirmation_code"),
    path('payment/initiate', PaymentView.as_view(), name="payment_initiate"),
    path('retrieve_booking/login', RetrieveBookingLoginView.as_view(), name="retrieve_booking_login"),
    path('retrieve_booking', RetrieveBookingView.as_view(), name="retrieve_booking"),
]
