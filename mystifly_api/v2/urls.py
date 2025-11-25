from django.urls import path, include

urlpatterns = [
    path('ryanair/', include('v2.ryanair.urls')),
]
