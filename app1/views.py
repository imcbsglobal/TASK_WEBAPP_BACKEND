# views.py - With debugging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import AccUser, Misel
from datetime import datetime, timedelta
import jwt
from django.conf import settings
from .models import AccUser, Misel, AccMaster, AccLedgers, AccInvmast,CashAndBankAccMaster
from accesscontroll.models import AllowedMenu




@api_view(['POST'])
def login(request):
    username     = request.data.get('username')
    password     = request.data.get('password')
    account_code = request.data.get('accountcode', '')
    client_id    = request.data.get('client_id')

    if not username or not password or not client_id:
        return Response({'success': False, 'error': 'Missing credentials'}, status=400)

    try:
        # Include client_id in the initial query to avoid MultipleObjectsReturned error
        user = AccUser.objects.get(id=username, password=password, client_id=client_id)
    except AccUser.DoesNotExist:
        return Response({'success': False, 'error': 'Invalid credentials'}, status=401)
    except AccUser.MultipleObjectsReturned:
        return Response({'success': False, 'error': 'Multiple users found with these credentials'}, status=401)

    # Remove the redundant client_id check since it's now part of the query
    # if client_id != user.client_id:
    #     return Response({'success': False, 'error': 'Invalid client ID'}, status=401)

    if account_code and account_code != user.accountcode:
        return Response({'success': False, 'error': 'Invalid account code'}, status=401)
    
    role = "Admin" if (user.role and user.role.strip().lower() == "level 3") else "User"


