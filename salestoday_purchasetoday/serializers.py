from rest_framework import serializers
from .models import SalesToday, PurchaseToday

class SalesTodaySerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesToday
        fields = [
            'id',
            'nettotal',
            'billno',
            'type',
            'userid',
            'invdate',
            'customername',
            'client_id',
        ]

class PurchaseTodaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseToday
        fields = [
            'id',
            'net',
            'billno',
            'pbillno',
            'date',
            'total',
            'suppliername',
            'client_id',
        ]
