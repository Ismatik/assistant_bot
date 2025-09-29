"""Helpers for working with the OpenWeather REST APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from config_reader import config


BASE_URL = "https://api.openweathermap.org"
GEOCODING_ENDPOINT = f"{BASE_URL}/geo/1.0/direct"
WEATHER_ENDPOINT = f"{BASE_URL}/data/2.5/weather"

DEFAULT_TIMEOUT = 10


class WeatherServiceError(RuntimeError):
    """Base error raised for any issues when fetching weather data."""


class LocationNotFoundError(WeatherServiceError):
    """Raised when the geocoding API cannot find a requested location."""


class WeatherApiKeyError(WeatherServiceError):
    """Raised when no API key is available for the OpenWeather requests."""


@dataclass(slots=True)
class Coordinates:
    """Simple structure describing a geographic coordinate pair."""

    lat: float
    lon: float


def _get_api_key(explicit_api_key: str | None = None) -> str:
    """Return the OpenWeather API key or raise if none is configured."""

    if explicit_api_key:
        return explicit_api_key

    secret = getattr(config, "weather_api_key", None)
    if secret is None:
        raise WeatherApiKeyError(
            "Weather API key is not configured. Set WEATHER_API_KEY in the environment or pass api_key explicitly."
        )

    try:
        return secret.get_secret_value()
    except AttributeError as exc:  # pragma: no cover - defensive: SecretStr missing method.
        raise WeatherApiKeyError("Invalid weather API key configuration.") from exc


def geocode_city(
    city: str,
    *,
    state: str | None = None,
    country: str | None = None,
    limit: int = 1,
    api_key: str | None = None,
) -> Coordinates:
    """Return coordinates for the provided city using the direct geocoding endpoint."""

    if not city or not city.strip():
        raise ValueError("City name must be a non-empty string.")

    query_parts = [city.strip()]
    if state:
        query_parts.append(state.strip())
    if country:
        query_parts.append(country.strip())

    params = {
        "q": ",".join(query_parts),
        "limit": limit,
        "appid": _get_api_key(api_key),
    }

    response = requests.get(GEOCODING_ENDPOINT, params=params, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    payload = response.json()

    if not payload:
        raise LocationNotFoundError(f"No matching locations found for '{params['q']}'.")

    location = payload[0]
    try:
        return Coordinates(lat=float(location["lat"]), lon=float(location["lon"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise WeatherServiceError("Malformed response from geocoding endpoint.") from exc


def fetch_weather_by_coordinates(
    coordinates: Coordinates,
    *,
    units: str = "metric",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Fetch weather information for the given coordinates."""

    params = {
        "lat": coordinates.lat,
        "lon": coordinates.lon,
        "units": units,
        "appid": _get_api_key(api_key),
    }

    response = requests.get(WEATHER_ENDPOINT, params=params, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise WeatherServiceError("Unexpected weather payload received.")
    return data


def fetch_weather_by_city(
    city: str,
    *,
    state: str | None = None,
    country: str | None = None,
    units: str = "metric",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Convenience wrapper that combines geocoding and weather lookups."""

    coordinates = geocode_city(city, state=state, country=country, api_key=api_key)
    return fetch_weather_by_coordinates(coordinates, units=units, api_key=api_key)


def summarise_weather(data: dict[str, Any]) -> str:
    """Return a human readable summary string from a weather payload."""

    try:
        city = data["name"]
        temperature = data["main"]["temp"]
        description = data["weather"][0]["description"]
    except (KeyError, IndexError, TypeError) as exc:
        raise WeatherServiceError("Weather payload is missing required fields.") from exc

    return f"Current weather in {city}: {temperature}°C, {description.capitalize()}."




# import requests
# from config_reader import config

# OPENWEATHER_API_KEY = config.weather_api_key.get_secret_value()
# BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# def get_weather_data(city_name):
#     params = {
#         "q": city_name,
#         "appid": OPENWEATHER_API_KEY,
#         "units": "metric"
#     }
#     response = requests.get(BASE_URL, params=params)
#     response.raise_for_status()
#     return response.json()

# def format_weather_info(data):
#     city = data.get("name")
#     weather = data["weather"][0]["description"].capitalize()
#     temp = data["main"]["temp"]
#     feels_like = data["main"]["feels_like"]
#     humidity = data["main"]["humidity"]
#     wind_speed = data["wind"]["speed"]

#     return (
#         f"🌤️ Weather in <b>{city}</b>:\n"
#         f"Condition: <b>{weather}</b>\n"
#         f"Temperature: <b>{temp}°C</b> (feels like {feels_like}°C)\n"
#         f"Humidity: <b>{humidity}%</b>\n"
#         f"Wind speed: <b>{wind_speed} m/s</b>"
#     )

# if __name__ == "__main__":
#     city = "Душанбе"
#     data = get_weather_data(city)
#     message = format_weather_info(data)
#     print(message)