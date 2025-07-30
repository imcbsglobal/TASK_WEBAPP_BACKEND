# models.py
from django.db import models

class AccUser(models.Model):
    """
    Legacy table already exists in PostgreSQL:
        acc_users (
            id          varchar PK,
            pass        varchar,
            role        varchar,
            accountcode varchar,
            client_id   varchar
        )
    """
    id          = models.CharField(max_length=64, primary_key=True, db_column='id')
    password    = models.CharField(max_length=128, db_column='pass')
    role        = models.CharField(max_length=32, blank=True, null=True)
    accountcode = models.CharField(max_length=64, blank=True, null=True)
    client_id   = models.CharField(max_length=64, blank=True, null=True, db_column='client_id')

    class Meta:
        db_table = 'acc_users'
        managed  = False          # table already exists  # table already exists



# models.py - Add this new model
class Misel(models.Model):
    """
    MISEL database table model
    """
    id = models.AutoField(primary_key=True)
    firm_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    phones = models.CharField(max_length=50)
    mobile = models.CharField(max_length=50, blank=True, null=True)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255)
    address3 = models.CharField(max_length=255)
    pagers = models.CharField(max_length=255)
    tinno = models.CharField(max_length=50)
    client_id = models.CharField(max_length=64)

    class Meta:
        db_table = 'misel'
        managed = False  # Since the table already exists