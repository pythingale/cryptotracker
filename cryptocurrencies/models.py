from django.db import models


class Cryptocurrency(models.Model):
    coin_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


from django.db import models


class HistoricalPrice(models.Model):
    cryptocurrency = models.ForeignKey(
        Cryptocurrency,
        on_delete=models.CASCADE,
        related_name="prices",
    )
    date = models.DateField()
    open_price = models.DecimalField(max_digits=20, decimal_places=4)
    high_price = models.DecimalField(max_digits=20, decimal_places=4)
    low_price = models.DecimalField(max_digits=20, decimal_places=4)
    close_price = models.DecimalField(max_digits=20, decimal_places=4)
    volume_from = models.DecimalField(max_digits=30, decimal_places=10)
    volume_to = models.DecimalField(max_digits=30, decimal_places=10)

    class Meta:
        unique_together = ["cryptocurrency", "date"]

    def __str__(self):
        return f"{self.cryptocurrency.name} on {self.date}"
