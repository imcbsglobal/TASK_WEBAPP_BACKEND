from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
import jwt

from .models import AccMaster


@api_view(['GET'])
def suppliers_list(request):
    try:
        # 1️⃣ Get Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if not auth_header or not auth_header.startswith('Bearer '):
            return Response(
                {'success': False, 'error': 'Missing or invalid authorization header'},
                status=401
            )

        token = auth_header.split(' ')[1]

        # 2️⃣ Decode JWT token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            client_id = payload.get('client_id')

            if not client_id:
                return Response(
                    {'success': False, 'error': 'Invalid token: client_id missing'},
                    status=401
                )

        except jwt.ExpiredSignatureError:
            return Response({'success': False, 'error': 'Token expired'}, status=401)
        except jwt.InvalidTokenError:
            return Response({'success': False, 'error': 'Invalid token'}, status=401)

        # 3️⃣ Fetch suppliers ONLY for logged-in client
        suppliers = AccMaster.objects.filter(
            super_code='SUNCR',
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
            'area',
            'client_id',
            'super_code'
        ).order_by('code')

        return Response({'success': True, 'data': list(suppliers)})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)