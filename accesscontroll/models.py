from django.db import models
from django.contrib.auth.models import AbstractUser
from app1.models import AccUser 


class AllowedMenu(models.Model):
    id= models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=64)
    client_id =models.CharField(max_length=64)
    allowedMenuIds = models.JSONField(default=list) 
    label = models.CharField(max_length=100 ,null=True)  
    path = models.CharField(max_length=200, blank=True, null=True)  # Optional frontend path

    class Meta:
        db_table = 'user_menus'


