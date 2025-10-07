from django.urls import path
from .views import get_debtors_list

urlpatterns = [
    path('get-debtors/', get_debtors_list, name='get_debtors_list'),
]