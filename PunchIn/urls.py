from django.urls import path
from .views import punch_in, get_firms

urlpatterns = [
    path('punch-in/', punch_in, name='punch_in'),
    path('punch-in/firms/', get_firms, name='get_firms'),
]