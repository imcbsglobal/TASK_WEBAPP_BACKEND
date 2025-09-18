from django.urls import path
from .views import shop_location, get_firms,get_table_data,update_location_status ,get_upload_signature

urlpatterns = [    
    #Shop Location Management
    path('shop-location/', shop_location, name='shop_location'), #POST shop_location
    path('shop-location/firms/', get_firms, name='get_firms'),
    path('shop-location/table/',get_table_data,name='get_table_data'),
    path('shop-location/status/',update_location_status , name='update_location_status'),

    #Punch In System
    path("punch-in/cloudinary-signature/",get_upload_signature, name="cloudinary-signature")


]