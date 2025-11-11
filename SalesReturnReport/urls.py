from django.urls import path
from .views import get_sales_return_data

urlpatterns = [
    path('get-data/', get_sales_return_data, name='get_sales_return_data'),
]
