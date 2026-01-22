from django.urls import path
from .views import get_tendercash

urlpatterns = [
    path('get-tendercash/', get_tendercash, name='get_tendercash'),
]