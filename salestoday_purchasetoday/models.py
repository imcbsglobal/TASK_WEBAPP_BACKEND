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
