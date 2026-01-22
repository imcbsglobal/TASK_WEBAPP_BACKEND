from django.urls import path
from .views import get_acc_sales_types

urlpatterns = [
    path('get-acc-sales-types/', get_acc_sales_types, name='get_acc_sales_types'),
]
