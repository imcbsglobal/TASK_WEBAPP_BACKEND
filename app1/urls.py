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
    get_cash_ledger_details,
    get_sale_report,
    dashboard_total_expenses,
    dashboard_total_income,
    dashboard_budget_remaining,
    dashboard_active_users,
    dashboard_category_breakdown,
    dashboard_expense_trends,
    dashboard_recent_transactions,
    dashboard_recent_purchases,
    dashboard_total_sales,
    dashboard_total_expense,
    dashboard_payment_sent,
    dashboard_payment_received,
    dashboard_sales_purchases,
    dashboard_recent_invoices,
    dashboard_stock_history
)


urlpatterns = [
    path('login/',      login,      name='login'),
    path('get-users/',  get_users,  name='get_users'),
    path('get-misel-data/', get_misel_data, name='get_misel_data'),
    path('test-token/', test_token, name='test_token'),
    path('get-debtors-data/',   get_debtors_data,   name='get_debtors_data'),
    path('get-ledger-details/', get_ledger_details, name='get_ledger_details'),
    path('get-invoice-details/', get_invoice_details, name='get_invoice_details'),
    path('get-sale-report/', get_sale_report, name='get_sale_report'),
    path('get-cash-book-data/',  get_cash_book_data,  name='get_cash_book_data'),
    path('get-bank-book-data/',  get_bank_book_data,  name='get_bank_book_data'),
    path('get-cash-ledger-details/', get_cash_ledger_details, name='get_cash_ledger_details'),
    path('get-bank-ledger-details/', get_bank_ledger_details, name='get_bank_ledger_details'),
    path('dashboard/total-expenses/', dashboard_total_expenses, name='dashboard_total_expenses'),
    path('dashboard/total-income/', dashboard_total_income, name='dashboard_total_income'),
    path('dashboard/budget-remaining/', dashboard_budget_remaining, name='dashboard_budget_remaining'),
    path('dashboard/active-users/', dashboard_active_users, name='dashboard_active_users'),
    path('dashboard/category-breakdown/', dashboard_category_breakdown, name='dashboard_category_breakdown'),
    path('dashboard/expense-trends/', dashboard_expense_trends, name='dashboard_expense_trends'),
    path('dashboard/recent-transactions/', dashboard_recent_transactions, name='dashboard_recent_transactions'),
    path('dashboard/recent-purchases/', dashboard_recent_purchases, name='dashboard_recent_purchases'),
    path('dashboard/total-sales/', dashboard_total_sales, name='dashboard_total_sales'),
    path('dashboard/total-expense/', dashboard_total_expense, name='dashboard_total_expense'),
    path('dashboard/payment-sent/', dashboard_payment_sent, name='dashboard_payment_sent'),
    path('dashboard/payment-received/', dashboard_payment_received, name='dashboard_payment_received'),
    path('dashboard/sales-purchases/', dashboard_sales_purchases, name='dashboard_sales_purchases'),
    path('dashboard/recent-invoices/', dashboard_recent_invoices, name='dashboard_recent_invoices'),
    path('dashboard/stock-history/', dashboard_stock_history, name='dashboard_stock_history'),
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