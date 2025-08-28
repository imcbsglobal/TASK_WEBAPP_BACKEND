from django.db import models
from app1.models import Misel,AccMaster  # import Misel model from your main app


class ShopLocation(models.Model):

    STATUS_CHOICES =[
        ("verified", "Verified"),
        ("pending", "Pending"),
        ("rejected", "Rejected"),
    ]


    firm = models.ForeignKey(AccMaster, on_delete=models.CASCADE,
                                db_column='firm_code' ,
                                db_constraint=False 
                             )  
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    client_id = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    status=models.CharField(max_length=20 ,choices=STATUS_CHOICES,default="pending")
    created_by = models.CharField(max_length=64)

    class Meta:
        db_table = "shop_location"
