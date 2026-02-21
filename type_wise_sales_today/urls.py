from django.urls import path
from .views import type_wise_sales_today

urlpatterns = [
    path('type-wise-sales-today/', type_wise_sales_today),
]