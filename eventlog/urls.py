from django.urls import path
from .views import get_eventlog

urlpatterns = [
    path('get-eventlog/', get_eventlog, name='get_eventlog'),
]