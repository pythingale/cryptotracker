import asyncio
import datetime
import logging
from decimal import ROUND_HALF_UP
from decimal import Decimal
from decimal import InvalidOperation

import aiohttp
import numpy as np
import pandas as pd
from asgiref.sync import sync_to_async
from celery import shared_task

from cryptocurrencies.models import Cryptocurrency
from cryptocurrencies.models import HistoricalPrice

API_KEY = "434606a7969df44cfeec988681132381bdbe46352e675acffb2bd11bd7c06a20"
HTTP_STATUS_OK = 200

logger = logging.getLogger(__name__)


def round_value(value, precision=20, scale=10):
    """Rounds a value to fit within the required precision and scale, or returns 0 if invalid."""
    if value is not None:
        try:
            return Decimal(value).quantize(
                Decimal(f'1.{"0" * scale}'),
                rounding=ROUND_HALF_UP,
            )
        except (InvalidOperation, ValueError, TypeError):
            return Decimal(0)
    return Decimal(0)


async def fetch_crypto_data(
    crypto,
    session,
    semaphore,
    updated_symbols,
    no_endpoint_symbols,
):
    """
    Fetches historical data for a single cryptocurrency asynchronously.
    Updates the appropriate lists based on whether data was updated or no historical data endpoint was found.
    """
    url_template = "https://min-api.cryptocompare.com/data/v2/histoday?fsym={symbol}&tsym=USD&limit=1&api_key={api_key}"
    url = url_template.format(symbol=crypto.symbol, api_key=API_KEY)

    async with semaphore:
        try:
            async with session.get(url, timeout=120) as response:
                if response.status == HTTP_STATUS_OK:
                    data = await response.json()

                    if data["Response"] == "Success":
                        records = []
                        for day_data in data["Data"]["Data"]:
                            date = datetime.datetime.fromtimestamp(
                                day_data["time"],
                                tz=datetime.UTC,
                            ).date()
                            exists = await sync_to_async(
                                HistoricalPrice.objects.filter(
                                    cryptocurrency=crypto,
                                    date=date,
                                ).exists,
                            )()

                            if not exists:
                                records.append(
                                    {
                                        "cryptocurrency": crypto,
                                        "date": date,
                                        "open_price": round_value(
                                            day_data.get("open"),
                                            precision=20,
                                            scale=4,
                                        ),
                                        "high_price": round_value(
                                            day_data.get("high"),
                                            precision=20,
                                            scale=4,
                                        ),
                                        "low_price": round_value(
                                            day_data.get("low"),
                                            precision=20,
                                            scale=4,
                                        ),
                                        "close_price": round_value(
                                            day_data.get("close"),
                                            precision=20,
                                            scale=4,
                                        ),
                                        "volume_from": round_value(
                                            day_data.get("volumefrom"),
                                            precision=30,
                                            scale=10,
                                        ),
                                        "volume_to": round_value(
                                            day_data.get("volumeto"),
                                            precision=30,
                                            scale=10,
                                        ),
                                    },
                                )

                        if records:
                            historical_prices = pd.DataFrame(records)
                            await sync_to_async(HistoricalPrice.objects.bulk_create)(
                                [
                                    HistoricalPrice(
                                        cryptocurrency=row["cryptocurrency"],
                                        date=row["date"],
                                        open_price=row["open_price"],
                                        high_price=row["high_price"],
                                        low_price=row["low_price"],
                                        close_price=row["close_price"],
                                        volume_from=row["volume_from"],
                                        volume_to=row["volume_to"],
                                    )
                                    for _, row in historical_prices.iterrows()
                                ],
                            )
                            updated_symbols.append(crypto.symbol)
                        else:
                            no_endpoint_symbols.append(crypto.symbol)
                    else:
                        no_endpoint_symbols.append(crypto.symbol)
                else:
                    no_endpoint_symbols.append(crypto.symbol)

        except aiohttp.ClientError:
            no_endpoint_symbols.append(crypto.symbol)


@shared_task(soft_time_limit=14400)
def fetch_historical_prices():
    """Celery task to fetch historical prices for all cryptocurrencies."""
    asyncio.run(fetch_all_cryptos())


async def fetch_all_cryptos(batch_size=50, max_concurrency=10):
    """Fetches historical prices for all cryptocurrencies in batches with controlled concurrency."""
    cryptos = await sync_to_async(list)(Cryptocurrency.objects.all())
    batches = np.array_split(cryptos, len(cryptos) // batch_size)
    total_steps = len(batches)

    updated_symbols = []
    no_endpoint_symbols = []

    semaphore = asyncio.Semaphore(max_concurrency)
    async with aiohttp.ClientSession() as session:
        for step, batch in enumerate(batches, start=1):
            tasks = [
                fetch_crypto_data(
                    crypto,
                    session,
                    semaphore,
                    updated_symbols,
                    no_endpoint_symbols,
                )
                for crypto in batch
            ]
            logger.info(f"Processing batch {step}/{total_steps}")
            await asyncio.gather(*tasks)

    logger.info("\n--- Process Completed ---")
    logger.info(
        f"Updated symbols: {', '.join(updated_symbols) if updated_symbols else 'None'}",
    )
    logger.info(
        f"No historical data endpoint: {', '.join(no_endpoint_symbols) if no_endpoint_symbols else 'None'}",
    )

    return "Historical prices fetched successfully."
