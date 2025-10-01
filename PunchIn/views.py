from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.db import transaction, DatabaseError,connection
from django.db.models import OuterRef, Subquery
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
import uuid

import jwt
import logging
import time
import hashlib

from .models import ShopLocation, PunchIn
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

# shop location table 
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
        
        startDate = request.GET.get('start_date')
        endDate =request.GET.get('end_date')
        if startDate and endDate:
            date_filter = f"AND s.created_at BETWEEN '{startDate}' AND '{endDate}'"
        else:
            date_filter = ""


        print("Start/End date :",startDate ,endDate)


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
            WHERE s.client_id = %s  {date_filter}
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
            WHERE s.client_id = %s AND s.created_by = '{userName}'  {date_filter}
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
def get_upload_signature(request):
    """
    Generate Cloudinary upload signature for authenticated users with restrictions
    """
    try:
        # ✅ Authenticate user first
        payload = decode_jwt_token(request)
        if not payload:
            return Response({'error': 'Authentication required'}, status=401)
        
        client_id = payload.get('client_id')
        username = payload.get('username')
        customer_name = request.query_params.get('customerName')
        print("CustomerName: ",customer_name)

        if not client_id or not username:
            return Response({'error': 'Invalid token payload'}, status=401)
        
        timestamp = int(time.time())
        today_str  = time.strftime("%Y-%m-%d")


        logger.info(f"Generating signature for user: {username}, timestamp: {timestamp}")
        
        # ✅ Access Cloudinary config
        cloudinary_config = settings.CLOUDINARY_STORAGE
        api_secret = cloudinary_config['API_SECRET']
        cloud_name = cloudinary_config['CLOUD_NAME']
        api_key = cloudinary_config['API_KEY']
        public_id = f"punch_images/{client_id}/{customer_name}/{username}{today_str}{uuid.uuid4().hex[:4]}"
        # ✅ ONLY include parameters that will be signed
        # Parameters that go into the signature generation
        params_to_sign = {
            'timestamp': timestamp,
            'folder': f'punch_images/{client_id}/{customer_name}',
            'allowed_formats': 'jpg,png,jpeg',
            'tags': f'client_{client_id},user_{username}',
            'public_id':public_id
        }
        
        # Additional params for frontend validation (NOT signed)
        additional_params = {
            'max_file_size': 5000000,  # 5MB limit - frontend validation only
            'resource_type': 'image'   # Not included in signature
        }
        
        # ✅ Create signature string - ONLY signed parameters
        params_list = []
        for key in sorted(params_to_sign.keys()):
            params_list.append(f"{key}={params_to_sign[key]}")
        
        params_string = "&".join(params_list)
        signature_string = params_string + api_secret
        signature = hashlib.sha1(signature_string.encode('utf-8')).hexdigest()
        
        # ✅ Log for debugging
        logger.info(f"Params to sign: {params_string}")
        logger.info(f"Generated signature: {signature}")
        
        response_data = {
            'success': True,
            'data': {
                "timestamp": timestamp,
                "signature": signature,
                "cloudName": cloud_name,
                # Signed parameters
                "folder": params_to_sign['folder'],
                "allowed_formats": params_to_sign['allowed_formats'],
                "tags": params_to_sign['tags'],
                # Additional parameters for frontend (not signed)
                "max_file_size": additional_params['max_file_size'],
                'public_id': public_id,
                "success": True
            }
        }
        
        logger.info(f"Successfully generated signature for user: {username}")
        
        return Response(response_data, status=200)
        
    except KeyError as e:
        logger.error(f"Missing Cloudinary configuration: {str(e)}")
        return Response({'error': 'Service configuration error', 'success': False}, status=500)
    except Exception as e:
        logger.error(f"Error generating upload signature for user {username if 'username' in locals() else 'unknown'}: {str(e)}")
        return Response({'error': 'Failed to generate upload signature', 'success': False}, status=500)

