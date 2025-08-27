from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import jwt
from .models import ShopLocation
from .serializers import ShopLocationSerializer
from app1.models import Misel,AccUser  # import existing Misel

def get_client_id_from_token(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload.get('client_id')
    except Exception:
        return None

def decode_jwt_token(request):

    auth_header = request.META.get("HTTP_AUTHORIZATION")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token =auth_header.split(' ')[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload
    
    except Exception:
        return None




@api_view(['POST'])
def shop_location(request):

    payload =decode_jwt_token(request)

    client_id=payload.get("client_id")
    username = payload.get("username")

    if not client_id:
        return Response({'error': 'Invalid or missing token'}, status=401)

    firm_name = request.data.get('firm_name')
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')

    if not firm_name or not latitude or not longitude:
        return Response({'error': 'firm_name, latitude, longitude required'}, status=400)

    try:
        firm = Misel.objects.get(firm_name=firm_name, client_id=client_id)
    except Misel.DoesNotExist:
        return Response({'error': 'Invalid firm for this client'}, status=404)

    

    shop, created = ShopLocation.objects.get_or_create(
        firm=firm,
        client_id=client_id,
        defaults={
            'latitude': latitude,
            'longitude': longitude,
            "created_by" :username 
        },
    )

    if not created:
        shop.latitude = latitude
        shop.longitude = longitude

        if username:  # optionally update who modified it
            shop.created_by = username

        shop.save()

    serializer = ShopLocationSerializer(shop)
    return Response({'success': True, 'data': serializer.data}, status=201 if created else 200)


@api_view(['GET'])
def get_firms(request):

    payload = decode_jwt_token(request)
    client_id = payload.get('client_id')

    if not client_id:
        return Response({'error': 'Invalid or missing token'}, status=401)

    firms = Misel.objects.filter(client_id=client_id)

    data = []
    for firm in firms:
        shop = ShopLocation.objects.filter(firm=firm, client_id=client_id).order_by('-created_at').first()
        data.append({
            'id': firm.id,
            'firm_name': firm.firm_name,
            'latitude': float(shop.latitude) if shop else None,
            'longitude': float(shop.longitude) if shop else None,
        })

    return Response({'success': True, 'firms': data})



# Get Table Datas
@api_view(['GET'])
def get_table_data(req):
    payload = decode_jwt_token(req)
    client_id = payload.get('client_id')
    role= payload.get('role')
    print(payload)

    if not client_id:
        return Response({'error': 'Invalid or missing token'}, status=401)
    
    shops =ShopLocation.objects.filter(client_id=client_id)
    
    data=[]
    for shop in shops:    
        print("Client shops :",shop)
        data.append({
          'id':shop.id,
          'shop_name': shop.firm.firm_name  if shop.firm else None,
          'shop_address':shop.firm.address if shop.firm else None,
          'latitude':float(shop.latitude) if shop.latitude else  None,
          'longitude':float(shop.longitude) if shop.longitude else  None,
          'status':shop.status,
          'created_by': shop.created_by,
          'created_at': shop.created_at,
          'client_id': shop.client_id   
        })

    return Response({'success': True, 'Data':data})



@api_view(['POST'])
def update_location_status(req):

    payload =decode_jwt_token(req)

    if not payload:
        return Response({'error': 'Invalid or missing token'}, status=401)
        

    client_id=payload.get("client_id")
    username = payload.get("username")

    newStatus = req.data.get('status')
    shop_id = req.data.get('shop_id')

    if not newStatus:
        return Response({"error":'Status is required'},status=400)

    shopLocation = ShopLocation.objects.filter(client_id=client_id,created_by=username,id=shop_id)

    shopLocation.status =status 
    shopLocation.save()

    return Response({"success":True})

