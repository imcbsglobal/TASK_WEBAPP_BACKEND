from django.urls import path
from .views import login, get_users,get_misel_data,test_token


urlpatterns = [
    path('login/',      login,      name='login'),
    path('get-users/',  get_users,  name='get_users'),
    path('get-misel-data/', get_misel_data, name='get_misel_data'),
    path('test-token/', test_token, name='test_token'),
]