@api_view(['POST'])
def punchin(request):
    """
    Handle punch-in functionality with image upload and location tracking
    """
    try:
        # ✅ Authenticate user
        payload = decode_jwt_token(request)
        if not payload:
            return Response({'error': 'Authentication required'}, status=401)
        
        client_id = payload.get('client_id')
        username = payload.get('username')
        user_id = payload.get('user_id')

        if not client_id or not username:
            return Response({'error': 'Invalid token payload'}, status=401)

        # Get request data
        firm_code = request.data.get('customerCode')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        photo_url = request.data.get('photo_url')  # Cloudinary URL after upload
        notes = request.data.get('notes', '')
        address = request.data.get('address', '')

        #  Validate required fields
        if not firm_code:
            return Response({'error': 'firm_code is required'}, status=400)
        
        if not latitude or not longitude:
            return Response({'error': 'Location coordinates are required'}, status=400)

        if not photo_url:
            return Response({'error': 'Photo is required for punch-in'}, status=400)

        #  Validate coordinates
        try:
            lat = float(latitude)
            lng = float(longitude)
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return Response({'error': 'Invalid coordinate values'}, status=400)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid coordinate format'}, status=400)

        #  Verify firm exists for this client
        try:
            firm = AccMaster.objects.get(code=firm_code, client_id=client_id)
        except AccMaster.DoesNotExist:
            return Response({'error': 'Invalid firm code for this client'}, status=404)

        #  Check if user is already punched in today
        from django.utils import timezone
        today = timezone.now().date()
        existing_punchin = PunchIn.objects.filter(
            client_id=client_id,
            created_by=username,
            punchin_time__date=today,
            punchout_time__isnull=True  # Still punched in
        ).first()

        # if existing_punchin:
        #     return Response({
        #         'error': 'You are already punched in today. Please punch out first.',
        #         'existing_punchin_id': existing_punchin.id,
        #         'punchin_time': existing_punchin.punchin_time.isoformat()
        #     }, status=400)

        #  Create punch-in record
        with transaction.atomic():
            punchin_record = PunchIn.objects.create(
                firm=firm,
                client_id=client_id,
                latitude=lat,
                longitude=lng,
                photo_url=photo_url,
                address=address,
                notes=notes,
                created_by=username,
                status='pending'
            )

            logger.info(f"Punch-in created successfully for user {username}, ID: {punchin_record.id}")

        # ✅ Prepare response data
        response_data = {
            'success': True,
            'message': 'Punch-in recorded successfully',
            'data': {
                'punchin_id': punchin_record.id,
                'firm_name': firm.name,
                'firm_code': firm.code,
                'punchin_time': punchin_record.punchin_time.isoformat(),
                'latitude': float(punchin_record.latitude),
                'longitude': float(punchin_record.longitude),
                'photo_url': punchin_record.photo_url,
                'address': punchin_record.address,
                'status': punchin_record.status,
                'created_by': punchin_record.created_by
            }
        }

        return Response(response_data, status=201)

    except DatabaseError as e:
        logger.error(f"Database error in punchin: {str(e)}")
        return Response({'error': 'Database operation failed'}, status=500)
    except Exception as e:
        logger.error(f"Error in punchin for user {username if 'username' in locals() else 'unknown'}: {str(e)}")
        return Response({'error': 'Punch-in failed'}, status=500)


@api_view(['POST'])
def punchout(request ,id):
    """
    Handle punch-out functionality
    """
    try:
        # ✅ Authenticate user
        payload = decode_jwt_token(request)
        if not payload:
            return Response({'error': 'Authentication required'}, status=401)
        
        client_id = payload.get('client_id')
        username = payload.get('username')

        if not client_id or not username:
            return Response({'error': 'Invalid token payload'}, status=401)

        punchinId = id
        print(punchinId)

        # ✅ Get optional data
        notes = request.data.get('notes', '')

        # ✅ Find active punch-in record
        from django.utils import timezone
        today = timezone.now().date()
        
        active_punchin = PunchIn.objects.filter(
            client_id=client_id,
            created_by=username,
            punchin_time__date=today,
            punchout_time__isnull=True,
            id=punchinId
        ).first()

        if not active_punchin:
            return Response({
                'error': 'No active punch-in found for today'
            }, status=400)

        # ✅ Update punch-out time
        with transaction.atomic():
            active_punchin.punchout_time = timezone.now()
            active_punchin.status = 'completed'
            if notes:
                active_punchin.notes = (active_punchin.notes + f"\nPunch-out notes: {notes}").strip()
            active_punchin.save()

            logger.info(f"Punch-out recorded successfully for user {username}, ID: {active_punchin.id}")

        # ✅ Calculate work duration
        work_duration = active_punchin.punchout_time - active_punchin.punchin_time
        hours = work_duration.total_seconds() / 3600

        response_data = {
            'success': True,
            'message': 'Punch-out recorded successfully',
            'data': {
                'punchin_id': active_punchin.id,
                'firm_name': active_punchin.firm.name,
                'punchin_time': active_punchin.punchin_time.isoformat(),
                'punchout_time': active_punchin.punchout_time.isoformat(),
                'work_duration_hours': round(hours, 2),
                'status': active_punchin.status
            }
        }

        return Response(response_data, status=200)

    except DatabaseError as e:
        logger.error(f"Database error in punchout: {str(e)}")
        return Response({'error': 'Database operation failed'}, status=500)
    except Exception as e:
        logger.error(f"Error in punchout for user {username if 'username' in locals() else 'unknown'}: {str(e)}")
        return Response({'error': 'Punch-out failed'}, status=500)


