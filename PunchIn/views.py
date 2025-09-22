from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.db import transaction, DatabaseError
from django.db.models import OuterRef, Subquery
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
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
        public_id = f"punch_images/{client_id}/{customer_name}/{username}{today_str}"
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
def punchout(request):
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

        # ✅ Get optional data
        notes = request.data.get('notes', '')

        # ✅ Find active punch-in record
        from django.utils import timezone
        today = timezone.now().date()
        
        active_punchin = PunchIn.objects.filter(
            client_id=client_id,
            created_by=username,
            punchin_time__date=today,
            punchout_time__isnull=True
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
def health_check(request):
    """Simple health check endpoint"""
    return Response({
        'status': 'healthy',
        'message': 'API is running'
    }, status=200)