from django.contrib import admin

from .models import Cryptocurrency
from .models import HistoricalPrice


@admin.register(Cryptocurrency)
class CryptocurrencyAdmin(admin.ModelAdmin):
    list_display = ("name", "symbol")
    search_fields = ("name", "symbol")
    ordering = ("name",)


@admin.register(HistoricalPrice)
class HistoricalPriceAdmin(admin.ModelAdmin):
    list_display = (
        "cryptocurrency",
        "date",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume_from",
        "volume_to",
    )
    list_filter = ("cryptocurrency", "date")
    search_fields = ("cryptocurrency__name", "date")
    ordering = ("-date",)
    date_hierarchy = "date"
