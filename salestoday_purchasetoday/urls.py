from django.urls import path
from . import views

urlpatterns = [
    # SALES
    path('salestoday/', views.get_sales_today, name='get_sales_today'),
    path('salesdaywise/', views.get_sales_daywise, name='get_sales_daywise'),
    path('salesmonthwise/', views.get_sales_monthwise, name='get_sales_monthwise'),

    # PURCHASE ✅
    path('purchasetoday/', views.get_purchase_today, name='get_purchase_today'),
    path('purchasemonth/', views.get_purchase_month, name='get_purchase_month'),
    path('purchaseoverall/', views.get_purchase_overall, name='get_purchase_overall'),
]
