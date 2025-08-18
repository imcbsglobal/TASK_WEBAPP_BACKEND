from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import jwt
from .models import PunchIn
from .serializers import PunchInSerializer
from app1.models import Misel  # import existing Misel

def get_client_id_from_token(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload.get('client_id')
    except Exception:
        return None

@api_view(['POST'])
def punch_in(request):
    client_id = get_client_id_from_token(request)
    if not client_id:
        return Response({'error': 'Invalid or missing token'}, status=401)

    firm_name = request.data.get('firm_name')
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')

    if not firm_name or not latitude or not longitude:
        return Response({'error': 'firm_name, latitude, longitude required'}, status=400)

    try:
        # Try to find the firm by firm_name and client_id
        firm = Misel.objects.get(firm_name=firm_name, client_id=client_id)
    except Misel.DoesNotExist:
        return Response({'error': 'Invalid firm for this client'}, status=404)

    # Check if a PunchIn entry already exists for this firm and client_id
    punch, created = PunchIn.objects.get_or_create(
        firm=firm,
        client_id=client_id,
        defaults={
            'latitude': latitude,
            'longitude': longitude
        }
    )

    # If the entry already exists, update the latitude and longitude
    if not created:
        punch.latitude = latitude
        punch.longitude = longitude
        punch.save()

    serializer = PunchInSerializer(punch)
    return Response({'success': True, 'data': serializer.data}, status=201 if created else 200)


from .models import PunchIn
from app1.models import Misel

@api_view(['GET'])
def get_firms(request):
    client_id = get_client_id_from_token(request)
    if not client_id:
        return Response({'error': 'Invalid or missing token'}, status=401)

    firms = Misel.objects.filter(client_id=client_id)

    data = []
    for firm in firms:
        # get latest punch-in record for this firm
        punch = PunchIn.objects.filter(firm=firm, client_id=client_id).order_by('-created_at').first()
        data.append({
            'id': firm.id,
            'firm_name': firm.firm_name,
            'latitude': float(punch.latitude) if punch else None,
            'longitude': float(punch.longitude) if punch else None,
        })

    return Response({'success': True, 'firms': data})
