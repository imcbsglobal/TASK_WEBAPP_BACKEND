from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
import jwt
from django.conf import settings
from collections import defaultdict


@api_view(['GET'])
def tender_cash_bytype(request):
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

        client_id = payload.get('client_id')
        if not client_id:
            return Response({'success': False, 'error': 'Invalid token payload'}, status=401)

        # ✅ TYPE-WISE QUERY
        query = """
            SELECT
                i.type,
                i.userid,
                t.tender_code,
                t.amount
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

        # 🔁 Group by TYPE
        grouped = defaultdict(lambda: {
            "total": 0.0,
            "items": []
        })

        for typ, userid, code, amount in rows:
            typ = typ if typ else "UNKNOWN"
            userid = userid if userid else None
            amount = float(amount)

            grouped[typ]["items"].append({
                "user": userid,
                "code": code,
                "amount": amount
            })
            grouped[typ]["total"] += amount

        # 🔢 Final response
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
        return Response(
            {'success': False, 'error': str(e)},
            status=500
        )