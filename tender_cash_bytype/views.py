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
                COALESCE(i.type, 'UNKNOWN') AS type,
                t.tender_code,
                t.currency_name,
                SUM(t.amount) AS total_amount
            FROM tendercash t
            LEFT JOIN acc_invmast i
                ON t.mslno = i.slno
               AND t.client_id = i.client_id
            WHERE t.client_id = %s
            GROUP BY COALESCE(i.type, 'UNKNOWN'), t.tender_code, t.currency_name
            ORDER BY COALESCE(i.type, 'UNKNOWN'), t.tender_code
        """

        with connection.cursor() as cursor:
            cursor.execute(query, [client_id])
            rows = cursor.fetchall()

        grouped = {}

        for typ, code, currency_name, total_amount in rows:
            total_amount = float(total_amount)

            if typ not in grouped:
                grouped[typ] = {
                    "type": typ,
                    "total": 0.0,
                    "items": []
                }

            grouped[typ]["items"].append({
                "code": code,
                "currency_name": currency_name,
                "total_amount": total_amount
            })

            grouped[typ]["total"] += total_amount

        return Response({
            "success": True,
            "client_id": client_id,
            "data": list(grouped.values())
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
    


    # jikk