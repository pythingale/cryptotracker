from django.db.models import Max
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from cryptocurrencies.models import Cryptocurrency
from cryptocurrencies.models import HistoricalPrice
from cryptocurrencies.serializers import HistoricalPriceSerializer
from cryptocurrencies.utils import calculate_rsi


class HistoricalPriceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling historical price data for cryptocurrencies.
    Provides actions to retrieve historical prices, calculate daily returns, and calculate the RSI.
    """

    queryset = HistoricalPrice.objects.all()
    serializer_class = HistoricalPriceSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "symbol",
                OpenApiTypes.STR,
                description="Cryptocurrency symbol",
                required=True,
            ),
            OpenApiParameter(
                "start_date",
                OpenApiTypes.DATE,
                description="Start date (YYYY-MM-DD)",
                required=True,
            ),
            OpenApiParameter(
                "end_date",
                OpenApiTypes.DATE,
                description="End date (YYYY-MM-DD)",
                required=True,
            ),
        ],
        responses=HistoricalPriceSerializer(many=True),
    )
    @action(detail=False, methods=["get"], url_path="price-range")
    def get_price_range(self, request):
        """
        Retrieve historical prices for a specific cryptocurrency within a date range.
        """
        symbol = request.query_params.get("symbol")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not symbol or not start_date or not end_date:
            return Response(
                {
                    "error": "Please provide 'symbol', 'start_date', and 'end_date' parameters.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            crypto = (
                Cryptocurrency.objects.filter(symbol=symbol)
                .annotate(max_volume=Max("prices__volume_to"))
                .order_by("-max_volume")
                .first()
            )

            if not crypto:
                return Response(
                    {"error": "Cryptocurrency not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            historical_data = HistoricalPrice.objects.filter(
                cryptocurrency=crypto,
                date__range=[start_date, end_date],
            ).order_by("date")

            serializer = self.get_serializer(historical_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "symbol",
                OpenApiTypes.STR,
                description="Cryptocurrency symbol",
                required=True,
            ),
        ],
        responses={
            "200": OpenApiTypes.NUMBER,
            "400": OpenApiTypes.OBJECT,
            "404": OpenApiTypes.OBJECT,
        },
    )
    @action(detail=False, methods=["get"], url_path="daily-return")
    def get_daily_return(self, request):
        """
        Calculate and retrieve the daily return for the last two days.
        """
        symbol = request.query_params.get("symbol")

        if not symbol:
            return Response(
                {"error": "Please provide 'symbol' parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            crypto = (
                Cryptocurrency.objects.filter(symbol=symbol)
                .annotate(max_volume=Max("prices__volume_to"))
                .order_by("-max_volume")
                .first()
            )

            if not crypto:
                return Response(
                    {"error": "Cryptocurrency not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            historical_data = HistoricalPrice.objects.filter(
                cryptocurrency=crypto,
            ).order_by("-date")[:2]

            if len(historical_data) < 2:
                return Response(
                    {"error": "Not enough data to calculate daily return."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            price_today = historical_data[0].close_price
            price_yesterday = historical_data[1].close_price
            daily_return = (price_today - price_yesterday) / price_yesterday

            return Response(
                {"symbol": symbol, "daily_return": daily_return},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "symbol",
                OpenApiTypes.STR,
                description="Cryptocurrency symbol",
                required=True,
            ),
            OpenApiParameter(
                "period",
                OpenApiTypes.INT,
                description="RSI calculation period (default: 14)",
                required=False,
            ),
        ],
        responses={
            "200": OpenApiTypes.OBJECT,
            "400": OpenApiTypes.OBJECT,
            "404": OpenApiTypes.OBJECT,
        },
    )
    @action(detail=False, methods=["get"], url_path="rsi")
    def get_rsi(self, request):
        """
        Calculate and retrieve the RSI for a given period (default 14 days).
        """
        symbol = request.query_params.get("symbol")
        period = int(request.query_params.get("period", 14))

        if not symbol:
            return Response(
                {"error": "Please provide 'symbol' parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Find the cryptocurrency with the most volume for the symbol
            crypto = (
                Cryptocurrency.objects.filter(symbol=symbol)
                .annotate(max_volume=Max("prices__volume_to"))
                .order_by("-max_volume")
                .first()
            )

            if not crypto:
                return Response(
                    {"error": "Cryptocurrency not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Fetch historical data for the last 'period' days
            historical_data = HistoricalPrice.objects.filter(
                cryptocurrency=crypto,
            ).order_by("-date")[: period + 1]

            if len(historical_data) < period + 1:
                return Response(
                    {"error": "Not enough data to calculate RSI."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Extract the closing prices
            close_prices = [
                item.close_price for item in historical_data[::-1]
            ]  # Reverse to keep oldest to newest

            # Calculate RSI
            rsi_data = calculate_rsi(close_prices, period)

            return Response(
                {
                    "symbol": symbol,
                    "period": period,
                    "gains": rsi_data["gains"],
                    "losses": rsi_data["losses"],
                    "RS": rsi_data["RS"],
                    "RSI": rsi_data["RSI"],
                    "interpretation": rsi_data["interpretation"],
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
