from django.contrib import admin
from .models import Subscriber, User, SubscriberWebDriver, SubscriberSearchHistory, \
    AdminCookies, WebdriverLifeManager

# Register your models here.
admin.site.register(Subscriber)
admin.site.register(SubscriberWebDriver)
admin.site.register(SubscriberSearchHistory)
admin.site.register(User)
admin.site.register(AdminCookies)
admin.site.register(WebdriverLifeManager)
