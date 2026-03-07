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
                s.type,
                t.tender_code,
                t.currency_name,
                SUM(t.amount) AS total_amount
            FROM tendercash t
            JOIN sales_today s
              ON s.slno = t.mslno
             AND s.client_id = t.client_id
            WHERE t.client_id = %s
            GROUP BY s.type, t.tender_code, t.currency_name
            ORDER BY s.type, t.tender_code
        """

        with connection.cursor() as cursor:
            cursor.execute(query, [client_id])
            rows = cursor.fetchall()

        grouped = {}
        grand_total = 0

        for typ, code, name, amount in rows:

            amount = float(amount)
            grand_total += amount

            if typ not in grouped:
                grouped[typ] = {
                    "type": typ,
                    "total": 0,
                    "split": []
                }

            grouped[typ]["split"].append({
                "code": code,
                "currency_name": name,
                "amount": amount
            })

            grouped[typ]["total"] += amount

        return Response({
            "success": True,
            "client_id": client_id,
            "grand_total": grand_total,
            "data": list(grouped.values())
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)