from django.urls import path
from .views import get_type_wise_salestoday

urlpatterns = [
    path('get-type-wise-salestoday/', get_type_wise_salestoday, name='get_type_wise_salestoday'),
]
