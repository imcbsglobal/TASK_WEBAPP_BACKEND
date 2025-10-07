from django.shortcuts import render

# Create your views here.
# DebtorsAPI/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from app1.models import AccMaster
import jwt
from django.conf import settings

@api_view(['GET'])
def get_debtors_list(request):
    """Return all debtors with Balance > 0 (Balance = debit - credit)"""
    try:
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'success': False, 'error': 'Missing or invalid authorization header'}, status=401)
        
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            client_id = payload.get('client_id')
        except jwt.ExpiredSignatureError:
            return Response({'success': False, 'error': 'Token expired'}, status=401)
        except jwt.InvalidTokenError:
            return Response({'success': False, 'error': 'Invalid token'}, status=401)

        # Get all accounts where Balance > 0
        debtors = (
            AccMaster.objects.filter(client_id=client_id)
            .values('code', 'name', 'place', 'phone2', 'debit', 'credit')
        )

        result = []
        for d in debtors:
            balance = float(d['debit'] or 0) - float(d['credit'] or 0)
            if balance > 0:
                result.append({
                    'code': d['code'],
                    'name': d['name'],
                    'place': d['place'],
                    'phone': d['phone2'],
                    'balance': round(balance, 2),
                })

        return Response({'success': True, 'data': result})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
