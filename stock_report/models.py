from django.db import models

# Create your models here.
from django.db import models

class StockReport(models.Model):
    client_id = models.CharField(max_length=50, db_index=True)

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    productcode = models.CharField(max_length=30)
    barcode = models.CharField(max_length=35, null=True, blank=True)
    bmrp = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    salesprice = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)

    class Meta:
        db_table = "stock_report"

    def __str__(self):
        return self.code
