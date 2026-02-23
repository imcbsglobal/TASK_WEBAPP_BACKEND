from django.urls import path
from .views import tender_cash_by_user

urlpatterns = [
    path('tender-cash-by-user/', tender_cash_by_user),
]