from django.db import models

# Create your models here.
from django.db import models

class TenderCash(models.Model):
    client_id = models.CharField(max_length=50)

    # acc_tendercash fields
    mslno = models.BigIntegerField()
    tender_code = models.CharField(max_length=7)
    amount = models.DecimalField(max_digits=12, decimal_places=3)

    # acc_currency fields
    currency_code = models.CharField(max_length=10)
    currency_name = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        db_table = "tendercash"

    def __str__(self):
        return f"{self.tender_code} - {self.amount}"
