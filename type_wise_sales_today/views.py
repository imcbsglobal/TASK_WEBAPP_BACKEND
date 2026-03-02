from datetime import date

from django.conf import settings
from django.db.models import (
    Sum, Count, OuterRef, Subquery, F,
    Value, DecimalField
)
from django.db.models.functions import Coalesce

from rest_framework.decorators import api_view
from rest_framework.response import Response

import jwt

from app1.models import AccInvmast
from acc_sales_type.models import AccSalesType


@api_view(["GET"])
def type_wise_sales_today(request):

    # ==========================
    # 🔐 TOKEN VALIDATION
    # ==========================
    auth_header = request.META.get("HTTP_AUTHORIZATION")

    if not auth_header or not auth_header.startswith("Bearer "):
        return Response(
            {"success": False, "error": "Missing or invalid authorization header"},
            status=401
        )

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        client_id = payload.get("client_id")

        if not client_id:
            return Response(
                {"success": False, "error": "Invalid token: client_id missing"},
                status=401
            )

    except jwt.ExpiredSignatureError:
        return Response({"success": False, "error": "Token expired"}, status=401)
    except jwt.InvalidTokenError:
        return Response({"success": False, "error": "Invalid token"}, status=401)

    # ==========================
    # 📊 BUSINESS LOGIC
    # ==========================
    today = date.today()

    sales_type_name = AccSalesType.objects.filter(
        cd=OuterRef("modeofpayment"),
        client_id=client_id
    ).values("name")[:1]

    data = (
        AccInvmast.objects
        .filter(
            invdate=today,
            client_id=client_id,
            modeofpayment__isnull=False
        )
        .values(payment_type=F("modeofpayment"))
        .annotate(
            nettotal=Coalesce(
                Sum("nettotal"),
                Value(0),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            ),
            billcount=Count("id"),
            name=Coalesce(Subquery(sales_type_name), Value("Unknown"))
        )
        .order_by("payment_type")
    )

    return Response({
        "success": True,
        "client_id": client_id,
        "date": str(today),
        "data": list(data)
    })