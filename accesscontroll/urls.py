from django.urls import path
from .views import update_user_menu

urlpatterns = [
    path('update-menu/',update_user_menu ,name='update_menu')
]
