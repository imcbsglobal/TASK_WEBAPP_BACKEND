from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.db import transaction, DatabaseError
from django.db.models import OuterRef, Subquery
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from decimal import Decimal, InvalidOperation
import jwt
import logging

from .models import ShopLocation
from .serializers import ShopLocationSerializer
from app1.models import Misel, AccMaster

logger = logging.getLogger(__name__)


def decode_jwt_token(request):
    """Decode JWT token from Authorization header"""
    auth_header = request.META.get("HTTP_AUTHORIZATION")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload
    except Exception:
        return None


def get_client_id_from_token(request):
    """Get client_id from JWT token"""
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload.get('client_id')
    except Exception:
        return None


@api_view(['POST'])
def shop_location(request):
    """Create or update shop location"""
    try:
        payload = decode_jwt_token(request)
        if not payload:
            return Response({'error': 'Invalid or missing token'}, status=401)

        client_id = payload.get("client_id")
        username = payload.get("username")

        if not client_id:
            return Response({'error': 'Invalid or missing token'}, status=401)

        firm_name = request.data.get('firm_name')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        if not firm_name or not latitude or not longitude:
            return Response({'error': 'firm_name, latitude, longitude required'}, status=400)

        # Validate coordinates
        try:
            lat = Decimal(str(latitude))
            lng = Decimal(str(longitude))
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return Response({'error': 'Invalid coordinate values'}, status=400)
        except (InvalidOperation, ValueError):
            return Response({'error': 'Invalid coordinate format'}, status=400)

        try:
            firm = AccMaster.objects.get(name=firm_name, client_id=client_id)
        except AccMaster.DoesNotExist:
            return Response({'error': 'Invalid firm for this client'}, status=404)

        with transaction.atomic():
            shop, created = ShopLocation.objects.get_or_create(
                firm=firm,
                client_id=client_id,
                defaults={
                    'latitude': latitude,
                    'longitude': longitude,
                    "created_by": username 
                },
            )

            if not created:
                shop.latitude = latitude
                shop.longitude = longitude
                if username:
                    shop.created_by = username
                shop.save()

        serializer = ShopLocationSerializer(shop)
        return Response({'success': True, 'data': serializer.data}, status=201 if created else 200)

    except DatabaseError as e:
        logger.error(f"Database error in shop_location: {str(e)}")
        return Response({'error': 'Database operation failed'}, status=500)
    except Exception as e:
        logger.exception("Unexpected error in shop_location")
        return Response({'error': 'An unexpected error occurred'}, status=500)


