from django.urls import path
from . import views

urlpatterns = [
    path('salestoday/', views.get_sales_today, name='get_sales_today'),
    path('purchasetoday/', views.get_purchase_today, name='get_purchase_today'),
    path('salesdaywise/', views.get_sales_daywise, name='get_sales_daywise'),
    path('salesmonthwise/', views.get_sales_monthwise, name='get_sales_monthwise'),
]
