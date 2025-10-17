from django.db import models
from app1.models import Misel,AccMaster,AccUser  # import Misel model from your main app


class ShopLocation(models.Model):

    STATUS_CHOICES =[
        ("verified", "Verified"),
        ("pending", "Pending"),
        ("rejected", "Rejected"),
    ]


    firm = models.ForeignKey(
                            AccMaster,
                            to_field='code',              # explicit target PK
                            db_column='firm_code',        # legacy column in DB
                            on_delete=models.CASCADE,
                            db_constraint=False,
                            related_name='shop_locations',
                             )  
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    client_id = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    status=models.CharField(max_length=20 ,choices=STATUS_CHOICES,default="pending")
    created_by = models.CharField(max_length=64)

    class Meta:
        db_table = "shop_location"
        indexes = [
            models.Index(fields=["firm", "client_id"], name="idx_shop_firm_client"),
            models.Index(fields=["created_at"], name="idx_shop_created_at"),
        ]






class PunchIn(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
    ]

    firm = models.ForeignKey(
        AccMaster,
        to_field="code",
        db_column="firm_code",
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="punchins",  # unique related_name
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    client_id = models.CharField(max_length=64, db_index=True)

    # Track punchin and punchout
    punchin_time = models.DateTimeField(auto_now_add=True)   # when record is created
    punchout_time = models.DateTimeField(null=True, blank=True)  # filled later

    # User information
    created_by = models.CharField(max_length=64)  # username from JWT

    # Location and photo
    photo_url = models.URLField(max_length=500, null=True, blank=True)
    address = models.TextField(blank=True, null=True)  # Optional address
    notes = models.TextField(blank=True, null=True)  # Optional notes

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)  # useful for audits
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "punchin"
        indexes = [
            models.Index(fields=["firm", "client_id"], name="idx_punchin_firm_client"),
            models.Index(fields=["punchin_time"], name="idx_punchin_time"),
            models.Index(fields=["client_id", "created_by"], name="idx_punchin_client_user"),
        ]
        ordering = ["-punchin_time"]  # newest first

    def __str__(self):
        return f"{self.created_by} - {self.firm.name} - {self.punchin_time.strftime('%Y-%m-%d %H:%M')}"
    


class UserAreas(models.Model):
    user= models.ForeignKey(AccUser,
        to_field="id",
        db_column="user_id",
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="Areas" )
    client_id = models.CharField(max_length=64, db_index=True)

    
    area_code =models.CharField(max_length=64,db_column="area_code")

    class Meta:
        db_table= "user_areas"
        constraints = [
            models.UniqueConstraint(fields=["user", "area_code"], name="uniq_user_area"),
        ]