@api_view(['GET'])
def get_active_punchin(request):
    """
    Get current punch status for authenticated user
    """
    try:
        # ✅ Authenticate user
        payload = decode_jwt_token(request)
        if not payload:
            return Response({'error': 'Authentication required'}, status=401)
        
        client_id = payload.get('client_id')
        username = payload.get('username')

        if not client_id or not username:
            return Response({'error': 'Invalid token payload'}, status=401)

        # ✅ Check today's punch status
        from django.utils import timezone
        today = timezone.now().date()
        
        active_punchin = PunchIn.objects.filter(
            client_id=client_id,
            created_by=username,
            punchin_time__date=today,
            punchout_time__isnull=True
        ).first()

        if active_punchin:
            # User is currently punched in
            work_duration = timezone.now() - active_punchin.punchin_time
            hours = work_duration.total_seconds() / 3600

            response_data = {
                'success': True,
                'is_punched_in': True,
                'data': {
                    'punchin_id': active_punchin.id,
                    'firm_name': active_punchin.firm.name,
                    'firm_code': active_punchin.firm.code,
                    'punchin_time': active_punchin.punchin_time.isoformat(),
                    'current_work_hours': round(hours, 2),
                    'seconds':work_duration,
                    'photo_url': active_punchin.photo_url,
                    'address': active_punchin.address,
                    'status': active_punchin.status
                }
            }
        else:
            # Check if user has completed punch today
            completed_today = PunchIn.objects.filter(
                client_id=client_id,
                created_by=username,
                punchin_time__date=today,
                punchout_time__isnull=False
            ).first()

            response_data = {
                'success': True,
                'is_punched_in': False,
                'completed_today': completed_today is not None,
                'data': None
            }

            if completed_today:
                work_duration = completed_today.punchout_time - completed_today.punchin_time
                hours = work_duration.total_seconds() / 3600
                response_data['data'] = {
                    'punchin_id': completed_today.id,
                    'firm_name': completed_today.firm.name,
                    'punchin_time': completed_today.punchin_time.isoformat(),
                    'punchout_time': completed_today.punchout_time.isoformat(),
                    'total_work_hours': round(hours, 2),
                    'status': completed_today.status
                }

        return Response(response_data, status=200)

    except DatabaseError as e:
        logger.error(f"Database error in get_punch_status: {str(e)}")
        return Response({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.error(f"Error in get_punch_status for user {username if 'username' in locals() else 'unknown'}: {str(e)}")
        return Response({'error': 'Failed to get punch status'}, status=500)


@api_view(['GET'])
def punchin_table(request):
    """Get punch-in table data for authenticated client with role-based filtering"""
    try:
        payload = decode_jwt_token(request)
        if not payload:
            return Response({'error': 'Invalid or missing token'}, status=401)

        client_id = payload.get('client_id')
        if not client_id:
            return Response({'error': 'Invalid token payload'}, status=401)
        
        user_role = payload.get('role')
        username = payload.get('username')
        
        from django.db import connection

        # Get dynamic table names
        punchin_table = PunchIn._meta.db_table  # "punchin"
        firm_table = AccMaster._meta.db_table   # "acc_master"

        # Role-based query construction
        if user_role and user_role.lower() == 'admin':
            # Admin sees all punch-ins for the client
            sql_query = f"""
            SELECT 
                p.id,
                p.latitude,
                p.longitude,
                p.punchin_time,
                p.punchout_time,
                p.photo_url,
                p.address,
                p.notes,
                p.status,
                p.created_by,
                p.created_at,
                p.updated_at,
                p.client_id,
                a.code as firm_code,
                COALESCE(a.name, 'Unknown Store') as firm_name,
                COALESCE(a.place, 'No address') as firm_place
            FROM {punchin_table} p
            LEFT JOIN {firm_table} a ON p.firm_code = a.code AND p.client_id = a.client_id
            WHERE p.client_id = %s
            ORDER BY p.punchin_time DESC
            """
            query_params = [client_id]
        else:
            # Regular user sees only their own punch-ins
            sql_query = f"""
            SELECT 
                p.id,
                p.latitude,
                p.longitude,
                p.punchin_time,
                p.punchout_time,
                p.photo_url,
                p.address,
                p.notes,
                p.status,
                p.created_by,
                p.created_at,
                p.updated_at,
                p.client_id,
                a.code as firm_code,
                COALESCE(a.name, 'Unknown Store') as firm_name,
                COALESCE(a.place, 'No address') as firm_place
            FROM {punchin_table} p
            LEFT JOIN {firm_table} a ON p.firm_code = a.code AND p.client_id = a.client_id
            WHERE p.client_id = %s AND p.created_by = %s
            ORDER BY p.punchin_time DESC
            """
            query_params = [client_id, username]

        with connection.cursor() as cursor:
            cursor.execute(sql_query, query_params)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

        if not rows:
            return Response({
                'success': True,
                'data': [],
                'message': 'No punch-in records found',
                'count': 0
            }, status=200)

        # Process rows into structured data
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
                punchin_time = row_dict['punchin_time'].isoformat() if row_dict['punchin_time'] else None
            except Exception:
                punchin_time = str(row_dict['punchin_time']) if row_dict['punchin_time'] else None

            try:
                punchout_time = row_dict['punchout_time'].isoformat() if row_dict['punchout_time'] else None
            except Exception:
                punchout_time = str(row_dict['punchout_time']) if row_dict['punchout_time'] else None

            # Calculate work duration if both times exist
            work_duration_hours = None
            if row_dict['punchin_time'] and row_dict['punchout_time']:
                try:
                    from django.utils import timezone
                    if hasattr(row_dict['punchin_time'], 'timestamp') and hasattr(row_dict['punchout_time'], 'timestamp'):
                        duration = row_dict['punchout_time'] - row_dict['punchin_time']
                        work_duration_hours = round(duration.total_seconds() / 3600, 2)
                except Exception:
                    work_duration_hours = None

            # Build response record
            record = {
                'id': row_dict['id'],
                'firm_code': row_dict['firm_code'],
                'firm_name': row_dict['firm_name'],
                'firm_location': row_dict['firm_place'],
                'latitude': latitude,
                'longitude': longitude,
                'punchin_time': punchin_time,
                'punchout_time': punchout_time,
                'work_duration_hours': work_duration_hours,
                'photo_url': row_dict['photo_url'],
                'address': row_dict['address'] or '',
                'notes': row_dict['notes'] or '',
                'status': row_dict['status'] or 'pending',
                'created_by': row_dict['created_by'] or 'Unknown',
                'client_id': row_dict['client_id'],
                'is_active': row_dict['punchout_time'] is None,  # Still punched in
                'created_at': row_dict['created_at'].isoformat() if row_dict['created_at'] else None,
                'updated_at': row_dict['updated_at'].isoformat() if row_dict['updated_at'] else None
            }

            data.append(record)

        return Response({
            'success': True,
            'data': data,
            'count': len(data),
            'message': f'Punch-in records retrieved successfully ({len(data)} records)',
            'user_role': user_role,
            'is_admin_view': user_role and user_role.lower() == 'admin'
        }, status=200)

    except DatabaseError as e:
        logger.error(f"Database error in punchin_table: {str(e)}")
        return Response({'error': 'Database error'}, status=500)
    except Exception as e:
        logger.error(f"Error in punchin_table: {str(e)}")
        return Response({'error': 'Failed to get punch-in records'}, status=500)



#  id | latitude  | longitude | client_id |         punchin_time          |         punchout_time         |                                                                                                 photo_url                                                                                                  |  status   |          created_at           |          updated_at           | firm_code | address | created_by | notes
# ----+-----------+-----------+-----------+-------------------------------+-------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------------------------+-------------------------------+-----------+---------+------------+-------
#   1 | 11.617994 | 76.081437 | SYSMAC    | 2025-09-19 06:08:45.637841+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758262122/punch_images/SYSMAC/ARUN/p77tk6m44qmv5yapdlsj.jpg                                                                                            | pending   | 2025-09-19 06:08:45.637887+00 | 2025-09-19 06:08:45.637893+00 | 00918     |         | ARUN       |
#   2 | 11.617994 | 76.081437 | SYSMAC    | 2025-09-19 06:10:42.223465+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758262238/punch_images/SYSMAC/ARUN/hpshgisc6ikvtx7yfqyu.jpg                                                                                            | pending   | 2025-09-19 06:10:42.223565+00 | 2025-09-19 06:10:42.223577+00 | 00918     |         | ARUN       |
#   3 | 11.617994 | 76.081437 | SYSMAC    | 2025-09-19 06:13:02.379596+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758262379/punch_images/SYSMAC/ARUN/lwl9s35gi2s0lqonozjn.jpg                                                                                            | pending   | 2025-09-19 06:13:02.379646+00 | 2025-09-19 06:13:02.379652+00 | 00918     |         | ARUN       |
#   4 | 11.617990 | 76.081440 | SYSMAC    | 2025-09-19 06:13:44.029351+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758258546/punch_images/SYSMAC/ARUN/vr66o6wls8x4agwrz8bf.jpg                                                                                            | pending   | 2025-09-19 06:13:44.029451+00 | 2025-09-19 06:13:44.029457+00 | 00918     |         | ARUN       |
#   5 | 11.617994 | 76.081437 | SYSMAC    | 2025-09-19 06:51:01.311328+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758264658/punch_images/SYSMAC/ARUN/punch_images/SYSMAC/ARUN/2025-09-19.jpg                                                                             | pending   | 2025-09-19 06:51:01.311378+00 | 2025-09-19 06:51:01.311384+00 | 00930     |         | ARUN       |
#   6 | 11.617994 | 76.081437 | SYSMAC    | 2025-09-19 07:01:29.657624+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758265286/punch_images/SYSMAC/ARUN/punch_images/SYSMAC/ARUN/2025-09-19.jpg                                                                             | pending   | 2025-09-19 07:01:29.657663+00 | 2025-09-19 07:01:29.657668+00 | 00918     |         | ARUN       |
#   7 | 11.617996 | 76.081440 | SYSMAC    | 2025-09-19 09:14:14.106415+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758273250/punch_images/SYSMAC/ARUN/punch_images/SYSMAC/ARUN/2025-09-19.jpg                                                                             | pending   | 2025-09-19 09:14:14.106477+00 | 2025-09-19 09:14:14.106482+00 | 00931     |         | ARUN       |
#   8 | 11.618095 | 76.081223 | SYSMAC    | 2025-09-19 10:52:51.463708+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758279170/punch_images/SYSMAC/ARUN/punch_images/SYSMAC/ARUN/2025-09-19.jpg                                                                             | pending   | 2025-09-19 10:52:51.463756+00 | 2025-09-19 10:52:51.463761+00 | 00930     |         | ARUN       |
#   9 | 11.618071 | 76.081289 | SYSMAC    | 2025-09-19 11:04:56.377473+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758279895/punch_images/SYSMAC/ARUN/punch_images/SYSMAC/ARUN/2025-09-19.jpg                                                                             | pending   | 2025-09-19 11:04:56.377537+00 | 2025-09-19 11:04:56.377546+00 | 00933     |         | ARUN       |
#  10 | 11.618069 | 76.081286 | SYSMAC    | 2025-09-19 11:06:40.977501+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758280000/punch_images/SYSMAC/ARUN/punch_images/SYSMAC/ARUN/2025-09-19.jpg                                                                             | pending   | 2025-09-19 11:06:40.977546+00 | 2025-09-19 11:06:40.97755+00  | 00936     |         | ARUN       |
#  11 | 11.618069 | 76.081286 | SYSMAC    | 2025-09-19 11:07:34.457512+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758280053/punch_images/SYSMAC/ARUN/punch_images/SYSMAC/ARUN/2025-09-19.jpg                                                                             | pending   | 2025-09-19 11:07:34.457552+00 | 2025-09-19 11:07:34.457555+00 | 00936     |         | ARUN       |
#  12 | 11.618069 | 76.081286 | SYSMAC    | 2025-09-19 11:08:32.09833+00  |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758280111/punch_images/SYSMAC/ARUN/punch_images/SYSMAC/ARUN/2025-09-19.jpg                                                                             | pending   | 2025-09-19 11:08:32.098362+00 | 2025-09-19 11:08:32.098365+00 | 00934     |         | ARUN       |
#  13 | 11.618071 | 76.081289 | SYSMAC    | 2025-09-19 11:10:54.28611+00  |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758280253/punch_images/SYSMAC/ARUN/punch_images/SYSMAC/ARUN/2025-09-19.jpg                                                                             | pending   | 2025-09-19 11:10:54.286138+00 | 2025-09-19 11:10:54.286141+00 | 00995     |         | ARUN       |
#  14 | 11.617996 | 76.081433 | SYSMAC    | 2025-09-19 11:26:06.572109+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758281163/punch_images/SYSMAC/ARUN/punch_images/SYSMAC/ARUN/2025-09-19.jpg                                                                             | pending   | 2025-09-19 11:26:06.572158+00 | 2025-09-19 11:26:06.572164+00 | 00930     |         | ARUN       |
#  15 | 11.617996 | 76.081433 | SYSMAC    | 2025-09-19 11:32:29.439105+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758281546/punch_images/SYSMAC/ARUN/punch_images/SYSMAC/KAILASH%20BAKERY/ARUN2025-09-19.jpg                                                             | pending   | 2025-09-19 11:32:29.439151+00 | 2025-09-19 11:32:29.439157+00 | 00982     |         | ARUN       |
#  16 | 11.617996 | 76.081433 | SYSMAC    | 2025-09-19 11:34:10.232929+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758281646/punch_images/SYSMAC/TOP%20IN%20TOWN%20RETAIL%20%28BTM%29/punch_images/SYSMAC/TOP%20IN%20TOWN%20RETAIL%20%28BTM%29/ARUN2025-09-19.jpg         | pending   | 2025-09-19 11:34:10.232975+00 | 2025-09-19 11:34:10.232981+00 | 00932     |         | ARUN       |
#  17 | 11.618071 | 76.081289 | SYSMAC    | 2025-09-19 11:35:08.412546+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758281707/punch_images/SYSMAC/ARUN/punch_images/SYSMAC/ARUN/2025-09-19.jpg                                                                             | pending   | 2025-09-19 11:35:08.412592+00 | 2025-09-19 11:35:08.412596+00 | 00933     |         | ARUN       |
#  18 | 11.618070 | 76.081286 | SYSMAC    | 2025-09-19 11:41:59.188002+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758282118/punch_images/SYSMAC/MAHABAZAR%28VARTHUR%29/punch_images/SYSMAC/MAHABAZAR%28VARTHUR%29/ARUN2025-09-19.jpg                                     | pending   | 2025-09-19 11:41:59.18804+00  | 2025-09-19 11:41:59.188044+00 | 00996     |         | ARUN       |
#  19 | 11.618070 | 76.081286 | SYSMAC    | 2025-09-19 11:44:16.200782+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758282255/punch_images/SYSMAC/SUHAIL%28FUN%20WORLD%29/punch_images/SYSMAC/SUHAIL%28FUN%20WORLD%29/ARUN2025-09-19.jpg                                   | pending   | 2025-09-19 11:44:16.200838+00 | 2025-09-19 11:44:16.200842+00 | 00983     |         | ARUN       |
#  20 | 11.617996 | 76.081438 | SYSMAC    | 2025-09-22 04:48:23.940201+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758516498/punch_images/SYSMAC/CRAFT%20SUPER%20MARKET/punch_images/SYSMAC/CRAFT%20SUPER%20MARKET/ARUN2025-09-22.jpg                                     | pending   | 2025-09-22 04:48:23.940249+00 | 2025-09-22 04:48:23.940254+00 | 00931     |         | ARUN       |
#  21 | 11.617990 | 76.081440 | SYSMAC    | 2025-09-22 09:11:30.322979+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758258546/punch_images/SYSMAC/ARUN/vr66o6wls8x4agwrz8bf.jpg                                                                                            | pending   | 2025-09-22 09:11:30.323061+00 | 2025-09-22 09:11:30.323071+00 | 00918     |         | ARUN       |
#  22 | 11.617994 | 76.081435 | SYSMAC    | 2025-09-22 11:03:03.987357+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758538978/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-22.jpg                                                         | pending   | 2025-09-22 11:03:03.987404+00 | 2025-09-22 11:03:03.98741+00  | 00918     |         | ARUN       |
#  23 | 11.617994 | 76.081435 | SYSMAC    | 2025-09-22 11:07:08.29524+00  |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758539220/punch_images/SYSMAC/CRAFT%20SUPER%20MARKET/punch_images/SYSMAC/CRAFT%20SUPER%20MARKET/ARUN2025-09-22.jpg                                     | pending   | 2025-09-22 11:07:08.295301+00 | 2025-09-22 11:07:08.295308+00 | 00931     |         | ARUN       |
#  24 | 11.617994 | 76.081437 | SYSMAC    | 2025-09-23 04:04:38.802297+00 | 2025-09-23 05:30:17.583276+00 | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758600278/punch_images/SYSMAC/IN%20AND%20OUT/punch_images/SYSMAC/IN%20AND%20OUT/ARUN2025-09-23.jpg                                                     | completed | 2025-09-23 04:04:38.802763+00 | 2025-09-23 05:30:17.583564+00 | 00930     |         | ARUN       |
#  25 | 11.617990 | 76.081440 | SYSMAC    | 2025-09-23 06:09:47.917104+00 | 2025-09-23 07:03:05.586452+00 | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758258546/punch_images/SYSMAC/ARUN/vr66o6wls8x4agwrz8bf.jpg                                                                                            | completed | 2025-09-23 06:09:47.917163+00 | 2025-09-23 07:03:05.586615+00 | 00918     |         | ARUN       |
#  26 | 11.617990 | 76.081440 | SYSMAC    | 2025-09-23 07:47:45.410429+00 | 2025-09-23 07:47:51.148287+00 | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758258546/punch_images/SYSMAC/ARUN/vr66o6wls8x4agwrz8bf.jpg                                                                                            | completed | 2025-09-23 07:47:45.410478+00 | 2025-09-23 07:47:51.148396+00 | 00918     |         | ARUN       |
#  27 | 11.617990 | 76.081440 | SYSMAC    | 2025-09-23 07:48:14.562321+00 | 2025-09-23 07:49:39.347074+00 | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758258546/punch_images/SYSMAC/ARUN/vr66o6wls8x4agwrz8bf.jpg                                                                                            | completed | 2025-09-23 07:48:14.562474+00 | 2025-09-23 07:49:39.347195+00 | 00918     |         | ARUN       |
#  29 | 11.617996 | 76.081438 | SYSMAC    | 2025-09-23 08:02:28.305689+00 | 2025-09-23 09:06:01.485035+00 | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758614547/punch_images/SYSMAC/TOP%20IN%20TOWN%20RETAIL%20%28BTM%29/punch_images/SYSMAC/TOP%20IN%20TOWN%20RETAIL%20%28BTM%29/ARUN2025-09-23.jpg         | completed | 2025-09-23 08:02:28.306497+00 | 2025-09-23 09:06:01.4854+00   | 00932     |         | ARUN       |
#  28 | 11.617990 | 76.081440 | SYSMAC    | 2025-09-23 07:58:45.311472+00 | 2025-09-23 09:21:21.584773+00 | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758258546/punch_images/SYSMAC/ARUN/vr66o6wls8x4agwrz8bf.jpg                                                                                            | completed | 2025-09-23 07:58:45.311519+00 | 2025-09-23 09:21:21.58488+00  | 00918     |         | ARUN       |
#  30 | 11.617998 | 76.081451 | SYSMAC    | 2025-09-23 09:22:58.097144+00 | 2025-09-23 09:24:33.722754+00 | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758619371/punch_images/SYSMAC/ATHULYA%20DEPARTMENT%20STORE%20%28ANL%29/punch_images/SYSMAC/ATHULYA%20DEPARTMENT%20STORE%20%28ANL%29/ARUN2025-09-23.jpg | completed | 2025-09-23 09:22:58.097195+00 | 2025-09-23 09:24:33.722859+00 | 00933     |         | ARUN       |
#  31 | 11.617996 | 76.081438 | SYSMAC    | 2025-09-23 09:25:13.122221+00 | 2025-09-23 11:48:40.237942+00 | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758619506/punch_images/SYSMAC/CRAFT%20SUPER%20MARKET/punch_images/SYSMAC/CRAFT%20SUPER%20MARKET/ARUN2025-09-23.jpg                                     | completed | 2025-09-23 09:25:13.122262+00 | 2025-09-23 11:48:40.238253+00 | 00931     |         | ARUN       |
#  32 | 11.618063 | 76.081297 | SYSMAC    | 2025-09-23 12:13:44.509502+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758629623/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-23.jpg                                                         | pending   | 2025-09-23 12:13:44.509555+00 | 2025-09-23 12:13:44.509559+00 | 00918     |         | ARUN       |
#  33 | 11.617996 | 76.081438 | SYSMAC    | 2025-09-23 12:18:32.761606+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758629906/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-23.jpg                                                         | pending   | 2025-09-23 12:18:32.761664+00 | 2025-09-23 12:18:32.76167+00  | 00918     |         | ARUN       |
#  34 | 11.617996 | 76.081438 | SYSMAC    | 2025-09-23 12:18:56.390422+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758629928/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-23.jpg                                                         | pending   | 2025-09-23 12:18:56.390464+00 | 2025-09-23 12:18:56.390468+00 | 00918     |         | ARUN       |
#  35 | 11.617996 | 76.081438 | SYSMAC    | 2025-09-23 12:20:04.092721+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758629995/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-23.jpg                                                         | pending   | 2025-09-23 12:20:04.092761+00 | 2025-09-23 12:20:04.092765+00 | 00918     |         | ARUN       |
#  36 | 11.617996 | 76.081438 | SYSMAC    | 2025-09-23 12:21:27.265211+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758630080/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-23.jpg                                                         | pending   | 2025-09-23 12:21:27.265251+00 | 2025-09-23 12:21:27.265256+00 | 00918     |         | ARUN       |
#  37 | 11.617994 | 76.081435 | SYSMAC    | 2025-09-23 12:24:12.818839+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758630246/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-23.jpg                                                         | pending   | 2025-09-23 12:24:12.818883+00 | 2025-09-23 12:24:12.818889+00 | 00918     |         | ARUN       |
#  38 | 11.617996 | 76.081433 | SYSMAC    | 2025-09-23 12:28:25.849712+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758630499/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-23.jpg                                                         | pending   | 2025-09-23 12:28:25.849754+00 | 2025-09-23 12:28:25.849759+00 | 00918     |         | ARUN       |
#  39 | 11.618088 | 76.081476 | SYSMAC    | 2025-09-23 12:32:06.254666+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758630725/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-23.jpg                                                         | pending   | 2025-09-23 12:32:06.254702+00 | 2025-09-23 12:32:06.254705+00 | 00918     |         | ARUN       |
#  40 | 11.617994 | 76.081437 | SYSMAC    | 2025-09-24 05:13:42.286584+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758690815/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-24.jpg                                                         | pending   | 2025-09-24 05:13:42.286637+00 | 2025-09-24 05:13:42.286643+00 | 00918     |         | ARUN       |
#  41 | 11.617998 | 76.081430 | SYSMAC    | 2025-09-24 05:16:26.788311+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758690979/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-24.jpg                                                         | pending   | 2025-09-24 05:16:26.788351+00 | 2025-09-24 05:16:26.788356+00 | 00918     |         | ARUN       |
#  42 | 11.617994 | 76.081435 | SYSMAC    | 2025-09-24 06:12:17.157971+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758694330/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-24.jpg                                                         | pending   | 2025-09-24 06:12:17.158032+00 | 2025-09-24 06:12:17.158037+00 | 00918     |         | ARUN       |
#  43 | 11.617994 | 76.081437 | SYSMAC    | 2025-09-24 06:14:13.006624+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758694446/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-24.jpg                                                         | pending   | 2025-09-24 06:14:13.006666+00 | 2025-09-24 06:14:13.00667+00  | 00918     |         | ARUN       |
#  44 | 11.617923 | 76.081499 | SYSMAC    | 2025-09-24 06:23:32.148799+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758695005/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-24.jpg                                                         | pending   | 2025-09-24 06:23:32.148842+00 | 2025-09-24 06:23:32.148885+00 | 00918     |         | ARUN       |
#  45 | 11.617994 | 76.081435 | SYSMAC    | 2025-09-24 06:48:06.695276+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758696479/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-24.jpg                                                         | pending   | 2025-09-24 06:48:06.695397+00 | 2025-09-24 06:48:06.69541+00  | 00918     |         | ARUN       |
#  46 | 11.618074 | 76.081282 | SYSMAC    | 2025-09-24 06:56:42.406064+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758697001/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-24.jpg                                                         | pending   | 2025-09-24 06:56:42.406989+00 | 2025-09-24 06:56:42.407+00    | 00918     |         | ARUN       |
#  47 | 11.618000 | 76.081449 | SYSMAC    | 2025-09-24 09:55:56.1814+00   |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758707749/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-24.jpg                                                         | pending   | 2025-09-24 09:55:56.181537+00 | 2025-09-24 09:55:56.181544+00 | 00918     |         | ARUN       |
#  48 | 11.617994 | 76.081435 | SYSMAC    | 2025-09-24 11:18:26.467094+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758712699/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-24.jpg                                                         | pending   | 2025-09-24 11:18:26.467162+00 | 2025-09-24 11:18:26.467167+00 | 00918     |         | ARUN       |
#  49 | 11.617994 | 76.081435 | SYSMAC    | 2025-09-25 06:31:47.058964+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758781905/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-25.jpg                                                         | pending   | 2025-09-25 06:31:47.059764+00 | 2025-09-25 06:31:47.059778+00 | 00918     |         | ARUN       |
#  50 | 11.617994 | 76.081435 | SYSMAC    | 2025-09-25 07:04:45.862512+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758783885/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-25.jpg                                                         | pending   | 2025-09-25 07:04:45.863334+00 | 2025-09-25 07:04:45.863342+00 | 00918     |         | ARUN       |
#  51 | 11.617994 | 76.081435 | SYSMAC    | 2025-09-25 07:08:12.641898+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758784084/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-25.jpg                                                         | pending   | 2025-09-25 07:08:12.641947+00 | 2025-09-25 07:08:12.641953+00 | 00918     |         | ARUN       |
#  52 | 11.617996 | 76.081438 | SYSMAC    | 2025-09-25 10:51:27.356252+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758797480/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-25.jpg                                                         | pending   | 2025-09-25 10:51:27.356299+00 | 2025-09-25 10:51:27.356305+00 | 00918     |         | ARUN       |
#  53 | 11.617996 | 76.081433 | SYSMAC    | 2025-09-25 10:55:03.874909+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758797694/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-25.jpg                                                         | pending   | 2025-09-25 10:55:03.874949+00 | 2025-09-25 10:55:03.874954+00 | 00918     |         | ARUN       |
#  54 | 11.617916 | 76.081499 | SYSMAC    | 2025-09-25 10:58:27.461031+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758797900/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-25.jpg                                                         | pending   | 2025-09-25 10:58:27.461073+00 | 2025-09-25 10:58:27.461077+00 | 00918     |         | ARUN       |
#  55 | 11.617996 | 76.081433 | SYSMAC    | 2025-09-25 11:21:24.081038+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758799276/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-25.jpg                                                         | pending   | 2025-09-25 11:21:24.081079+00 | 2025-09-25 11:21:24.081084+00 | 00918     |         | ARUN       |
#  56 | 11.617924 | 76.081500 | SYSMAC    | 2025-09-26 04:45:36.529748+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758861935/punch_images/SYSMAC/ARUN%20KUMAR/punch_images/SYSMAC/ARUN%20KUMAR/ARUN2025-09-26.jpg                                                         | pending   | 2025-09-26 04:45:36.529943+00 | 2025-09-26 04:45:36.529952+00 | 00918     |         | ARUN       |
#  57 | 11.618065 | 76.081296 | SYSMAC    | 2025-09-26 04:55:03.827299+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758862503/punch_images/SYSMAC/CRAFT%20SUPER%20MARKET/punch_images/SYSMAC/CRAFT%20SUPER%20MARKET/ARUN2025-09-26.jpg                                     | pending   | 2025-09-26 04:55:03.828408+00 | 2025-09-26 04:55:03.828418+00 | 00931     |         | ARUN       |
#  58 | 11.617996 | 76.081438 | SYSMAC    | 2025-09-26 05:00:45.607822+00 |                               | https://res.cloudinary.com/dfbei9mv1/image/upload/v1758862844/punch_images/SYSMAC/QUALITY%20MART%20%28KASTURI%20NAGAR%29/punch_images/SYSMAC/QUALITY%20MART%20%28KASTURI%20NAGAR%29/ARUN2025-09-26.jpg     | pending   | 2025-09-26 05:00:45.607861+00 | 2025-09-26 05:00:45.607866+00 | 00936     |         | ARUN       |
# (58 rows)

# ~
# ~
# ~
# ~
# ~
# ~
# ~
# ~
# ~
# ~
# ~
# ~
# ~
# ~
# ~





@api_view(['GET'])
def health_check(request):
    """Simple health check endpoint"""
    return Response({
        'status': 'healthy',
        'message': 'API is running'
    }, status=200)