# replace this with menuconfig function
    if role == "Admin":
       allowedMenuIds= [
     "item-details",
    "bank-cash",
    "cash-book",
    "bank-book",
    "debtors",
    "company",
    "punch-in",
    "location-capture",
    "punch-in-action",
    "area-assign",
    "master",
    "user-menu",
    "settings"
    ]
    else :    
        try:
        # Fetch allowed menu IDs for the user
            allowedMenuIds = AllowedMenu.objects.filter(
            user_id=user.id, client_id=client_id
            ).values_list('allowedMenuIds',flat=True).first()


        # If no allowed menus found, default to ['company']
            if not allowedMenuIds:
                allowedMenuIds = ['company']

        except AllowedMenu.DoesNotExist:
        # This usually won't trigger with filter(), but included for safety
            allowedMenuIds = ['company']

        except Exception as e:
        # Log the error in production
            print(f"Error fetching AllowedMenuIds: {e}")
            return Response({'success': False, "error": "Error fetching AllowedMenuIds"}, status=500)

     

    # Create custom JWT token with user data
    payload = {
        'user_id': user.id,
        'username': user.id,
        'client_id': user.client_id,
        'role': role,
        'accountcode': user.accountcode,
        'exp': datetime.utcnow() + timedelta(hours=24),  # Token expires in 24 hours
        'iat': datetime.utcnow(),
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    return Response({
        'success': True,
        'user': {
            'username': user.id,
            'role': role,
            'client_id': user.client_id,
            'accountcode': user.accountcode,
            'login_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'allowedMenuIds':allowedMenuIds

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







@api_view(['GET'])
def get_debtors_data(request):
    """Get joined data from AccMaster, AccLedgers, and AccInvmast tables for logged user's client_id with pagination and search"""
    from django.db import connection
    from django.core.paginator import Paginator
    import math
    
    try:
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'success': False, 'error': 'Missing or invalid authorization header'}, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode the JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            client_id = payload.get('client_id')
            
            if not client_id:
                return Response({'success': False, 'error': 'Invalid token: missing client_id'}, status=401)
                
        except jwt.ExpiredSignatureError:
            return Response({'success': False, 'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError as e:
            return Response({'success': False, 'error': f'Invalid token: {str(e)}'}, status=401)
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        search_term = request.GET.get('search', '').strip()
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build the WHERE clause for search
        search_condition = ""
        search_params = [client_id]
        
        if search_term:
            # Search in name, code, and place fields (case-insensitive)
            search_condition = """
                AND (
                    UPPER(am.name) LIKE UPPER(%s) OR 
                    UPPER(am.code) LIKE UPPER(%s) OR 
                    UPPER(am.place) LIKE UPPER(%s)
                )
            """
            search_pattern = f"%{search_term}%"
            search_params.extend([search_pattern, search_pattern, search_pattern])
        
        # First, get the total count with search filter
        count_query = f"""
            SELECT COUNT(DISTINCT am.code)
            FROM acc_master am
            WHERE am.client_id = %s
            {search_condition}
        """
        
        with connection.cursor() as cursor:
            cursor.execute(count_query, search_params)
            total_records = cursor.fetchone()[0]
        
        # Calculate total pages
        total_pages = math.ceil(total_records / page_size) if total_records > 0 else 1
        
        # Main query with search filter
        main_query = f"""
            SELECT 
                am.code,
                am.name,
                am.opening_balance,
                am.debit as master_debit,
                am.credit as master_credit,
                am.place,
                am.phone2,
                am.openingdepartment
            FROM acc_master am
            WHERE am.client_id = %s
            {search_condition}
            ORDER BY am.code
            LIMIT %s OFFSET %s
        """
        
        # Add limit and offset parameters
        query_params = search_params + [page_size, offset]
        
        with connection.cursor() as cursor:
            cursor.execute(main_query, query_params)
            columns = [col[0] for col in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                row_data = dict(zip(columns, row))
                results.append(row_data)
        
        return Response({
            'success': True, 
            'data': results,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_records': total_records,
                'page_size': page_size,
                'has_next': page < total_pages,
                'has_previous': page > 1
            },
            'search_applied': bool(search_term),
            'search_term': search_term
        })
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['GET'])
def get_ledger_details(request):
    """Get detailed ledger entries for a specific account"""
    try:
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'success': False, 'error': 'Missing or invalid authorization header'}, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode the JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            client_id = payload.get('client_id')
            
            if not client_id:
                return Response({'success': False, 'error': 'Invalid token: missing client_id'}, status=401)
                
        except jwt.ExpiredSignatureError:
            return Response({'success': False, 'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError as e:
            return Response({'success': False, 'error': f'Invalid token: {str(e)}'}, status=401)
        
        # Get account code from query parameters
        account_code = request.GET.get('account_code')
        if not account_code:
            return Response({'success': False, 'error': 'Missing account_code parameter'}, status=400)
        
        # Fetch all ledger entries for the specific account
        ledger_entries = AccLedgers.objects.filter(
            code=account_code, 
            client_id=client_id
        ).values(
            'entry_date', 'particulars', 'voucher_no', 'entry_mode', 
            'debit', 'credit', 'narration'
        ).order_by('-entry_date', '-id')
        
        return Response({
            'success': True, 
            'data': list(ledger_entries)
        })
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
def get_invoice_details(request):
    """Get detailed invoice entries for a specific account"""
    try:
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'success': False, 'error': 'Missing or invalid authorization header'}, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode the JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            client_id = payload.get('client_id')
            
            if not client_id:
                return Response({'success': False, 'error': 'Invalid token: missing client_id'}, status=401)
                
        except jwt.ExpiredSignatureError:
            return Response({'success': False, 'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError as e:
            return Response({'success': False, 'error': f'Invalid token: {str(e)}'}, status=401)
        
        # Get account code from query parameters
        account_code = request.GET.get('account_code')
        if not account_code:
            return Response({'success': False, 'error': 'Missing account_code parameter'}, status=400)
        
        # Fetch all invoice entries for the specific account
        invoice_entries = AccInvmast.objects.filter(
            customerid=account_code, 
            client_id=client_id
        ).values(
            'invdate', 'bill_ref', 'modeofpayment', 
            'nettotal', 'paid'
        ).order_by('-invdate', '-id')
        
        return Response({
            'success': True, 
            'data': list(invoice_entries)
        })
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
    





@api_view(['GET'])
def get_cash_book_data(request):
    """Get cash book data - accounts with super_code='CASH' for logged user's client_id"""
    try:
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'success': False, 'error': 'Missing or invalid authorization header'}, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode the JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            client_id = payload.get('client_id')
            
            if not client_id:
                return Response({'success': False, 'error': 'Invalid token: missing client_id'}, status=401)
                
        except jwt.ExpiredSignatureError:
            return Response({'success': False, 'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError as e:
            return Response({'success': False, 'error': f'Invalid token: {str(e)}'}, status=401)
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get cash accounts (super_code='CASH')
        cash_accounts = CashAndBankAccMaster.objects.filter(
            client_id=client_id,
            super_code='CASH'
        ).values(
            'code', 'name', 'opening_balance', 'opening_date',
            'debit', 'credit'
        ).order_by('code')[offset:offset + page_size]
        
        # Get total count for pagination
        total_records = CashAndBankAccMaster.objects.filter(
            client_id=client_id,
            super_code='CASH'
        ).count()
        
        import math
        total_pages = math.ceil(total_records / page_size)
        
        return Response({
            'success': True, 
            'data': list(cash_accounts),
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_records': total_records,
                'page_size': page_size,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
        })
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
def get_bank_book_data(request):
    """Get bank book data - accounts with super_code='BANK' for logged user's client_id"""
    try:
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'success': False, 'error': 'Missing or invalid authorization header'}, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode the JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            client_id = payload.get('client_id')
            
            if not client_id:
                return Response({'success': False, 'error': 'Invalid token: missing client_id'}, status=401)
                
        except jwt.ExpiredSignatureError:
            return Response({'success': False, 'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError as e:
            return Response({'success': False, 'error': f'Invalid token: {str(e)}'}, status=401)
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get bank accounts (super_code='BANK')
        bank_accounts = CashAndBankAccMaster.objects.filter(
            client_id=client_id,
            super_code='BANK'
        ).values(
            'code', 'name', 'opening_balance', 'opening_date',
            'debit', 'credit'
        ).order_by('code')[offset:offset + page_size]
        
        # Get total count for pagination
        total_records = CashAndBankAccMaster.objects.filter(
            client_id=client_id,
            super_code='BANK'
        ).count()
        
        import math
        total_pages = math.ceil(total_records / page_size)
        
        return Response({
            'success': True, 
            'data': list(bank_accounts),
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_records': total_records,
                'page_size': page_size,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
        })
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
    






@api_view(['GET'])
def get_cash_ledger_details(request):
    """Get detailed ledger entries for a specific cash account"""
    try:
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'success': False, 'error': 'Missing or invalid authorization header'}, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode the JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            client_id = payload.get('client_id')
            
            if not client_id:
                return Response({'success': False, 'error': 'Invalid token: missing client_id'}, status=401)
                
        except jwt.ExpiredSignatureError:
            return Response({'success': False, 'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError as e:
            return Response({'success': False, 'error': f'Invalid token: {str(e)}'}, status=401)
        
        # Get account code from query parameters
        account_code = request.GET.get('account_code')
        if not account_code:
            return Response({'success': False, 'error': 'Missing account_code parameter'}, status=400)
        
        # Verify that this is a cash account before fetching ledger data
        cash_account_exists = CashAndBankAccMaster.objects.filter(
            code=account_code,
            client_id=client_id,
            super_code='CASH'
        ).exists()
        
        if not cash_account_exists:
            return Response({'success': False, 'error': 'Cash account not found'}, status=404)
        
        # Fetch all ledger entries for the specific cash account
        ledger_entries = AccLedgers.objects.filter(
            code=account_code, 
            client_id=client_id
        ).values(
            'entry_date', 'particulars', 'voucher_no', 'entry_mode', 
            'debit', 'credit', 'narration'
        ).order_by('-entry_date', '-id')
        
        return Response({
            'success': True, 
            'data': list(ledger_entries)
        })
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
def get_bank_ledger_details(request):
    """Get detailed ledger entries for a specific bank account"""
    try:
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'success': False, 'error': 'Missing or invalid authorization header'}, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode the JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            client_id = payload.get('client_id')
            
            if not client_id:
                return Response({'success': False, 'error': 'Invalid token: missing client_id'}, status=401)
                
        except jwt.ExpiredSignatureError:
            return Response({'success': False, 'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError as e:
            return Response({'success': False, 'error': f'Invalid token: {str(e)}'}, status=401)
        
        # Get account code from query parameters
        account_code = request.GET.get('account_code')
        if not account_code:
            return Response({'success': False, 'error': 'Missing account_code parameter'}, status=400)
        
        # Verify that this is a bank account before fetching ledger data
        bank_account_exists = CashAndBankAccMaster.objects.filter(
            code=account_code,
            client_id=client_id,
            super_code='BANK'
        ).exists()
        
        if not bank_account_exists:
            return Response({'success': False, 'error': 'Bank account not found'}, status=404)
        
        # Fetch all ledger entries for the specific bank account
        ledger_entries = AccLedgers.objects.filter(
            code=account_code, 
            client_id=client_id
        ).values(
            'entry_date', 'particulars', 'voucher_no', 'entry_mode', 
            'debit', 'credit', 'narration'
        ).order_by('-entry_date', '-id')
        
        return Response({
            'success': True, 
            'data': list(ledger_entries)
        })
        
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
