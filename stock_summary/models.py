from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
from django.db import models


class StockSummary(models.Model):
    """
    Aggregated stock summary per client.

    Calculation rule (driven by acc_misel.barcodelength):
        barcodelength == 0 / NULL  →  billedcost * (openingquantity + quantity)
        barcodelength  > 0         →  SUM(cost * quantity) across acc_productbatch
    """

    id = models.AutoField(primary_key=True)

    total_products = models.IntegerField(default=0)
    total_stock_value = models.DecimalField(
        max_digits=20, decimal_places=3, default=0
    )
    # True  → batch mode  (barcodelength > 0)
    # False → product mode (barcodelength == 0)
    barcode_mode = models.CharField(max_length=10)

    client_id = models.CharField(max_length=100)

    class Meta:
        db_table = "stock_summary"
        managed = True
        # One summary row per client
        unique_together = ("client_id",)
        indexes = [
            models.Index(fields=["client_id"]),
        ]

    def __str__(self):
        return (
            f"StockSummary(client={self.client_id}, "
            f"products={self.total_products}, "
            f"value={self.total_stock_value})"
        )