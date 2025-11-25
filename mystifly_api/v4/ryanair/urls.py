from django.urls import path
from v4.ryanair.views import SearchFlightView


urlpatterns = [
    path('search/flights', SearchFlightView.as_view()),
]
