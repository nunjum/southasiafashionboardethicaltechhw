"""Cached exchange-rate conversion with explicit fallback labeling."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import urlopen

import streamlit as st


FALLBACK_RATES = {"BDT": 123.02, "INR": 96.78, "PKR": 277.02}
RATE_API_URL = "https://open.er-api.com/v6/latest/USD"


@st.cache_data(ttl=3600)
def get_exchange_rates() -> dict[str, object]:
    """Return USD-to-local rates with a live/fallback status for each currency."""
    try:
        with urlopen(RATE_API_URL, timeout=5) as response:
            payload = json.load(response)
        rates = payload.get("rates", {})
        local_rates = {
            currency: float(rates[currency])
            for currency in FALLBACK_RATES
            if currency in rates and float(rates[currency]) > 0
        }
        if not local_rates:
            raise ValueError("No supported local currencies were returned")
        return {
            "rates": local_rates,
            "fallback_rates": {
                currency: FALLBACK_RATES[currency]
                for currency in FALLBACK_RATES
                if currency not in local_rates
            },
            "rate_date": payload.get("time_last_update_utc", "Unknown date"),
            "source": "ExchangeRate-API open endpoint",
            "live": True,
        }
    except (OSError, URLError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return {
            "rates": {},
            "fallback_rates": FALLBACK_RATES,
            "rate_date": datetime.now(timezone.utc).strftime("%Y-%m-%d UTC"),
            "source": "Fallback mock rates; live exchange-rate request unavailable",
            "live": False,
        }


def local_to_usd(amount: float, currency: str, exchange_data: dict[str, object]) -> float:
    """Convert a local-currency amount to USD using the selected rate."""
    rates = exchange_data.get("rates", {})
    fallback_rates = exchange_data.get("fallback_rates", {})
    rate = rates.get(currency) or fallback_rates.get(currency)
    if not rate:
        raise ValueError(f"No exchange rate is available for {currency}")
    return float(amount) / float(rate)