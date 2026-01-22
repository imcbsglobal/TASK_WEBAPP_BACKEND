from django.db import models

# Create your models here.
from django.db import models

class TypeWiseSalesToday(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=30)
    nettotal = models.DecimalField(max_digits=15, decimal_places=3)
    billcount = models.IntegerField()
    client_id = models.CharField(max_length=100)

    class Meta:
        db_table = 'type_wise_salestoday'
        managed = True
        unique_together = ('type', 'client_id')

    def __str__(self):
        return f"{self.type} - {self.nettotal}"
