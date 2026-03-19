from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import PDC
from app1.models import AccMaster   # ✅ import acc master
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

    # ✅ get all party codes
    party_codes = [i.party for i in qs if i.party]

    # ✅ fetch account names in single query
    accounts = AccMaster.objects.filter(
        code__in=party_codes,
        client_id=client_id
    )

    # ✅ create map {code: name}
    acc_map = {a.code: a.name for a in accounts}

    data = []

    for i in qs:
        data.append({
            "colndate": i.colndate,
            "party": acc_map.get(i.party, i.party),   # ✅ NAME instead of CODE
            "amount": i.amount,
            "chequedate": i.chequedate,
            "chequeno": i.chequeno,
            "colnstatus": i.colnstatus,
            "status": i.status,
        })

    return Response({
        "success": True,
        "client_id": client_id,
        "count": len(data),
        "data": data
    })