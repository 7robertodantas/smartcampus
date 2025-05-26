import time
import logging
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
        url = f"{ORION_URL}/v2/entities/{entity_id}/attrs"
        headers = {"Content-Type": "application/json"}
        requests.post(url, json=weather_attrs, headers=headers)
        logger.info(f"Updated entity {entity_id} with weather data.")
    except Exception as e:
        logger.error(f"Error updating entity {entity_id}: {e}", exc_info=True)


def create_entity(entity):
    try:
        url = f"{ORION_URL}/v2/entities"
        headers = {"Content-Type": "application/json"}
        res = requests.post(url, json=entity, headers=headers)
        if res.status_code in [201, 204]:
            logger.info(f"Created entity {entity.get('id')}")
            return True
        else:
            logger.warning(
                f"Failed to create entity {entity.get('id')}: {res.status_code} {res.text}"
            )
            return False
    except Exception as e:
        logger.error(f"Error creating entity {entity.get('id')}: {e}", exc_info=True)
        return False


def delete_all_entities():
    try:
        url = f"{ORION_URL}/v2/entities"
        headers = {"Accept": "application/json"}
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        entities = res.json()
        for entity in entities:
            entity_id = entity.get("id")
            if entity_id:
                del_url = f"{ORION_URL}/v2/entities/{entity_id}"
                try:
                    del_res = requests.delete(del_url, headers=headers)
                    if del_res.status_code in [204, 404]:
                        logger.info(f"Deleted entity {entity_id}")
                    else:
                        logger.warning(
                            f"Failed to delete entity {entity_id}: {del_res.status_code}"
                        )
                except Exception as e:
                    logger.error(
                        f"Error deleting entity {entity_id}: {e}", exc_info=True
                    )
    except Exception as e:
        logger.error(f"Error retrieving entities: {e}", exc_info=True)


def wait_for_orion():
    url = f"{ORION_URL}/version"
    timeout_seconds = 30
    retry_interval = 1
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                logger.info("Orion is available.")
                return True
            else:
                logger.warning(
                    f"Orion /version responded with status {res.status_code}"
                )
        except (ConnectionError, Timeout) as e:
            logger.warning(f"Waiting for Orion: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error while waiting for Orion: {e}")
        time.sleep(retry_interval)

    logger.error("Orion did not become available within 30 seconds.")
    return False


def register_subscription(subscription):
    logger.info("Registering subscription to: " + json.dumps(subscription["subject"]))

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    timeout_seconds = 30
    retry_interval = 1
    start_time = time.time()

    subscriptions_url = f"{ORION_URL}/v2/subscriptions"

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
