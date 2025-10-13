from django.shortcuts import render
from django.conf import settings
import jwt
from rest_framework.response import Response
from .models import AllowedMenu
from rest_framework.decorators import api_view
from rest_framework import status

    # allowedMenuIds===
    #  "item-details",
    # "bank-cash",
    # "cash-book",
    # "bank-book",
    # "debtors",
    # "company",
    # "punch-in",
    # "location-capture",
    # "punch-in-action",
    # "area-assign"
    # "master",
    # "user-menu",
    # "settings"

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
def update_user_menu(request):
    try:
            payload = decode_jwt_token(request)
            if not payload:
                return Response({'error': 'Invalid or missing token'}, status=401)
            
            role = payload.get('role')
            print(role)
            if role.lower() != 'admin':
                return Response(
                {"detail": "Only admin can update this."},
                status=status.HTTP_403_FORBIDDEN
                )

            client_id = payload.get("client_id")
            username = request.data.get("user_id")
            allowedMenuIds = request.data.get("allowedMenuIds", [])

            if not client_id:
                return Response({'error': 'Invalid or missing token'}, status=401)

            obj, created = AllowedMenu.objects.update_or_create(
            user_id=username,
            client_id=client_id,
            defaults={"allowedMenuIds": allowedMenuIds},
            )

            return Response({
            "success": True,
            "created": created,
            "allowedMenuIds": obj.allowedMenuIds
            })

    except Exception as e:
        return Response(
            {'error': 'An unexpected error occurred. Please try again later.'}, 
        )
    

@api_view(['GET'])

def get_user_menus(request):
        
    try:
            payload = decode_jwt_token(request)
            if not payload:
                return Response({'error': 'Invalid or missing token'}, status=401)
            
            role = payload.get('role')
            # print(role ,"xio" if role == 'Admin' else "umn")
            if role.lower() != 'admin':
                return Response(
                {"detail": "Only admin can get menus."},
                status=status.HTTP_403_FORBIDDEN
                )
            # client_id from admin && username from req.data body
            client_id = payload.get("client_id")
            # username = request.data.get("user_id")
            username = request.GET.get("user_id")

            records = AllowedMenu.objects.filter(user_id=username,
            client_id=client_id
            ).first()

            if not records:
                return Response({
                    "success": True,
                    "user": username,
                    "allowedMenuIds": ["company"]
                }, status=200)

            
            
            return Response({
            "success": True,
            "user":username,
            "allowedMenuIds": records.allowedMenuIds
            },status=200)

            
    except Exception as e:
        return Response(
        {'error': f'An unexpected error occurred while getting the user menu: {e}'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

            
