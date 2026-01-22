from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import PDC
import jwt
from django.conf import settings


def get_client_from_token(request):
    auth = request.headers.get("Authorization")

    if not auth or not auth.startswith("Bearer "):
        return None

    token = auth.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload.get("client_id")
    except Exception:
        return None


@api_view(["GET"])
def get_pdc(request):
    client_id = get_client_from_token(request)

    if not client_id:
        return Response({"error": "Invalid or missing token"}, status=401)

    qs = PDC.objects.filter(client_id=client_id).order_by("-id")

    data = [
        {
            "colndate": i.colndate,
            "party": i.party,
            "amount": i.amount,
            "chequedate": i.chequedate,
            "chequeno": i.chequeno,
            "colnstatus": i.colnstatus,
            "status": i.status,
        }
        for i in qs
    ]

    return Response({
        "success": True,
        "client_id": client_id,
        "count": len(data),
        "data": data
    })
