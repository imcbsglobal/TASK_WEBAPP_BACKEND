from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
import jwt
from django.conf import settings
from collections import defaultdict


from collections import defaultdict
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
import jwt
from django.conf import settings


@api_view(['GET'])
def tender_cash_bytype(request):
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

        query = """
            SELECT
                i.type,
                t.tender_code,
                t.amount,
                t.currency_name
            FROM tendercash t
            LEFT JOIN acc_invmast i
                ON t.mslno = i.slno
               AND t.client_id = i.client_id
            WHERE t.client_id = %s
            ORDER BY i.type NULLS LAST
        """

        with connection.cursor() as cursor:
            cursor.execute(query, [client_id])
            rows = cursor.fetchall()

        grouped = defaultdict(lambda: {"total": 0.0, "items": []})

        for typ, code, amount, currency_name in rows:
            typ = typ or "UNKNOWN"
            amount = float(amount)

            grouped[typ]["items"].append({
                "code": code,
                "amount": amount,
                "currency_name": currency_name
            })

            grouped[typ]["total"] += amount

        data = []
        for typ, info in grouped.items():
            data.append({
                "type": typ,
                "total": info["total"],
                "items": info["items"]
            })

        return Response({
            "success": True,
            "client_id": client_id,
            "data": data
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)