from __future__ import annotations

from datetime import datetime, time
from unittest.mock import patch

import pytest

from utils.weather import LocationNotFoundError, WeatherServiceError
from utils.weather_broadcast import (
    _seconds_until,
    build_weather_digest,
    format_weather_info,
)


def test_format_weather_info_uses_expected_template():
    payload = {
        "name": "Dushanbe",
        "weather": [{"description": "clear sky"}],
        "main": {"temp": 17, "feels_like": 15, "humidity": 40},
        "wind": {"speed": 2.5},
    }

    message = format_weather_info(payload)

    assert message == (
        "🌤️ Weather in <b>Dushanbe</b>:\n"
        "Condition: <b>Clear sky</b>\n"
        "Temperature: <b>17°C</b> (feels like 15°C)\n"
        "Humidity: <b>40%</b>\n"
        "Wind speed: <b>2.5 m/s</b>"
    )


@patch("utils.weather_broadcast.fetch_weather_by_city")
def test_build_weather_digest_combines_results(mock_fetch):
    mock_fetch.side_effect = [
        {
            "name": "Dushanbe",
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 17, "feels_like": 15, "humidity": 40},
            "wind": {"speed": 2.5},
        },
        LocationNotFoundError(),
        WeatherServiceError("boom"),
    ]

    digest = build_weather_digest(["Dushanbe", " ", "Nowhere", "ErrorTown"])
    parts = digest.split("\n\n")

    assert "🌤️ Weather in <b>Dushanbe</b>" in parts[0]
    assert "Could not find coordinates for Nowhere" in parts[1]
    assert "Failed to load weather for ErrorTown" in parts[2]


@pytest.mark.parametrize(
    ("current", "target", "expected"),
    [
        (datetime(2024, 1, 1, 7, 0, 0), time(8, 0), 3600),
        (datetime(2024, 1, 1, 9, 0, 0), time(8, 0), 23 * 3600),
    ],
)
def test_seconds_until_handles_wraparound(current: datetime, target: time, expected: int):
    assert _seconds_until(target, now=current) == expected
