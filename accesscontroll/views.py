from django.shortcuts import render
from django.conf import settings
import jwt

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
