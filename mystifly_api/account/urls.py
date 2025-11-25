from django.urls import path
from account.views import SubscriberCreateView


urlpatterns = [
    path('subscriber', SubscriberCreateView.as_view(), name="subscriber_create_api")
]
