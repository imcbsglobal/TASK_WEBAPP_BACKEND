# views.py - With debugging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import AccUser, Misel
from datetime import datetime, timedelta
import jwt
from django.conf import settings

@api_view(['POST'])
def login(request):
    username     = request.data.get('username')
    password     = request.data.get('password')
    account_code = request.data.get('accountcode', '')
    client_id    = request.data.get('client_id')

    if not username or not password or not client_id:
        return Response({'success': False, 'error': 'Missing credentials'}, status=400)

    try:
        user = AccUser.objects.get(id=username, password=password)
    except AccUser.DoesNotExist:
        return Response({'success': False, 'error': 'Invalid credentials'}, status=401)

    if client_id != user.client_id:
        return Response({'success': False, 'error': 'Invalid client ID'}, status=401)

    if account_code and account_code != user.accountcode:
        return Response({'success': False, 'error': 'Invalid account code'}, status=401)

    role = "Admin" if (user.role and user.role.strip().lower() == "level 3") else "User"

    # Create custom JWT token with user data
    payload = {
        'user_id': user.id,
        'username': user.id,
        'client_id': user.client_id,
        'role': role,
        'accountcode': user.accountcode,
        'exp': datetime.utcnow() + timedelta(hours=24),  # Token expires in 24 hours
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    return Response({
        'success': True,
        'user': {
            'username': user.id,
            'role': role,
            'client_id': user.client_id,
            'accountcode': user.accountcode,
            'login_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        'token': token,
    })

@api_view(['GET'])
def get_users(request):
    qs = AccUser.objects.all().values('id', 'role', 'accountcode', 'client_id')
    return Response({'users': list(qs)})

@api_view(['GET'])
def get_misel_data(request):
    try:
        # Debug: Print all headers
        print("=== DEBUG: All request headers ===")
        for key, value in request.META.items():
            if 'HTTP_' in key or key in ['CONTENT_TYPE', 'CONTENT_LENGTH']:
                print(f"{key}: {value}")
        
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        print(f"=== DEBUG: Authorization header: {auth_header} ===")
        
        if not auth_header:
            return Response({
                'success': False, 
                'error': 'Missing authorization header',
                'debug': 'No HTTP_AUTHORIZATION found in request.META'
            }, status=401)
        
        if not auth_header.startswith('Bearer '):
            return Response({
                'success': False, 
                'error': 'Invalid authorization header format',
                'debug': f'Header value: {auth_header}'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        print(f"=== DEBUG: Extracted token: {token[:50]}... ===")
        
        try:
            # Decode the JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            print(f"=== DEBUG: Token payload: {payload} ===")
            client_id = payload.get('client_id')
            
            if not client_id:
                return Response({'success': False, 'error': 'Invalid token: missing client_id'}, status=401)
                
        except jwt.ExpiredSignatureError:
            return Response({'success': False, 'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError as e:
            return Response({'success': False, 'error': f'Invalid token: {str(e)}'}, status=401)
        
        # Fetch misel data for the client
        misel_data = Misel.objects.filter(client_id=client_id).values()
        return Response({'success': True, 'data': list(misel_data)})
        
    except Exception as e:
        print(f"=== DEBUG: Exception: {str(e)} ===")
        return Response({'success': False, 'error': str(e)}, status=500)
    


@api_view(['GET'])
def test_token(request):
    """Test endpoint to check if token is being sent correctly"""
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    
    return Response({
        'auth_header': auth_header,
        'all_headers': {k: v for k, v in request.META.items() if 'HTTP_' in k},
        'method': request.method,
    })
