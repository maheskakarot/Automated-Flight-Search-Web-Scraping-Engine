import uuid
from django.db import models
from utils.models import TimeStampedModel
from django.contrib.auth.models import AbstractUser

class AdminCookies(TimeStampedModel):

    user_email = models.CharField(max_length=255, unique=True)
    cookies = models.TextField(null=True)


class WebdriverLifeManager(TimeStampedModel):

    expire_after = models.PositiveIntegerField(default=8)

    def __str__(self):
        return "Close after - {} minutes".format(self.expire_after)

class User(AbstractUser, TimeStampedModel):

    ADMIN = 'admin'
    SUBSCRIBER = 'subscriber'

    USER_TYPE = (
        (ADMIN, 'admin'),
        (SUBSCRIBER, 'subscriber'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    user_type = models.CharField(max_length=25, choices=USER_TYPE, default=SUBSCRIBER)
    is_active = models.BooleanField(default=True)

class Subscriber(TimeStampedModel):

    id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscriber')
    country_code = models.CharField(max_length=4)
    mobile = models.CharField(max_length=12, unique=True)

    def __str__(self):
        return f"{self.country_code}{self.mobile}"

class SubscriberWebDriver(TimeStampedModel):

    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE, related_name='subscriber')
    url = models.URLField(null=True)
    session_id = models.CharField(max_length=255)
    reuse_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "Created on - {}, Mobile - {}, Url - {}, Reuse Count - {}, Updated on - {}, Active - {}".format(
            self.created_on.time(), self.subscriber.mobile, self.url, self.reuse_count, self.updated_on.time(), self.is_active)


# TODO: Will add more info related to user history in future.
class SubscriberSearchHistory(TimeStampedModel):

    SEARCH_SCREEN = "search"
    REPRICE_SCREEN = "reprice"
    INITIATE_BOOKING = "initiate_booking"
    SEAT_SELECTION_SCREEN = "seat_selection"
    BAGGAGES_SCREEN = "baggages"
    LOGIN_SCREEN = "login"
    PAYMENT_SCREEN = "payment"
    RETRIEVE_BOOKING_SCREEN = "retrieve"

    SCREENS = (
        (SEARCH_SCREEN, 'search'),
        (REPRICE_SCREEN, 'reprice'),
        (INITIATE_BOOKING, 'initiate_booking'),
        (SEAT_SELECTION_SCREEN, 'seat_selection'),
        (BAGGAGES_SCREEN, 'baggages'),
        (LOGIN_SCREEN, 'login'),
        (PAYMENT_SCREEN, 'payment'),
        (RETRIEVE_BOOKING_SCREEN, 'retrieve'),
    )

    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE, related_name='subscriber_search_history')
    adult = models.IntegerField(default=0)
    teen = models.IntegerField(default=0)
    child = models.IntegerField(default=0)
    infant = models.IntegerField(default=0)
    current_screen = models.CharField(max_length=255, choices=SCREENS, default=SEARCH_SCREEN)
    url = models.TextField(null=True)
    website_url = models.TextField(null=True)