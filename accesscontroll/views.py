from django.shortcuts import render
from django.conf import settings
import jwt
from rest_framework.response import Response
from .models import AllowedMenu


# Create your views here.

def decode_jwt_token(request):
    """Decode JWT token from Authorization header"""
    auth_header = request.META.get("HTTP_AUTHORIZATION")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload
    except Exception:
        return None
    

@api_view(["POST"])
def update_user_routes(request):
        payload = decode_jwt_token(request)
        if not payload:
            return Response({'error': 'Invalid or missing token'}, status=401)

        client_id = payload.get("client_id")
        username = payload.get("username")
        allowedMenuIds = request.data.get("allowedMenuIds", [])

        if not client_id:
            return Response({'error': 'Invalid or missing token'}, status=401)

        obj, created = AllowedMenu.objects.update_or_create(
        username=username,
        client_id=client_id,
        defaults={"allowedMenuIds": allowedMenuIds},
        )

        return Response({
        "success": True,
        "created": created,
        "allowedMenuIds": obj.allowedMenuIds
         })