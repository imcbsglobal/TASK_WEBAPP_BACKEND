from django.db import models
from app1.models import Misel   # import Misel model from your main app

class ShopLocation(models.Model):
    firm = models.ForeignKey(Misel, on_delete=models.CASCADE)  # link to Misel
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    client_id = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "shop_location"
