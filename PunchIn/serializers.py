from rest_framework import serializers
from .models import ShopLocation

class ShopLocationSerializer(serializers.ModelSerializer):
    firm_name = serializers.CharField(source='firm.firm_name', read_only=True)

    class Meta:
        model = ShopLocation
        fields = ['id', 'firm', 'firm_name', 'latitude', 'longitude', 'client_id', 'created_at','created_by']
