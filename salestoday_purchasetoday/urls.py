from django.urls import path
from . import views

urlpatterns = [
    path('salestoday/', views.get_sales_today, name='get_sales_today'),
    path('purchasetoday/', views.get_purchase_today, name='get_purchase_today'),
]
