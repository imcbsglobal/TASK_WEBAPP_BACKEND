from django.urls import path
from . import views

urlpatterns = [
    path('get_sales_today_usersummary/', views.get_sales_today_usersummary, name='get_sales_today_usersummary'),
    path('purchasetoday/', views.get_purchase_today, name='get_purchase_today'),
    path('salesdaywise/', views.get_sales_daywise, name='get_sales_daywise'),
    path('salesmonthwise/', views.get_sales_monthwise, name='get_sales_monthwise'),
    path('get-sale-report/', views.get_sale_report, name='get_sale_report'),
    path('salestoday-usersummary/', views.get_sales_today_usersummary, name='get_sales_today_usersummary'),
    path('salestoday-typewise/', views.get_sales_today_typewise, name='get_sales_today_typewise'),
    path('salestoday-details/', views.get_sales_today_details, name='get_sales_today_details'),
]
# s