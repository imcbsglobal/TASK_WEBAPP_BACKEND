from django.urls import path
from .views import (
    shop_location, get_firms, get_table_data, update_location_status,
    get_upload_signature, punchin, punchout, get_active_punchin,punchin_table,
    get_areas, update_area, get_user_areas
)

urlpatterns = [    
    #Shop Location Management
    path('shop-location/', shop_location, name='shop_location'), #POST shop_location
    path('shop-location/firms/', get_firms, name='get_firms'),
    path('shop-location/table/',get_table_data,name='get_table_data'),
    path('shop-location/status/',update_location_status , name='update_location_status'),

    #Punch In/Out System
    path("punch-in/cloudinary-signature/", get_upload_signature, name="cloudinary-signature"),
    path("punch-in/", punchin, name="punchin"),
    path("punch-out/<int:id>/", punchout, name="punchout"),
    path("punch-status/", get_active_punchin, name="punch-status"),
    path("punch-in/table/",punchin_table,name='punchin_table'),

    #Area management
    path("get-areas/", get_areas, name="get-areas"),
    path("get-user-area", get_user_areas, name="get_user_area"),
    path("update-area/", update_area, name="update-area"),

]