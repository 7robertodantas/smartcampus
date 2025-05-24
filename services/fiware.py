import time
import logging
import sys
import json
import os
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout, RequestException

logger = logging.getLogger("fiware")

ORION_URL = os.environ.get("ORION_URL")
if not ORION_URL:
    raise ValueError("ORION_URL environment variable is not set.")


def update_entity(entity_id, weather_attrs):
    try:
        url = f"{ORION_URL}/entities/{entity_id}/attrs"
        headers = {"Content-Type": "application/json"}
        requests.post(url, json=weather_attrs, headers=headers)
        logger.info(f"Updated entity {entity_id} with weather data.")
    except Exception as e:
        logger.error(f"Error updating entity {entity_id}: {e}", exc_info=True)


def register_subscription(subscription):
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
                return True
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
    return False
