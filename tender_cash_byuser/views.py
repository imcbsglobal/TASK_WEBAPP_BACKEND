from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
import jwt
from django.conf import settings


from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
import jwt
from django.conf import settings


@api_view(['GET'])
def tender_cash_by_user(request):
    try:
        # 🔐 JWT validation
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response(
                {'success': False, 'error': 'Missing or invalid authorization header'},
                status=401
            )

        token = auth_header.split(' ')[1]

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return Response({'success': False, 'error': 'Token expired'}, status=401)
        except jwt.InvalidTokenError:
            return Response({'success': False, 'error': 'Invalid token'}, status=401)

        # ✅ ONLY client_id from token
        client_id = payload.get('client_id')
        if not client_id:
            return Response(
                {'success': False, 'error': 'Invalid token payload'},
                status=401
            )

        # ✅ Database is source of truth
        query = """
            SELECT
                tender_code,
                amount
            FROM tendercash
            WHERE client_id = %s
            ORDER BY tender_code
        """

        with connection.cursor() as cursor:
            cursor.execute(query, [client_id])
            rows = cursor.fetchall()

        items = []
        total = 0.0

        for code, amount in rows:
            amount = float(amount)
            items.append({
                "code": code,
                "amount": amount
            })
            total += amount

        return Response({
            "success": True,
            "client_id": client_id,
            "data": {
                "user": None,          # 👈 explicitly NULL
                "total": total,
                "items": items
            }
        })

    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=500
        )