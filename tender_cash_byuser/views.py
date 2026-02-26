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
            return Response({'success': False, 'error': 'Unauthorized'}, status=401)

        token = auth_header.split(' ')[1]

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return Response({'success': False, 'error': 'Token expired'}, status=401)
        except jwt.InvalidTokenError:
            return Response({'success': False, 'error': 'Invalid token'}, status=401)

        client_id = payload.get('client_id')
        if not client_id:
            return Response({'success': False, 'error': 'Invalid token'}, status=401)

        # ✅ NO JOIN – currency_name from tendercash
        query = """
            SELECT
                tender_code,
                amount,
                currency_name
            FROM tendercash
            WHERE client_id = %s
            ORDER BY tender_code
        """

        with connection.cursor() as cursor:
            cursor.execute(query, [client_id])
            rows = cursor.fetchall()

        items = []
        total = 0.0

        for code, amount, currency_name in rows:
            amount = float(amount)
            total += amount
            items.append({
                "code": code,
                "amount": amount,
                "currency_name": currency_name
            })

        return Response({
            "success": True,
            "client_id": client_id,
            "data": {
                "user": None,
                "total": total,
                "items": items
            }
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)