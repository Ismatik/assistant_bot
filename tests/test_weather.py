from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import types as pytypes
from unittest.mock import Mock, patch

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

for module_name in ("utils.weather", "utils.utils", "utils", "requests"):
    sys.modules.pop(module_name, None)

requests_stub = pytypes.ModuleType("requests")
requests_stub.get = lambda *args, **kwargs: None
sys.modules["requests"] = requests_stub


def _build_response(payload):
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status = Mock()
    return response


@patch("utils.weather.requests.get")
def test_geocode_city_builds_query(mock_get):
    from utils.weather import Coordinates, geocode_city

    mock_get.return_value = _build_response([{"lat": 1.23, "lon": 3.21}])

    coords = geocode_city("London", state="England", country="GB", api_key="dummy")

    assert coords == Coordinates(lat=1.23, lon=3.21)
    mock_get.assert_called_once_with(
        "https://api.openweathermap.org/geo/1.0/direct",
        params={"q": "London,England,GB", "limit": 1, "appid": "dummy"},
        timeout=10,
    )


@patch("utils.weather.requests.get")
def test_geocode_city_raises_when_no_results(mock_get):
    from utils.weather import LocationNotFoundError, geocode_city

    mock_get.return_value = _build_response([])

    with pytest.raises(LocationNotFoundError):
        geocode_city("Unknown", api_key="dummy")


@patch("utils.weather.requests.get")
def test_fetch_weather_by_coordinates_returns_json(mock_get):
    from utils.weather import Coordinates, fetch_weather_by_coordinates

    mock_get.return_value = _build_response({"key": "value"})

    payload = fetch_weather_by_coordinates(Coordinates(1.0, 2.0), units="imperial", api_key="dummy")

    assert payload == {"key": "value"}
    mock_get.assert_called_once_with(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"lat": 1.0, "lon": 2.0, "units": "imperial", "appid": "dummy"},
        timeout=10,
    )


@patch("utils.weather.requests.get")
def test_fetch_weather_by_city_chains_calls(mock_get):
    from utils.weather import fetch_weather_by_city

    mock_get.side_effect = [
        _build_response([{"lat": 51.5, "lon": -0.12}]),
        _build_response({"weather": []}),
    ]

    payload = fetch_weather_by_city("London", api_key="dummy")

    assert payload == {"weather": []}
    assert mock_get.call_count == 2


def test_summarise_weather_formats_text():
    from utils.weather import summarise_weather

    payload = {
        "name": "Dushanbe",
        "main": {"temp": 17},
        "weather": [SimpleNamespace(description="clear sky").__dict__],
    }

    summary = summarise_weather(payload)
    assert summary == "Current weather in Dushanbe: 17°C, Clear sky."
