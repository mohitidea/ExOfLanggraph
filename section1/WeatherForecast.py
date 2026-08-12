from typing import TypedDict, Optional, Dict, Any
from datetime import datetime
from langgraph.graph import StateGraph, END, START
from operator import add
import os

# import requests if available; allow running even when requests isn't installed
try:
	import requests
except Exception:  # ImportError or other import-time issues
	requests = None

# Load environment variables from .env (if present)
try:
	from dotenv import load_dotenv
	load_dotenv()
except Exception:
	# If python-dotenv isn't installed, we continue; env vars may be set externally
	pass


class WeatherState(TypedDict):
    """Represents the state of our graph."""
    # Map city -> detailed weather info object
    cityInfos: Dict[str, Dict[str, Any]]
    # Error message when API call fails
    error: Optional[str]


def _parse_cities(s: Optional[str]) -> list:
	"""Parse `OPENWEATHER_CITY` env value into a list of city names.

	Accepts comma-separated values or a Python-style bracket list like
	`["DELHI","MUMBAI"]` and returns a list of stripped names.
	"""
	if not s:
		return ["London"]
	s = s.strip()
	if s.startswith("[") and s.endswith("]"):
		s = s[1:-1]
	parts = [p.strip().strip('"').strip("'") for p in s.split(",") if p.strip()]
	return parts or ["London"]

def forecast_weather(state: WeatherState) -> WeatherState:
	"""Fetch per-city detailed weather info from OpenWeatherMap and return structured state.

	Returned state keys:
	- `cityInfos`: Dict[city, info-object]
	- `error`: None if all OK or combined error message
	"""
	api_key = os.getenv("OPENWEATHER_API_KEY")
	raw = os.getenv("OPENWEATHER_CITY")
	cities = _parse_cities(raw)

	infos: Dict[str, Dict[str, Any]] = {}
	errors: list[str] = []

	if not api_key:
		return {"cityInfos": {}, "error": "Missing OPENWEATHER_API_KEY"}
	if requests is None:
		return {"cityInfos": {}, "error": "Missing 'requests' library"}

	for city in cities:
		city = city.strip()
		if not city:
			continue
		r = None
		try:
			r = requests.get(
				"https://api.openweathermap.org/data/2.5/weather",
				params={"q": city, "appid": api_key, "units": "metric"},
				timeout=10,
			)
			r.raise_for_status()
			data = r.json()

			main = data.get("main") or {}
			weather = (data.get("weather") or [{}])[0] or {}
			wind = data.get("wind") or {}
			clouds = data.get("clouds") or {}
			sys = data.get("sys") or {}

			def _f(x):
				try:
					return float(x) if x is not None else None
				except Exception:
					return None

			info: Dict[str, Any] = {
				"temp": _f(main.get("temp")),
				"feels_like": _f(main.get("feels_like")),
				"temp_min": _f(main.get("temp_min")),
				"temp_max": _f(main.get("temp_max")),
				"pressure": main.get("pressure"),
				"humidity": main.get("humidity"),
				"weather_main": weather.get("main"),
				"weather_description": weather.get("description"),
				"wind_speed": _f(wind.get("speed")),
				"wind_deg": wind.get("deg"),
				"clouds": clouds.get("all"),
				"sunrise": sys.get("sunrise"),
				"sunset": sys.get("sunset"),
				"timestamp": data.get("dt"),
				"raw": data,
			}

			infos[city] = info
		except requests.exceptions.HTTPError:
			status = r.status_code if r is not None else "unknown"
			body = r.text if r is not None else ""
			errors.append(f"{city}: HTTP {status} {body}")
		except Exception as e:
			errors.append(f"{city}: {e}")

	err_msg = None if not errors else "; ".join(errors)
	return {"cityInfos": infos, "error": err_msg}

# Initialize the StateGraph
workflow = StateGraph(WeatherState)
# Add nodes
workflow.add_node("forecast", forecast_weather)
# Set the entry point (the first node to run)
workflow.set_entry_point("forecast")
# Connect the end nodes to the final graph stop
workflow.add_edge("forecast", END)
# Compile the graph
app = workflow.compile()
workflow.compile()

result_1 = app.invoke({})

def _fmt(val, precision=2):
	if val is None:
		return "N/A"
	try:
		if isinstance(val, float):
			return f"{val:.{precision}f}"
		return str(val)
	except Exception:
		return str(val)

def _ts(ts):
	try:
		return datetime.fromtimestamp(int(ts)).isoformat(sep=' ', timespec='seconds')
	except Exception:
		return "N/A"

def pretty_print_city_infos(infos: Dict[str, Dict[str, Any]]):
	if not infos:
		print("No city weather info available.")
		return
	sep = "=" * 72
	for city, info in infos.items():
		print(sep)
		print(f" City: {city}")
		print(sep)
		print(f"  Temperature: { _fmt(info.get('temp')) } °C")
		print(f"  Feels like:  { _fmt(info.get('feels_like')) } °C")
		print(f"  Min/Max:     { _fmt(info.get('temp_min')) } / { _fmt(info.get('temp_max')) } °C")
		print(f"  Pressure:    { _fmt(info.get('pressure')) } hPa")
		print(f"  Humidity:    { _fmt(info.get('humidity')) } %")
		print(f"  Weather:     { _fmt(info.get('weather_main'))} - { _fmt(info.get('weather_description')) }")
		print(f"  Wind:        { _fmt(info.get('wind_speed')) } m/s, deg { _fmt(info.get('wind_deg')) }")
		print(f"  Clouds:      { _fmt(info.get('clouds')) } %")
		print(f"  Sunrise:     { _ts(info.get('sunrise')) }")
		print(f"  Sunset:      { _ts(info.get('sunset')) }")
		print(f"  Timestamp:   { _ts(info.get('timestamp')) }")
		print()
	print(sep)

if result_1.get("error"):
	print(f"Error: {result_1['error']}")
else:
	city_infos = result_1.get("cityInfos", {})
	pretty_print_city_infos(city_infos)
# Output shows per-city detailed weather info or an error message.




