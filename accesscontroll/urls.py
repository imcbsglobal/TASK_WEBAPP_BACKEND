from django.urls import path
from .views import update_user_menu,get_user_menus

urlpatterns = [
    path('update-menu/',update_user_menu ,name='update_menu'),
    path('get-user-menus/', get_user_menus ,name='get_user_menus')
]
