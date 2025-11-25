from django.urls import path, include

urlpatterns = [
    path('ryanair/', include('v5.ryanair.urls')),
]
