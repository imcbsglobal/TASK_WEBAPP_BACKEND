from django.db import models

# Create your models here.
from django.db import models

class PDC(models.Model):
    client_id = models.CharField(max_length=50)

    colndate = models.DateField()
    party = models.CharField(max_length=30, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    chequedate = models.DateField(null=True, blank=True)
    chequeno = models.CharField(max_length=20, null=True, blank=True)
    colnstatus = models.CharField(max_length=1, null=True, blank=True)
    status = models.CharField(max_length=1, null=True, blank=True)

    class Meta:
        db_table = "pdc"

    def __str__(self):
        return f"{self.party} - {self.amount}"