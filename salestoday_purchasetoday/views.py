from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
import jwt
from .models import SalesDaywise, SalesMonthwise, SalesToday, PurchaseToday
from .serializers import SalesDaywiseSerializer, SalesMonthwiseSerializer, SalesTodaySerializer, PurchaseTodaySerializer
from datetime import datetime
try:
    # Python 3.9+
    from zoneinfo import ZoneInfo
except Exception:
    # Fallback to pytz if zoneinfo is not available
    from pytz import timezone as ZoneInfo  # type: ignoree

def _decode_token_get_client_id(request):
    """
    Decode JWT from Authorization: Bearer <token> and return client_id.
    Returns (client_id, None) on success, or (None, Response(...)) on error.
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, Response({'success': False, 'error': 'Missing or invalid authorization header'}, status=401)
    token = auth_header.split(' ', 1)[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        client_id = payload.get('client_id')
        if not client_id:
            return None, Response({'success': False, 'error': 'Invalid token: missing client_id'}, status=401)
        return client_id, None
    except jwt.ExpiredSignatureError:
        return None, Response({'success': False, 'error': 'Token has expired'}, status=401)
    except jwt.InvalidTokenError as e:
        return None, Response({'success': False, 'error': f'Invalid token: {str(e)}'}, status=401)

def _current_date_in_kolkata():
    """
    Return current date in Asia/Kolkata timezone.
    Uses zoneinfo if available, otherwise falls back to pytz-like interface.
    """
    try:
        tz = ZoneInfo('Asia/Kolkata')
        now = datetime.now(tz)
    except Exception:
        # If ZoneInfo is actually pytz.timezone imported above, use it.
        try:
            tz = ZoneInfo('Asia/Kolkata')  # type: ignore
            now = datetime.now(tz)
        except Exception:
            # final fallback to naive UTC now
            now = datetime.utcnow()
    return now.date()

@api_view(['GET'])
def get_sales_today(request):
    """
    Returns SalesToday records for the requesting client's client_id
    where invdate == current date in Asia/Kolkata timezone.

    Auth: Authorization: Bearer <jwt>  (token must contain client_id)
    Query params are ignored for date filtering — API returns only today's data.
    """
    client_id, err = _decode_token_get_client_id(request)
    if err:
        return err

    today = _current_date_in_kolkata()

    qs = SalesToday.objects.filter(client_id=client_id, invdate=today).order_by('-invdate', '-id')

    serializer = SalesTodaySerializer(qs, many=True)
    return Response({
        'success': True,
        'date': today.isoformat(),
        'total_records': qs.count(),
        'data': serializer.data,
    })


@api_view(['GET'])
def get_purchase_today(request):
    """
    Returns PurchaseToday records for the requesting client's client_id
    where date == current date in Asia/Kolkata timezone.

    Auth: Authorization: Bearer <jwt>  (token must contain client_id)
    Query params are ignored for date filtering — API returns only today's data.
    """
    client_id, err = _decode_token_get_client_id(request)
    if err:
        return err

    today = _current_date_in_kolkata()

    qs = PurchaseToday.objects.filter(client_id=client_id, date=today).order_by('-date', '-id')

    serializer = PurchaseTodaySerializer(qs, many=True)
    return Response({
        'success': True,
        'date': today.isoformat(),
        'total_records': qs.count(),
        'data': serializer.data,
    })



@api_view(['GET'])
def get_sales_daywise(request):
    """
    Returns SalesDaywise records for the requesting client's client_id.
    Returns last 8 days of sales summary.

    Auth: Authorization: Bearer <jwt>  (token must contain client_id)
    
    Response format:
    {
        "success": true,
        "total_records": 8,
        "data": [
            {
                "id": 1,
                "date": "2025-11-08",
                "total_bills": 150,
                "total_amount": "125000.000",
                "client_id": "CLIENT001"
            },
            ...
        ]
    }
    """
    client_id, err = _decode_token_get_client_id(request)
    if err:
        return err

    qs = SalesDaywise.objects.filter(client_id=client_id).order_by('-date')

    serializer = SalesDaywiseSerializer(qs, many=True)
    return Response({
        'success': True,
        'total_records': qs.count(),
        'data': serializer.data,
    })

@api_view(['GET'])
def get_sales_monthwise(request):
    client_id, err = _decode_token_get_client_id(request)
    if err:
        return err

    year_param = request.GET.get('year')

    qs = SalesMonthwise.objects.filter(client_id=client_id)

    if year_param and year_param != 'all':
        qs = qs.filter(year=year_param)

    qs = qs.order_by('year', 'month_number')

    serializer = SalesMonthwiseSerializer(qs, many=True)

    return Response({
        'success': True,
        'year': year_param if year_param else 'all',
        'total_records': qs.count(),
        'data': serializer.data,
    })





"""
1. Test Sales Daywise API:
   GET http://your-domain/api/salesdaywise/
   Headers:
   Authorization: Bearer <your-jwt-token>

   Expected Response:
   {
       "success": true,
       "total_records": 8,
       "data": [
           {
               "id": 1,
               "date": "2025-11-08",
               "total_bills": 150,
               "total_amount": "125000.000",
               "client_id": "CLIENT001"
           }
       ]
   }

2. Test Sales Monthwise API:
   GET http://your-domain/api/salesmonthwise/
   Headers:
   Authorization: Bearer <your-jwt-token>

   Expected Response:
   {
       "success": true,
       "year": 2025,
       "total_records": 11,
       "data": [
           {
               "id": 1,
               "month_name": "January 2025",
               "month_number": 1,
               "year": 2025,
               "total_bills": 3500,
               "total_amount": "2500000.000",
               "client_id": "CLIENT001"
           }
       ]
   }

3. Test with curl:
   
   # Sales Daywise
   curl -X GET "http://your-domain/api/salesdaywise/" \
        -H "Authorization: Bearer YOUR_JWT_TOKEN"
   
   # Sales Monthwise
   curl -X GET "http://your-domain/api/salesmonthwise/" \
        -H "Authorization: Bearer YOUR_JWT_TOKEN"
"""