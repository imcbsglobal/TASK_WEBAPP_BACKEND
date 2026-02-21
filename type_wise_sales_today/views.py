from datetime import date
from django.db.models import Sum, Count, OuterRef, Subquery, F
from rest_framework.decorators import api_view
from rest_framework.response import Response
import jwt
from django.conf import settings

from app1.models import AccInvmast
from acc_sales_type.models import AccSalesType


@api_view(["GET"])
def type_wise_sales_today(request):
    """
    API: Type Wise Sales Today (Token Protected)

    Token: REQUIRED
    Client Scope: Logged-in client_id only

    Join Condition:
      acc_invmast.modeofpayment = acc_sales_types.cd

    Response Fields:
      1. type
      2. nettotal
      3. billcount
      4. name
    """

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

    # Subquery to fetch sales type name
    sales_type_name = AccSalesType.objects.filter(
        cd=OuterRef("modeofpayment"),
        client_id=client_id
    ).values("name")[:1]

    data = (
        AccInvmast.objects
        .filter(
            invdate=today,
            client_id=client_id
        )
        .values(type=F("modeofpayment"))
        .annotate(
            nettotal=Sum("nettotal"),
            billcount=Count("id"),
            name=Subquery(sales_type_name)
        )
        .order_by("type")
    )

    return Response({
        "success": True,
        "client_id": client_id,
        "date": str(today),
        "data": list(data)
    })