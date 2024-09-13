from rest_framework import serializers

from .models import Cryptocurrency
from .models import HistoricalPrice


class CryptocurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Cryptocurrency
        fields = ["id", "coin_id", "name", "symbol", "description"]


class HistoricalPriceSerializer(serializers.ModelSerializer):
    """
    Serializer for the HistoricalPrice model.
    Provides fields for cryptocurrency, date, and all relevant price and volume information.
    """

    class Meta:
        model = HistoricalPrice
        fields = "__all__"
