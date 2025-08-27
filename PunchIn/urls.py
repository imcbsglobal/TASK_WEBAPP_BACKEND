from django.urls import path
from .views import shop_location, get_firms,get_table_data,update_location_status

urlpatterns = [
    path('shop-location/', shop_location, name='shop_location'),
    path('shop-location/firms/', get_firms, name='get_firms'),
    path('shop-location/table/',get_table_data,name='get_table_data'),
    path('shop-location/status/',update_location_status , name='update_location_status')
]