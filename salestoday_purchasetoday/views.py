from acc_sales_type.models import AccSalesType
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
import jwt
from .models import SalesDaywise, SalesMonthwise, SalesToday, PurchaseToday
from .serializers import SalesDaywiseSerializer, SalesMonthwiseSerializer, SalesTodaySerializer, PurchaseTodaySerializer
from datetime import datetime
from django.db.models import Sum, Count
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

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count


@api_view(['GET'])
def get_sales_today_usersummary(request):
    """
    Returns USER wise sales summary for today
    """

    client_id, err = _decode_token_get_client_id(request)
    if err:
        return err

    today = _current_date_in_kolkata()

    qs = (
        SalesToday.objects
        .filter(client_id=client_id, invdate=today)
        .values('userid')
        .annotate(
            total_amount=Sum('nettotal'),
            bill_count=Count('id')
        )
        .order_by('userid')
    )

    data = []

    grand_total = 0
    total_bills = 0

    for row in qs:
        amount = float(row['total_amount'] or 0)
        grand_total += amount
        total_bills += row['bill_count']

        data.append({
            "userid": row['userid'],
            "total_amount": amount,
            "bill_count": row['bill_count']
        })

    return Response({
        "success": True,
        "date": today.isoformat(),
        "total_users": len(data),
        "total_bills": total_bills,
        "grand_total": grand_total,
        "data": data
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
    """
    Returns ALL monthwise sales data from DB
    """

    client_id, err = _decode_token_get_client_id(request)
    if err:
        return err

    qs = (
        SalesMonthwise.objects
        .filter(client_id=client_id)
        .order_by('year', 'month_number')
    )

    serializer = SalesMonthwiseSerializer(qs, many=True)

    return Response({
        'success': True,
        'total_records': qs.count(),
        'data': serializer.data,
    })


@api_view(['GET'])
def get_sale_report(request):
    """
    Returns individual sale records for the dashboard.
    Returns sales from the last 30 days for the requesting client.
    
    Auth: Authorization: Bearer <jwt> (token must contain client_id)
    
    Response format:
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "date": "2026-03-13",
                "amount": 2500.00,
                "total_amount": 2500.00,
                "customer_id": 1,
                "customername": "Customer Name",
                "billno": 100,
                "invdate": "2026-03-13"
            },
            ...
        ]
    }
    """
    from datetime import timedelta
    
    client_id, err = _decode_token_get_client_id(request)
    if err:
        return err

    today = _current_date_in_kolkata()
    thirty_days_ago = today - timedelta(days=30)
    
    # Get all sales from last 30 days
    qs = SalesToday.objects.filter(
        client_id=client_id,
        invdate__gte=thirty_days_ago,
        invdate__lte=today
    ).order_by('-invdate', '-id')
    
    data = []
    for sale in qs:
        data.append({
            'id': sale.id,
            'date': sale.invdate.isoformat() if sale.invdate else None,
            'sale_date': sale.invdate.isoformat() if sale.invdate else None,
            'amount': float(sale.nettotal or 0),
            'total_amount': float(sale.nettotal or 0),
            'customer_id': sale.customername,
            'customername': sale.customername,
            'billno': sale.billno,
            'invdate': sale.invdate.isoformat() if sale.invdate else None,
            'userid': sale.userid
        })
    
    return Response({
        'success': True,
        'total_records': len(data),
        'data': data,
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


@api_view(['GET'])
def get_sales_today_usersummary(request):
    """
    Returns sales summary by user for today
    
    Auth: Authorization: Bearer <jwt> (token must contain client_id)
    
    Response format:
    {
        "success": true,
        "date": "2026-03-18",
        "total_users": 5,
        "total_bills": 45,
        "grand_total": 125000.00,
        "data": [
            {
                "userid": "user1",
                "username": "John Doe",
                "total_amount": 25000.00,
                "bill_count": 8
            },
            ...
        ]
    }
    """
    client_id, err = _decode_token_get_client_id(request)
    if err:
        return err

    today = _current_date_in_kolkata()

    qs = (
        SalesToday.objects
        .filter(client_id=client_id, invdate=today)
        .values('userid')
        .annotate(
            total_amount=Sum('nettotal'),
            bill_count=Count('id')
        )
        .order_by('-total_amount')
    )

    data = []
    grand_total = 0
    total_bills = 0

    for row in qs:
        amount = float(row['total_amount'] or 0)
        grand_total += amount
        total_bills += row['bill_count']

        data.append({
            "userid": row['userid'] or 'Unknown',
            "total_amount": amount,
            "bill_count": row['bill_count'],
            "average_bill_value": amount / row['bill_count'] if row['bill_count'] > 0 else 0
        })

    return Response({
        "success": True,
        "date": today.isoformat(),
        "total_users": len(data),
        "total_bills": total_bills,
        "grand_total": grand_total,
        "data": data
    })


# jnk

from django.db.models import Sum, Count, OuterRef, Subquery

@api_view(['GET'])
def get_sales_today_typewise(request):
    """
    Returns SALE TYPE wise sales summary for today (with type name)
    """

    client_id, err = _decode_token_get_client_id(request)
    if err:
        return err

    today = _current_date_in_kolkata()

    # 🔥 Subquery to get type name
    type_name_subquery = AccSalesType.objects.filter(
        cd=OuterRef('type'),
        client_id=client_id
    ).values('name')[:1]

    qs = (
        SalesToday.objects
        .filter(client_id=client_id, invdate=today)
        .values('type')
        .annotate(
            type_name=Subquery(type_name_subquery),
            total_amount=Sum('nettotal'),
            bill_count=Count('id')
        )
        .order_by('type')
    )

    data = []
    grand_total = 0
    total_bills = 0

    for row in qs:
        amount = float(row['total_amount'] or 0)
        grand_total += amount
        total_bills += row['bill_count']

        data.append({
            "type": row['type'],
            "type_name": row['type_name'],
            "total_amount": amount,
            "bill_count": row['bill_count']
        })

    return Response({
        "success": True,
        "date": today.isoformat(),
        "total_types": len(data),
        "total_bills": total_bills,
        "grand_total": grand_total,
        "data": data
    })



@api_view(['GET'])
def get_sales_today_details(request):
    """
    Returns bill level sales details for today
    """

    client_id, err = _decode_token_get_client_id(request)
    if err:
        return err

    today = _current_date_in_kolkata()

    qs = (
        SalesToday.objects
        .filter(client_id=client_id, invdate=today)
        .values(
            'customername',
            'billno',
            'userid',
            'nettotal'
        )
        .order_by('-id')
    )

    data = []
    grand_total = 0

    for row in qs:
        amount = float(row['nettotal'] or 0)
        grand_total += amount

        data.append({
            "customername": row['customername'],
            "billno": row['billno'],
            "userid": row['userid'],
            "nettotal": amount
        })

    return Response({
        "success": True,
        "date": today.isoformat(),
        "total_bills": len(data),
        "grand_total": grand_total,
        "data": data
    })