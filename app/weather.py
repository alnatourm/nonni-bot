import re

import httpx


WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Light rain showers",
    81: "Rain showers",
    82: "Heavy rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


def is_weather_question(text: str) -> bool:
    value = text.lower()
    return any(word in value for word in ("weather", "forecast", "temperature", "طقس", "الطقس", "الحرارة"))


def extract_weather_location(text: str) -> str:
    patterns = (
        r"\b(?:in|for)\s+([\w\s,.'-]+?)(?:\?|\s+(?:today|tomorrow|now)\b|$)",
        r"(?:في|لـ)\s+([\w\s،.-]+?)(?:[؟?]|\s+(?:اليوم|غد[ًاا]?|الآن)\b|$)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" ,،.")
    return ""


async def get_weather(location: str) -> str:
    timeout = httpx.Timeout(15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        geo_response = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1, "language": "en", "format": "json"},
        )
        geo_response.raise_for_status()
        results = geo_response.json().get("results") or []
        if not results:
            return f"I could not find the location: {location}. Try adding the country name."

        place = results[0]
        forecast_response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max",
                "timezone": "auto",
                "forecast_days": 3,
            },
        )
        forecast_response.raise_for_status()
        daily = forecast_response.json()["daily"]

    place_name = ", ".join(filter(None, (place.get("name"), place.get("country"))))
    labels = ("Today", "Tomorrow", "Day after tomorrow")
    lines = [f"🌤 Weather for {place_name}"]
    for index, date in enumerate(daily["time"]):
        code = daily["weather_code"][index]
        description = WEATHER_CODES.get(code, f"Weather code {code}")
        lines.append(
            f"\n{labels[index]} — {date}\n"
            f"{description}\n"
            f"🌡 {daily['temperature_2m_min'][index]}–{daily['temperature_2m_max'][index]} °C\n"
            f"🌧 Rain chance: {daily['precipitation_probability_max'][index]}%\n"
            f"💨 Max wind: {daily['wind_speed_10m_max'][index]} km/h"
        )
    lines.append("\nSource: Open-Meteo")
    return "\n".join(lines)
