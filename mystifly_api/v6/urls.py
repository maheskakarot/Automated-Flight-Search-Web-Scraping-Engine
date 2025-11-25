from django.urls import path, include

urlpatterns = [
    path('ryanair/', include('v6.ryanair.urls')),
]