@api_view(['GET'])
def get_firms(request):
    """Get all firms with their latest shop location coordinates"""
    try:
        payload = decode_jwt_token(request)
        if not payload:
            return Response({'error': 'Invalid or missing token'}, status=401)

        client_id = payload.get('client_id')
        if not client_id:
            return Response({'error': 'Invalid or missing token'}, status=401)

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

        if not firms.exists():
            return Response({'success': True, 'firms': [], 'message': 'No firms found'}, status=200)

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

    except DatabaseError as e:
        logger.error(f"Database error in get_firms: {str(e)}")
        return Response({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.exception("Unexpected error in get_firms")
        return Response({'error': 'An unexpected error occurred'}, status=500)


@api_view(['GET'])
def get_table_data(request):
    """Get shop location data for authenticated client using optimized raw SQL"""
    try:
        payload = decode_jwt_token(request)
        if not payload:
            return Response({'error': 'Invalid or missing token'}, status=401)

        client_id = payload.get('client_id')
        if not client_id:
            return Response({'error': 'Invalid token payload'}, status=401)
        userRole=payload.get('role')
        userName=payload.get('username')
        print(userRole)
        from django.db import connection

        # ✅ Dynamic table names (no hardcoding)
        shop_table = ShopLocation._meta.db_table       # "shop_location"
        firm_table = AccMaster._meta.db_table          # "acc_master"

        if(userRole=='Admin' or userRole =='admin'):
            

        # ✅ Correct join: shop_location.firm_code → acc_master.code
            sql_query = f"""
            SELECT 
            s.id,
            s.latitude,
            s.longitude,
            s.status,
            s.created_by,
            s.created_at,
            s.client_id,
            a.code as firm_code,
            COALESCE(a.name, 'Unknown Store') as firm_name,
            COALESCE(a.place, 'No address') as firm_place
            FROM {shop_table} s
            LEFT JOIN {firm_table} a ON s.firm_code = a.code AND s.client_id = a.client_id
            WHERE s.client_id = %s
            ORDER BY s.created_at DESC
            """
        else :
                        sql_query = f"""
            SELECT 
            s.id,
            s.latitude,
            s.longitude,
            s.status,
            s.created_by,
            s.created_at,
            s.client_id,
            a.code as firm_code,
            COALESCE(a.name, 'Unknown Store') as firm_name,
            COALESCE(a.place, 'No address') as firm_place
            FROM {shop_table} s
            LEFT JOIN {firm_table} a ON s.firm_code = a.code AND s.client_id = a.client_id
            WHERE s.client_id = %s AND s.created_by = '{userName}'
            ORDER BY s.created_at DESC
            """


        with connection.cursor() as cursor:
            cursor.execute(sql_query, [client_id])
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

        if not rows:
            return Response({
                'success': True,
                'data': [],
                'message': 'No shop locations found',
                'count': 0
            }, status=200)

        # ✅ Convert rows → dicts
        data = []
        for row in rows:
            row_dict = dict(zip(columns, row))

            # Safe coordinate conversion
            try:
                latitude = float(row_dict['latitude']) if row_dict['latitude'] is not None else None
                longitude = float(row_dict['longitude']) if row_dict['longitude'] is not None else None
            except (ValueError, TypeError):
                latitude, longitude = None, None

            # Safe timestamp formatting
            try:
                last_captured = row_dict['created_at'].isoformat() if row_dict['created_at'] else None
            except Exception:
                last_captured = str(row_dict['created_at']) if row_dict['created_at'] else None

            data.append({
                'id': row_dict['id'],
                'firm_code': row_dict['firm_code'],
                'storeName': row_dict['firm_name'],
                'storeLocation': row_dict['firm_place'],
                'latitude': latitude,
                'longitude': longitude,
                'status': row_dict['status'] or 'pending',
                'taskDoneBy': row_dict['created_by'] or 'Unknown',
                'lastCapturedTime': last_captured,
                'client_id': row_dict['client_id'],
            })

        return Response({
            'success': True,
            'data': data,
            'count': len(data),
            'message': 'Shop locations retrieved successfully'
        }, status=200)

    except DatabaseError as e:
        logger.error(f"Database error in get_table_data: {str(e)}")
        return Response({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.exception("Unexpected error in get_table_data")
        return Response({'error': 'Internal server error'}, status=500)




@api_view(['POST'])
def update_location_status(request):
    """Update the status of a shop location"""
    try:
        payload = decode_jwt_token(request)
        if not payload:
            return Response({'error': 'Invalid or missing token'}, status=401)
        
        client_id = payload.get("client_id")
        username = payload.get("username")

        new_status = request.data.get('status')
        shop_id = request.data.get('shop_id')

        if not new_status:
            return Response({"error": 'Status is required'}, status=400)

        if not shop_id:
            return Response({"error": 'ShopId is required'}, status=400)
    
        with transaction.atomic():
            updated_count = ShopLocation.objects.filter(
                client_id=client_id,
                firm_id=shop_id
            ).update(status=new_status)

            if updated_count == 0:
                return Response({'error': 'Shop not found or unauthorized'}, status=404)

        return Response({'success': True, 'updated_count': updated_count}, status=200)

    except MultipleObjectsReturned:
        logger.error(f"Multiple ShopLocations found for client_id={client_id}, shop_id={shop_id}")
        return Response({'error': 'Multiple shops found with same ID, please contact support'}, status=500)
    except DatabaseError as e:
        logger.error(f"Database error in update_location_status: {str(e)}")
        return Response({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.exception("Unexpected error while updating shop status")
        return Response({'error': 'Internal server error'}, status=500)


@api_view(['GET'])
def health_check(request):
    """Simple health check endpoint"""
    return Response({
        'status': 'healthy',
        'message': 'API is running'
    }, status=200)