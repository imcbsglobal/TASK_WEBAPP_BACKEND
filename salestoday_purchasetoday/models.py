from django.db import models

# Create your models here.
from django.db import models

class SalesToday(models.Model):
    """Sales records from acc_invmast where billno > 0"""
    id = models.AutoField(primary_key=True)
    nettotal = models.DecimalField(max_digits=15, decimal_places=3, blank=True, null=True)
    billno = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=30, blank=True, null=True)
    userid = models.CharField(max_length=10, blank=True, null=True)
    invdate = models.DateField(blank=True, null=True)
    customername = models.CharField(max_length=250, blank=True, null=True)
    client_id = models.CharField(max_length=100)

    class Meta:
        db_table = 'sales_today'
        managed = True
        indexes = [
            models.Index(fields=['client_id', 'invdate']),
            models.Index(fields=['billno']),
        ]

class PurchaseToday(models.Model):
    """Purchase records from acc_purchasemaster where billno > 0"""
    id = models.AutoField(primary_key=True)
    net = models.DecimalField(max_digits=15, decimal_places=3, blank=True, null=True)
    billno = models.IntegerField(blank=True, null=True)
    pbillno = models.IntegerField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    total = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True)
    suppliername = models.CharField(max_length=250, blank=True, null=True)
    client_id = models.CharField(max_length=100)

    class Meta:
        db_table = 'purchase_today'
        managed = True
        indexes = [
            models.Index(fields=['client_id', 'date']),
            models.Index(fields=['billno']),
        ]




class SalesDaywise(models.Model):
    """Sales summary by date for last 8 days"""
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    total_bills = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    client_id = models.CharField(max_length=100)

    class Meta:
        db_table = 'sales_daywise'
        managed = True
        unique_together = ('date', 'client_id')
        indexes = [
            models.Index(fields=['client_id', 'date']),
        ]

    def __str__(self):
        return f"{self.date} - {self.total_bills} bills - ₹{self.total_amount}"


class SalesMonthwise(models.Model):
    """Sales summary by month for current year"""
    id = models.AutoField(primary_key=True)
    month_name = models.CharField(max_length=20)  # e.g., "January 2025"
    month_number = models.IntegerField()  # 1-12
    year = models.IntegerField()
    total_bills = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    client_id = models.CharField(max_length=100)

    class Meta:
        db_table = 'sales_monthwise'
        managed = True
        unique_together = ('month_number', 'year', 'client_id')
        indexes = [
            models.Index(fields=['client_id', 'year', 'month_number']),
        ]

    def __str__(self):
        return f"{self.month_name} - {self.total_bills} bills - ₹{self.total_amount}"