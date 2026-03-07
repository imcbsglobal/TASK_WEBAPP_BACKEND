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

        query = """
            SELECT
                s.userid,
                t.tender_code,
                t.currency_name,
                SUM(t.amount) AS total_amount
            FROM tendercash t
            JOIN sales_today s
            ON s.slno = t.mslno
            WHERE t.client_id = %s
            GROUP BY s.userid, t.tender_code, t.currency_name
            ORDER BY s.userid, t.tender_code
        """

        with connection.cursor() as cursor:
            cursor.execute(query, [client_id])
            rows = cursor.fetchall()

        users = {}
        grand_total = 0

        for userid, code, name, amount in rows:
            amount = float(amount)
            grand_total += amount

            if userid not in users:
                users[userid] = {
                    "userid": userid,
                    "tenders": [],
                    "total": 0
                }

            users[userid]["tenders"].append({
                "code": code,
                "currency_name": name,
                "amount": amount
            })

            users[userid]["total"] += amount

        return Response({
            "success": True,
            "client_id": client_id,
            "grand_total": grand_total,
            "users": list(users.values())
        })

    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)