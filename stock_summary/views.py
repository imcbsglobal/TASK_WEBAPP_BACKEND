from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
import jwt

from .models import StockSummary


def _get_client_id(request):
    """
    Decode JWT from Authorization header and return client_id.
    Returns (client_id, None) on success or (None, Response) on failure.
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION')

    if not auth_header or not auth_header.startswith('Bearer '):
        return None, Response(
            {'success': False, 'error': 'Missing or invalid authorization header'},
            status=401
        )

    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        client_id = payload.get('client_id')
        if not client_id:
            return None, Response(
                {'success': False, 'error': 'Invalid token: missing client_id'},
                status=401
            )
        return client_id, None

    except jwt.ExpiredSignatureError:
        return None, Response({'success': False, 'error': 'Token has expired'}, status=401)
    except jwt.InvalidTokenError as e:
        return None, Response({'success': False, 'error': f'Invalid token: {str(e)}'}, status=401)


@api_view(['GET'])
def get_stock_summary(request):
    """
    GET /api/stock-summary/
    Headers: Authorization: Bearer <token>

    Returns total_products and total_stock_value for the client.
    """
    try:
        client_id, err = _get_client_id(request)
        if err:
            return err

        try:
            summary = StockSummary.objects.get(client_id=client_id)
        except StockSummary.DoesNotExist:
            return Response(
                {'success': False, 'error': 'No stock summary found for this client'},
                status=404
            )

        return Response({
            'success': True,
            'data': {
                'total_products':    summary.total_products,
                'total_stock_value': float(summary.total_stock_value),
            }
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)