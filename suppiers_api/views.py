from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import AccMaster  # we'll import the existing model location below
# If your AccMaster model is in project app.models (as in your uploaded models.py),
# adjust import path accordingly:
# from your_app.models import AccMaster

# If AccMaster is in the root app's models.py (based on your upload), use:
# from <your_root_app_name>.models import AccMaster
# Replace <your_root_app_name> with the app name where models.py lives.

@api_view(['GET'])
def suppliers_list(request):
    """
    Returns list of suppliers from acc_master where super_code = 'SUNCR'.
    Fields returned: code,name,opening_balance,debit,credit,place,phone2,
                    openingdepartment,area,client_id,super_code
    Optional query param:
      - client_id (string): if provided, will filter by client_id as well.
    """
    try:
        client_id = request.GET.get('client_id', None)

        qs = AccMaster.objects.filter(super_code='SUNCR')
        if client_id:
            qs = qs.filter(client_id=client_id)

        # return only requested fields
        data = qs.values(
            'code',
            'name',
            'opening_balance',
            'debit',
            'credit',
            'place',
            'phone2',
            'openingdepartment',
            'area',
            'client_id',
            'super_code'
        ).order_by('code')

        return Response({'success': True, 'data': list(data)})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
