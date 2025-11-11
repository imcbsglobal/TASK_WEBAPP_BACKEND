from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import SalesReturnReport

@api_view(['GET'])
def get_sales_return_data(request):
    """
    Get all sales return report data for a specific client_id
    Example: /api/sales-return/get-data/?client_id=abc123
    """
    try:
        client_id = request.GET.get('client_id')

        if not client_id:
            return Response({
                'success': False,
                'error': 'Missing client_id parameter'
            }, status=400)

        # Fetch all data for that client_id
        sales_returns = SalesReturnReport.objects.filter(client_id=client_id).values(
            'date', 'invno', 'net', 'customername', 'userid'
        ).order_by('-date', '-invno')

        return Response({
            'success': True,
            'client_id': client_id,
            'count': sales_returns.count(),
            'data': list(sales_returns)
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
