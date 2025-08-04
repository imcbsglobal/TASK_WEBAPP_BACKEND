from django.urls import path
from .views import login, get_users,get_misel_data,test_token,get_debtors_data


urlpatterns = [
    path('login/',      login,      name='login'),
    path('get-users/',  get_users,  name='get_users'),
    path('get-misel-data/', get_misel_data, name='get_misel_data'),
    path('test-token/', test_token, name='test_token'),
    path('get-debtors-data/', get_debtors_data, name='get_debtors_data'),  # Add this line
]