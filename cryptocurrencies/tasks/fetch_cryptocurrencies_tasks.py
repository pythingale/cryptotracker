import pandas as pd
import requests
from celery import shared_task
from django.db import IntegrityError

from cryptocurrencies.models import Cryptocurrency


@shared_task
def fetch_cryptocurrencies():
    url = "https://min-api.cryptocompare.com/data/all/coinlist"
    response = requests.get(url, timeout=60)
    data = response.json()["Data"]

    new_cryptocurrencies = []
    existing_cryptocurrencies = []

    # Convert data to a pandas DataFrame for easy manipulation
    crypto_df = pd.DataFrame.from_dict(data, orient="index")

    # Iterate through each row in the DataFrame
    for _, row in crypto_df.iterrows():
        coin_id = row["Id"]
        name = row["CoinName"]
        symbol = row["Symbol"]
        description = row.get("Description", "")

        try:
            crypto, created = Cryptocurrency.objects.get_or_create(
                coin_id=coin_id,
                defaults={
                    "name": name,
                    "symbol": symbol,
                    "description": description,
                },
            )

            if created:
                new_cryptocurrencies.append(name)
            else:
                existing_cryptocurrencies.append(name)

        except IntegrityError:
            existing_cryptocurrencies.append(name)

    return {
        "new_cryptos": new_cryptocurrencies,
        "existing_cryptos": existing_cryptocurrencies,
        "total_cryptos": Cryptocurrency.objects.count(),
    }
