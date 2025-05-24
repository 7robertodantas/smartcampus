import time
import logging
import sys
import json
import os
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout, RequestException
from flask import Flask, request
import fiware

app = Flask(__name__)

ENTITY_ID = "CourseInstance"
ORION_URL = os.environ.get("ORION_URL")
CALLBACK_URL = os.environ.get("CALLBACK_URL")
subscription_created = False

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False


@app.route("/notify", methods=["POST"])
def notify():
    payload = request.json
    data = payload.get("data", [])

    for entity in data:
        entity_id = entity.get("id")
        location = entity.get("location", {}).get("value", {})
        lon, lat = location.get("coordinates", [None, None])

        if lat is None or lon is None:
            logger.warning(f"Missing coordinates in entity: {entity_id}")
            continue

        weather = get_weather_info(lat, lon)
        logger.info(f"Weather data: {entity_id} {json.dumps(weather)}")
        if not weather:
            logger.warning(f"No weather data returned for entity: {entity_id}")
            continue

        fiware.update_entity(entity_id, weather)

    return "", 204


def get_weather_info(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        res = requests.get(url)
        if res.status_code != 200:
            logger.warning(f"Failed weather API call. Status: {res.status_code}")
            return None

        data = res.json()
        current = data.get("current_weather", {})
        units = data.get("current_weather_units", {})

        return {
            "currentWeather": {
                "type": "StructuredValue",
                "value": {
                    "time": current.get("time"),
                    "temperature": current.get("temperature"),
                    "windspeed": current.get("windspeed"),
                    "winddirection": current.get("winddirection"),
                    "interval": current.get("interval"),
                    "is_day": current.get("is_day"),
                    "weathercode": current.get("weathercode"),
                },
                "metadata": {
                    "temperature_unit": {
                        "type": "Text",
                        "value": units.get("temperature", "°C"),
                    },
                    "windspeed_unit": {
                        "type": "Text",
                        "value": units.get("windspeed", "km/h"),
                    },
                    "winddirection_unit": {
                        "type": "Text",
                        "value": units.get("winddirection", "°"),
                    },
                    "interval_unit": {
                        "type": "Text",
                        "value": units.get("interval", "seconds"),
                    },
                    "weathercode_unit": {
                        "type": "Text",
                        "value": units.get("weathercode", "wmo code"),
                    },
                    "time_format": {
                        "type": "Text",
                        "value": units.get("time", "iso8601"),
                    },
                },
            }
        }

    except Exception as e:
        logger.error(f"Weather fetch error: {e}")
        return None


def register_subscription():
    global subscription_created
    if subscription_created:
        return

    subscription = {
        "description": "Enrich CourseInstance with weather info based on location",
        "subject": {
            "entities": [{"type": ENTITY_ID, "idPattern": "^CourseInstance.*"}],
            "condition": {"attrs": ["location"]},
        },
        "notification": {"http": {"url": CALLBACK_URL}, "attrs": ["location"]},
        "throttling": 30,
    }

    subscription_created = fiware.register_subscription(subscription)


with app.app_context():
    register_subscription()

if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
