# SalesReturnReport/models.py
from django.db import models


class SalesReturnReport(models.Model):
    """
    Sales Return Report table - fetches data from acc_invoicereturn
    Shows sales return transactions
    """
    id = models.AutoField(primary_key=True)
    date = models.DateField(blank=True, null=True)
    invno = models.IntegerField(blank=True, null=True)
    net = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True)
    customername = models.CharField(max_length=250, blank=True, null=True)
    userid = models.CharField(max_length=13, blank=True, null=True)
    client_id = models.CharField(max_length=100)

    class Meta:
        db_table = 'salesreturn_report'
        managed = False  # Table already exists in PostgreSQL
        indexes = [
            models.Index(fields=['client_id', 'date']),
            models.Index(fields=['invno']),
        ]

    def __str__(self):
        return f"Sales Return {self.invno} - {self.customername}"
    









# API Endpoints Testing Examples

# 1. Get Sales Return Report (with pagination)
# GET http://127.0.0.1:8000/api/sales-return/get-sales-return-report/
# Headers:
#   Authorization: Bearer YOUR_JWT_TOKEN

# Query Parameters:
#   ?page=1&page_size=20

# Example Response:
# {
#     "success": true,
#     "data": [
#         {
#             "date": "2025-11-11",
#             "invno": 105,
#             "net": "2100.000",
#             "customername": "CUSTOMER ONE - SAMPLE",
#             "userid": "-555"
#         },
#         {
#             "date": "2025-11-11",
#             "invno": 106,
#             "net": "3200.000",
#             "customername": "CUSTOMER TWO - SAMPLE",
#             "userid": "-555"
#         }
#     ],
#     "pagination": {
#         "current_page": 1,
#         "total_pages": 1,
#         "total_records": 5,
#         "page_size": 20,
#         "has_next": false,
#         "has_previous": false
#     },
#     "search_applied": false,
#     "search_term": ""
# }


# 2. Get Sales Return Report with Search
# GET http://127.0.0.1:8000/api/sales-return/get-sales-return-report/?search=CUSTOMER
# Headers:
#   Authorization: Bearer YOUR_JWT_TOKEN


# 3. Get Specific Sales Return Details
# GET http://127.0.0.1:8000/api/sales-return/get-sales-return-details/?invno=105
# Headers:
#   Authorization: Bearer YOUR_JWT_TOKEN

# Example Response:
# {
#     "success": true,
#     "data": {
#         "date": "2025-11-11",
#         "invno": 105,
#         "net": "2100.000",
#         "customername": "CUSTOMER ONE - SAMPLE",
#         "userid": "-555"
#     }
# }