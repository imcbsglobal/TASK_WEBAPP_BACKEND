from django.urls import path
from .views import tender_cash_bytype

urlpatterns = [
    path('tender-cash-bytype/', tender_cash_bytype),
]