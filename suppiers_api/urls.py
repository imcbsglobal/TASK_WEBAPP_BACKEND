from django.urls import path
from .views import suppliers_list

urlpatterns = [
    path('suppliers/', suppliers_list, name='suppliers_list'),
]