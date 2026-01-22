from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import EventLog
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
def get_eventlog(request):
    client_id = get_client_from_token(request)

    if not client_id:
        return Response({"error": "Invalid or missing token"}, status=401)

    qs = EventLog.objects.filter(client_id=client_id).order_by("-id")

    data = [
        {
            "uid": i.uid,
            "edate": i.edate,
            "etime": i.etime,
            "sevent": i.sevent
        }
        for i in qs
    ]

    return Response({
        "success": True,
        "client_id": client_id,
        "count": len(data),
        "data": data
    })
