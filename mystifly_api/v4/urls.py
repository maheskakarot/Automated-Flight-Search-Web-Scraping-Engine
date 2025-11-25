from django.urls import path, include

urlpatterns = [
    path('ryanair/', include('v4.ryanair.urls')),
]
