from django.urls import path
from .views import get_pdc

urlpatterns = [
    path('get-pdc/', get_pdc, name='get_pdc'),
]
