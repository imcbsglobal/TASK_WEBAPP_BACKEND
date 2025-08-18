from django.urls import path
from .views import login, get_users,get_misel_data,test_token,get_debtors_data
from django.urls import path
from .views import (
    login, 
    get_users, 
    get_misel_data, 
    test_token, 
    get_debtors_data,
    get_ledger_details,
    get_invoice_details,
    get_cash_book_data,
    get_bank_book_data,
    get_bank_ledger_details,
    get_cash_ledger_details
)


urlpatterns = [
    path('login/',      login,      name='login'),
    path('get-users/',  get_users,  name='get_users'),
    path('get-misel-data/', get_misel_data, name='get_misel_data'),
    path('test-token/', test_token, name='test_token'),
    path('get-debtors-data/',   get_debtors_data,   name='get_debtors_data'),
    path('get-ledger-details/', get_ledger_details, name='get_ledger_details'),
    path('get-invoice-details/', get_invoice_details, name='get_invoice_details'),

    path('get-cash-book-data/',  get_cash_book_data,  name='get_cash_book_data'),
    path('get-bank-book-data/',  get_bank_book_data,  name='get_bank_book_data'),
    path('get-cash-ledger-details/', get_cash_ledger_details, name='get_cash_ledger_details'),
    path('get-bank-ledger-details/', get_bank_ledger_details, name='get_bank_ledger_details'),
]



# http://127.0.0.1:8000/api/login/


# {
#     "username": "ARUN",
#     "password": "Ford@123##",
#     "client_id": "SYSMAC"
    
# }

# {
#     "success": true,
#     "user": {
#         "username": "ARUN",
#         "role": "User",
#         "client_id": "SYSMAC",
#         "accountcode": "ACASH",
#         "login_time": "2025-08-16 16:41:14"
#     },
#     "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiQVJVTiIsInVzZXJuYW1lIjoiQVJVTiIsImNsaWVudF9pZCI6IlNZU01BQyIsInJvbGUiOiJVc2VyIiwiYWNjb3VudGNvZGUiOiJBQ0FTSCIsImV4cCI6MTc1NTQyOTA3NCwiaWF0IjoxNzU1MzQyNjc0fQ.wt5-jCNe5cQYOmbnBgjUdMSVo37j5VchBhuDGETSGF4"
# }