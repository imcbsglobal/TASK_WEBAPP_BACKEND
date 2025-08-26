from django.urls import path
from .views import shop_location, get_firms

urlpatterns = [
    path('shop-location/', shop_location, name='shop_location'),
    path('shop-location/firms/', get_firms, name='get_firms'),
]