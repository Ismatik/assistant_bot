"""Utilities for building and scheduling daily weather broadcasts."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Iterable, Sequence

from aiogram import Bot

from utils.weather import (
    LocationNotFoundError,
    WeatherServiceError,
    fetch_weather_by_city,
)

LOGGER = logging.getLogger(__name__)


def _weather_emoji(description: str, temp: float) -> str:
    desc = description.lower()
    if "snow" in desc:
        return "❄️"
    if "rain" in desc or "drizzle" in desc:
        return "🌧️"
    if "thunder" in desc:
        return "⛈️"
    if "clear" in desc:
        return "☀️" if temp > 0 else "🌤️"
    if "cloud" in desc:
        return "☁️" if temp < 10 else "🌥️"
    if "fog" in desc or "mist" in desc or "haze" in desc:
        return "🌫️"
    if temp <= 0:
        return "🥶"
    if temp >= 30:
        return "🔥"
    return "🌡️"

def format_weather_info(data: dict, requested_city: str | None = None) -> str:
    """Return a formatted HTML weather summary using the user's template."""

    city = data.get("name")
    country = data.get("sys", {}).get("country", "")
    weather = data["weather"][0]["description"].capitalize()
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]

    emoji = _weather_emoji(weather, temp)

    city_line = f"<b>{city}</b>"
    if country:
        city_line += f" ({country})"
    if requested_city and city and requested_city.lower() != city.lower():
        city_line += f"\n<i>Note: Closest match for '{requested_city}'</i>"

    return (
        f"{emoji} Weather in {city_line}:\n"
        f"Condition: <b>{weather}</b>\n"
        f"Temperature: <b>{temp}°C</b> (feels like {feels_like}°C)\n"
        f"Humidity: <b>{humidity}%</b>\n"
        f"Wind speed: <b>{wind_speed} m/s</b>"
    )


def build_weather_digest(
    cities: Sequence[str],
    *,
    units: str = "metric",
    api_key: str | None = None,
) -> str:
    """Collect weather data for *cities* and assemble a multi-city report."""

    sections: list[str] = []

    for raw_city in cities:
        city = raw_city.strip()
        if not city:
            continue

        try:
            payload = fetch_weather_by_city(city, units=units, api_key=api_key)
        except LocationNotFoundError:
            sections.append(f"⚠️ Could not find coordinates for {city}.")
        except WeatherServiceError as exc:
            sections.append(f"⚠️ Failed to load weather for {city}: {exc}")
        else:
            try:
                sections.append(format_weather_info(payload, requested_city=city))
            except (KeyError, IndexError, TypeError) as exc:
                LOGGER.exception("Malformed weather payload for %s", city)
                sections.append(f"⚠️ Received unexpected data for {city}: {exc}")

    return "\n\n".join(sections)

def _seconds_until(send_at: time, *, now: datetime | None = None) -> float:
    """Return the number of seconds until the next *send_at* occurrence."""

    reference = now or datetime.now()
    target = datetime.combine(reference.date(), send_at)
    if target <= reference:
        target += timedelta(days=1)
    return (target - reference).total_seconds()


async def broadcast_daily_weather(
    bot: Bot,
    chat_ids: Iterable[int],
    cities: Sequence[str],
    *,
    send_at: time,
    units: str = "metric",
    api_key: str | None = None,
) -> None:
    """Send a morning weather digest to every chat in *chat_ids* each day."""

    chat_id_list = [chat_id for chat_id in chat_ids if chat_id is not None]
    if not chat_id_list:
        LOGGER.info("Weather broadcast task started without chat IDs; exiting.")
        return

    LOGGER.info(
        "Starting daily weather broadcast at %s for %d chat(s).",
        send_at.strftime("%H:%M"),
        len(chat_id_list),
    )

    try:
        while True:
            delay = max(0.0, _seconds_until(send_at))
            LOGGER.debug("Next weather broadcast in %.2f seconds", delay)
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                LOGGER.info("Weather broadcast task cancelled before sending message.")
                raise

            try:
                report = await asyncio.to_thread(
                    build_weather_digest, cities, units=units, api_key=api_key
                )
            except WeatherServiceError as exc:
                LOGGER.exception("Unable to assemble weather digest: %s", exc)
                continue

            if not report.strip():
                LOGGER.info("Weather digest was empty; skipping broadcast.")
                continue

            for chat_id in chat_id_list:
                try:
                    await bot.send_message(chat_id, report, parse_mode="HTML")
                except Exception:  # pragma: no cover - aiogram raises runtime-specific errors.
                    LOGGER.exception("Failed to send weather broadcast to chat %s", chat_id)
    except asyncio.CancelledError:
        LOGGER.info("Weather broadcast loop stopped.")
        raise
