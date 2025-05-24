import time
import logging
import sys
import json
import os
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout, RequestException
from flask import Flask, request


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

        update_entity(entity_id, weather)

    return "", 204


def update_entity(entity_id, weather_attrs):
    try:
        url = f"{ORION_URL}/entities/{entity_id}/attrs"
        headers = {"Content-Type": "application/json"}
        requests.post(url, json=weather_attrs, headers=headers)
        logger.info(f"Updated entity {entity_id} with weather data.")
    except Exception as e:
        logger.error(f"Error updating entity {entity_id}: {e}", exc_info=True)


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

    logger.info("Registering subscription to: " + json.dumps(subscription["subject"]))

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    timeout_seconds = 30
    retry_interval = 1
    start_time = time.time()

    subscriptions_url = f"{ORION_URL}/subscriptions"

    while time.time() - start_time < timeout_seconds:
        try:
            res = requests.post(subscriptions_url, json=subscription, headers=headers)
            if res.status_code in [200, 201]:
                logger.info("Subscription registered.")
                subscription_created = True
                return
            else:
                logger.warning(f"Subscription attempt failed: {res.status_code}")
                logger.warning(res.text)
        except ConnectionError as ce:
            logger.warning(f"Could not connect to orion: {subscriptions_url}")
        except HTTPError as he:
            logger.warning(f"Response error from Orion: {he}")
        except Timeout as te:
            logger.warning(f"Orion did not respond in time: {te}")
        except RequestException as e:
            logger.warning(f"Unexpected request error {e}")
        except Exception as e:
            logger.warning(f"Unknown error: {e}")

        time.sleep(retry_interval)

    logger.error("Failed to register subscription after 30 seconds.")


with app.app_context():
    register_subscription()

if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
