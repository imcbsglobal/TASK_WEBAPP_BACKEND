from django.urls import path
from .views import get_stock_report

urlpatterns = [
    path('get-stock-report/', get_stock_report, name='get_stock_report'),
]
