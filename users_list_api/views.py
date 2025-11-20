from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from app1.models import AccUser
import jwt
from django.conf import settings


@api_view(['GET'])
def users_list(request):
    """Return users list filtered by logged user's client_id"""

    # Get Token
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response({'success': False, 'error': 'Missing or invalid token'}, status=401)

    token = auth_header.split(" ")[1]

    try:
        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        client_id = payload.get('client_id')

        if not client_id:
            return Response({'success': False, 'error': 'Invalid token'}, status=401)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=401)

    # Filter users by client_id
    qs = AccUser.objects.filter(client_id=client_id).values('id', 'role', 'client_id')

    return Response({
        'success': True,
        'users': list(qs)
    })
