from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cryptocurrency
from .serializers import CryptocurrencySerializer
from .tasks import fetch_cryptocurrencies


class CryptocurrencyUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Trigger the Celery task to fetch and update cryptocurrencies
        task_result = fetch_cryptocurrencies.delay()

        result_data = task_result.get(timeout=120)

        if result_data["new_cryptos"]:
            return Response(
                {
                    "status": "Success",
                    "message": f"New added: {', '.join(result_data['new_cryptos'])}",
                    "existing_cryptocurrencies": result_data["existing_cryptos"],
                    "total_cryptocurrencies": result_data["total_cryptos"],
                },
            )
        return Response(
            {
                "status": "Success",
                "message": "No new cryptocurrencies added.",
                "existing_cryptocurrencies": result_data["existing_cryptos"],
                "total_cryptocurrencies": result_data["total_cryptos"],
            },
        )


class CryptocurrencyViewSet(viewsets.ModelViewSet):
    queryset = Cryptocurrency.objects.all()
    serializer_class = CryptocurrencySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name", "symbol", "description"]
    filterset_fields = ["name", "symbol"]
