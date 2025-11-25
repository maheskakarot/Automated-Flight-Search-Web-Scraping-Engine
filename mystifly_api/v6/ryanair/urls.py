from django.urls import path
from v6.ryanair.views.booking import BookingAPIView

urlpatterns = [
    path('Book', BookingAPIView.as_view()),
]
