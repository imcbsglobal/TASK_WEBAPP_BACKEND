from rest_framework import serializers
from .models import SalesDaywise, SalesMonthwise, SalesToday, PurchaseToday

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




class SalesDaywiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesDaywise
        fields = [
            'id',
            'date',
            'total_bills',
            'total_amount',
            'client_id',
        ]


class SalesMonthwiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesMonthwise
        fields = [
            'id',
            'month_name',
            'month_number',
            'year',
            'total_bills',
            'total_amount',
            'client_id',
        ]