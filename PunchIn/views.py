from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import jwt
from .models import ShopLocation
from .serializers import ShopLocationSerializer
from app1.models import Misel,AccMaster  # import existing Misel
from django.db.models import OuterRef, Subquery
from django.db import DatabaseError
from django.core.exceptions import ObjectDoesNotExist,MultipleObjectsReturned
import logging

logger = logging.getLogger(__name__)

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



# add shop location
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
        firm = AccMaster.objects.get(name=firm_name, client_id=client_id)
    except AccMaster.DoesNotExist:
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


# Punchin Drop down data  

@api_view(['GET'])
def get_firms(request):
    try:
        # Decode token
        payload = decode_jwt_token(request)
        client_id = payload.get('client_id')

        if not client_id:
            return Response(
                {'error': 'Invalid or missing token'},
                status=401
            )

        # Prepare subquery for latest shop location
        latest_shop = ShopLocation.objects.filter(
            firm=OuterRef('pk'),
            client_id=client_id
        ).order_by('-created_at')

        # Fetch firms with latest location
        firms = AccMaster.objects.filter(client_id=client_id).annotate(
            latitude=Subquery(latest_shop.values('latitude')[:1]),
            longitude=Subquery(latest_shop.values('longitude')[:1]),
        )

        # If no firms found
        if not firms.exists():
            return Response(
                {'success': True, 'firms': [], 'message': 'No firms found'},
                status=200
            )

        # Build response data
        data = [
            {
                'id': firm.code,
                'firm_name': firm.name,
                'latitude': float(firm.latitude) if firm.latitude is not None else None,
                'longitude': float(firm.longitude) if firm.longitude is not None else None,
            }
            for firm in firms
        ]

        return Response({'success': True, 'firms': data}, status=200)

    except ObjectDoesNotExist:
        return Response(
            {'error': 'Requested resource does not exist'},
            status=404
        )
    except DatabaseError as db_err:
        return Response(
            {'error': 'Database error', 'details': str(db_err)},
            status=500
        )
    except Exception as e:
        # Catch-all for unexpected errors
        return Response(
            {'error': 'An unexpected error occurred', 'details': str(e)},
            status=500
        )


# Get Table Datas
@api_view(['GET'])
def get_table_data(req):

    try:
        payload = decode_jwt_token(req)

        if not payload:
            return Response({'error': 'Invalid or missing token'}, status=401)
        
        client_id = payload.get('client_id')
        role= payload.get('role')

        shops =(ShopLocation.objects.select_related('firm')
                .only(
                    'id', 'latitude', 'longitude', 'status', 
                    'created_by', 'created_at', 'client_id',
                    'firm__code', 'firm__name', 'firm__place'
                ).order_by('-created_at'))
    

        if not shops.exists():
            return Response({
                'success':True,
                'data':[],
                'message':'No Shop location Found'
            })
        
        data=[]
        for shop in shops:
            try:
                shop_data = {
                    'id': shop.id, 
                    'firm_code': shop.firm.code if shop.firm else None,
                    'storeName': shop.firm.name if shop.firm else 'Unknown',
                    'storeLocation': shop.firm.place if shop.firm else 'No address',
                    'latitude': float(shop.latitude) if shop.latitude is not None else None,
                    'longitude': float(shop.longitude) if shop.longitude is not None else None,
                    'status': shop.status,
                    'taskDoneBy': shop.created_by,
                    'lastCapturedTime': shop.created_at.isoformat() if shop.created_at else None,
                    'client_id': shop.client_id
                }
                data.append(shop_data)                    

            except Exception as e :
                print(f"Error processing shop {shop.id}: {str(e)}")
                continue

        return Response({
            'success': True, 
            'data': data,
            'count': len(data)
        })
    
    except Exception as e :
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def update_location_status(req):

    try:
        payload =decode_jwt_token(req)

        if not payload:
            return Response({'error': 'Invalid or missing token'}, status=401)
        

        client_id=payload.get("client_id")
        username = payload.get("username")

        newStatus = req.data.get('status')
        shop_id = req.data.get('shop_id')

        if not newStatus:
            return Response({"error":'Status is required'},status=400)

        if not shop_id :
            return Response({"error":'ShopId is required'},status=400)
    
        updated_count = ShopLocation.objects.filter(
            client_id=client_id,
            created_by=username,
            firm_id=shop_id
        ).update(status=newStatus)

        if updated_count ==0:
            return Response({'error': 'Shop not found or unauthorized'}, status=404)

        return Response({'success': True, 'updated_count': updated_count})


    except MultipleObjectsReturned:
        logger.error(f"Multiple ShopLocations found for client_id={client_id}, username={username}, shop_id={shop_id}")
        return Response({'error': 'Multiple shops found with same ID, please contact support'}, status=500)

    except Exception as e:
        logger.exception("Unexpected error while updating shop status")
        return Response({'error': 'Internal server error'}, status=500)

