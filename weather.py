"""Deterministic weather stub.

Plug a real provider (e.g. OpenWeatherMap, wttr.in) in here: replace
``weather_for`` with an async call to the provider and map its response onto
``WeatherOut``. The rest of the API does not need to change.
"""
from __future__ import annotations

import math
from datetime import date

from models import WeatherOut

_CONDITIONS = [
    (28.0, "Sunny"),
    (22.0, "Partly cloudy"),
    (17.0, "Cloudy"),
    (12.0, "Light rain"),
]


def weather_for(day: date) -> WeatherOut:
    """Plausible weather for a day, varying deterministically by day-of-year."""
    doy = day.timetuple().tm_yday
    # Seasonal wave peaking in mid-July, plus a small per-day wobble.
    temp = 18.0 + 8.0 * math.sin(2 * math.pi * (doy - 105) / 365.0) + (doy % 5) - 2.0
    condition = next(label for threshold, label in _CONDITIONS if temp >= threshold)
    return WeatherOut(
        temperature_c=round(temp, 1),
        condition=condition,
        high_c=round(temp + 3.5, 1),
        low_c=round(temp - 4.5, 1),
    )
