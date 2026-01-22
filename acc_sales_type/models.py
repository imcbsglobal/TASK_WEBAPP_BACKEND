from django.db import models

# Create your models here.
from django.db import models


class AccSalesType(models.Model):
    cd = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    client_id = models.CharField(max_length=50)

    class Meta:
        db_table = "acc_sales_types"

