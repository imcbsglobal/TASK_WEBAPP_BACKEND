from django.urls import path
from .views import get_stock_summary

urlpatterns = [
    path('stock-summary/', get_stock_summary, name='get_stock_summary'),
]