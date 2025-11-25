from django.urls import path, include

urlpatterns = [
    path('ryanair/', include('v1.ryanair.urls')),
]
