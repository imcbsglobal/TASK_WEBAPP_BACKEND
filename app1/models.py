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
        managed  = False          # table already exists 



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
        managed = False  # Since the table already 
        




class AccMaster(models.Model):
    """
    Account Master table - contains account information
    Connected via 'code' field to other tables
    """
    code = models.CharField(max_length=30, primary_key=True)
    name = models.CharField(max_length=200, blank=True, null=True)#
    super_code = models.CharField(max_length=5, blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)#
    debit = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)#
    credit = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)#
    place = models.CharField(max_length=100, blank=True, null=True)#
    phone2 = models.CharField(max_length=60, blank=True, null=True)#
    openingdepartment = models.CharField(max_length=100, blank=True, null=True)
    area = models.CharField(max_length=200, blank=True, null=True)
    client_id = models.CharField(max_length=100)

    class Meta:
        db_table = 'acc_master'
        managed = False  # Since the table already exists
        unique_together = ('code', 'client_id')


class AccLedgers(models.Model):
    """
    Account Ledgers table - contains transaction records
    Connected via 'code' field to AccMaster
    """
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=30)  # Links to AccMaster.code
    particulars = models.CharField(max_length=500, blank=True, null=True)#
    debit = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)#
    credit = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)#
    entry_mode = models.CharField(max_length=20, blank=True, null=True)
    entry_date = models.DateField(blank=True, null=True)#
    voucher_no = models.IntegerField(blank=True, null=True)
    narration = models.TextField(blank=True, null=True)
    client_id = models.CharField(max_length=100)

    class Meta:
        db_table = 'acc_ledgers'
        managed = False  # Since the table already exists


class AccInvmast(models.Model):
    """
    Invoice Master table - contains invoice information
    Connected via 'customerid' field to AccMaster.code
    """
    id = models.AutoField(primary_key=True)
    modeofpayment = models.CharField(max_length=10, blank=True, null=True)
    customerid = models.CharField(max_length=30, blank=True, null=True)  # Links to AccMaster.code
    invdate = models.DateField(blank=True, null=True)#
    nettotal = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)#
    paid = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)#
    bill_ref = models.CharField(max_length=100, blank=True, null=True)
    client_id = models.CharField(max_length=100)

    class Meta:
        db_table = 'acc_invmast'
        managed = False  # Since the table alrea



class CashAndBankAccMaster(models.Model):
    """
    Cash and Bank Account Master table
    Stores cash and bank account information
    super_code determines if it's CASH or BANK
    """
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=250)
    super_code = models.CharField(max_length=5, blank=True, null=True)  # CASH or BANK
    opening_balance = models.DecimalField(max_digits=15, decimal_places=3, blank=True, null=True)
    opening_date = models.DateField(blank=True, null=True)
    debit = models.DecimalField(max_digits=15, decimal_places=3, blank=True, null=True)
    credit = models.DecimalField(max_digits=15, decimal_places=3, blank=True, null=True)
    client_id = models.CharField(max_length=100)

    class Meta:
        db_table = 'cashandbankaccmaster'
        managed = False  # Since the table already exists
        unique_together = ('code', 'client_id')