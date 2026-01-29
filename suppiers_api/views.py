from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
import jwt

from .models import AccMaster


@api_view(['GET'])
def suppliers_list(request):
    """
    Suppliers API
    - JWT token mandatory
    - client_id extracted ONLY from token
    - Data filtered by client_id
    """

    # 🔐 1. Read Authorization header
    auth_header = request.META.get('HTTP_AUTHORIZATION')

    if not auth_header or not auth_header.startswith('Bearer '):
        return Response(
            {'success': False, 'error': 'Authorization token required'},
            status=401
        )

    token = auth_header.split(' ')[1]

    # 🔓 2. Decode token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        client_id = payload.get('client_id')

        if not client_id:
            return Response(
                {'success': False, 'error': 'Invalid token: client_id missing'},
                status=401
            )

    except jwt.ExpiredSignatureError:
        return Response(
            {'success': False, 'error': 'Token expired'},
            status=401
        )

    except jwt.InvalidTokenError:
        return Response(
            {'success': False, 'error': 'Invalid token'},
            status=401
        )

    # ✅ 3. Fetch suppliers ONLY for this client
    suppliers = AccMaster.objects.filter(
        super_code='SUNCR',   # Suppliers
        client_id=client_id
    ).values(
        'code',
        'name',
        'opening_balance',
        'debit',
        'credit',
        'place',
        'phone2',
        'openingdepartment',
        'area'
    ).order_by('code')

    return Response({
        'success': True,
        'client_id': client_id,
        'count': suppliers.count(),
        'data': list(suppliers)
    })
