from django.urls import path, include

urlpatterns = [
    path('ryanair/', include('v3.ryanair.urls')),
]
