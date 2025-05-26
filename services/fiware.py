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


def upsert_entity(entity):
    """
    Create or update an entity in Orion. If the entity already exists, update its attributes.
    Returns the response object or None if an error occurs.
    """
    try:
        url = f"{ORION_URL}/v2/entities"
        headers = {"Content-Type": "application/json"}
        res = requests.post(url, json=entity, headers=headers)
        if res.status_code == 422 and "Already Exists" in res.text:
            # Entity exists, update its attributes
            alert_id = entity.get("id")
            if not alert_id:
                logger.error("Entity ID missing for update.")
                return None
            update_url = f"{ORION_URL}/v2/entities/{alert_id}/attrs"
            update_entity = entity.copy()
            update_entity.pop("id", None)
            update_entity.pop("type", None)
            res = requests.put(update_url, headers=headers, json=update_entity)
        return res
    except Exception as e:
        logger.error(f"Error upserting entity {entity.get('id', 'Unknown')}: {e}")
        raise


def update_entity(entity_id, attrs):
    """
    Update attributes of an existing entity in Orion using POST /v2/entities/{entity_id}/attrs.
    Args:
        entity_id (str): The ID of the entity to update.
        attrs (dict): The attributes to update in the entity.
    Logging:
        - Logs success or error for the update operation.
    """
    try:
        url = f"{ORION_URL}/v2/entities/{entity_id}/attrs"
        headers = {"Content-Type": "application/json"}
        requests.post(url, json=attrs, headers=headers)
        logger.info(f"Updated entity {entity_id} with {json.dumps(attrs)} attributes.")
    except Exception as e:
        logger.error(
            f"Error updating entiupdate_entityty {entity_id}: {e}", exc_info=True
        )
        raise


def create_entity(entity):
    """
    Create a new entity in Orion using POST /v2/entities.
    Args:
        entity (dict): The entity data to create.
    Returns:
        bool: True if created successfully, False otherwise.
    Logging:
        - Logs success or error for the creation operation.
    """
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


def delete_all_entities(type):
    """
    Deletes all entities of a specified type from the Orion Context Broker.

    This function retrieves all entities of the given type in batches (with a limit of 100 per request)
    and deletes each entity individually. It logs the number of entities found, each deletion attempt,
    and any errors encountered during the process.

    Args:
        type (str): The type of entities to delete.

    Raises:
        RequestsException: If there is an error retrieving or deleting entities from the Orion Context Broker.
        Exception: For any other unexpected errors during the process.

    Logging:
        - Logs the total number of entities found for the given type.
        - Logs each successful or failed deletion.
        - Logs errors encountered during retrieval or deletion.
    """
    try:
        headers = {"Accept": "application/json"}
        limit = 100

        while True:
            params = {
                "type": type,
                "limit": limit,
                "offset": 0,
                "options": "count",
            }
            url = f"{ORION_URL}/v2/entities"
            res = requests.get(url, params=params, headers=headers)
            res.raise_for_status()
            total = int(res.headers.get("Fiware-Total-Count", 0))
            logger.info(f"Found entities of type {type}: {total}")
            if total == 0:
                logger.info(f"No entities of type {type} to delete.")
                break

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
    """
    Waits for the Orion Context Broker to become available by polling the /version endpoint.
    Tries for up to 30 seconds, checking every second. Logs the status of each attempt.
    Returns:
        bool: True if Orion is available within the timeout, False otherwise.
    Logging:
        - Logs each attempt and the final result (success or failure).
    """
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
    """
    Registers a subscription in Orion Context Broker with retries for up to 30 seconds.
    Args:
        subscription (dict): The subscription payload to register.
    Returns:
        bool: True if the subscription was registered successfully, False otherwise.
    Logging:
        - Logs each attempt, success, or failure, including error details if any.
    """
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


def find_entities_nearby(entity_type, latitude, longitude, radius_meters=5000):
    """
    Find entities of a given type near a location using Orion's georel query.
    Returns a list of entities (dicts).
    """
    logger.info(
        f"Searching for {entity_type} near: lat={latitude}, lon={longitude}, radius={radius_meters}m"
    )
    try:
        params_geo = {
            "type": entity_type,
            "georel": f"near;maxDistance:{radius_meters}",
            "geometry": "point",
            "coords": f"{latitude},{longitude}",
        }
        response_geo = requests.get(f"{ORION_URL}/v2/entities", params=params_geo)
        response_geo.raise_for_status()
        entities = response_geo.json()
        logger.info(f"Total nearby {entity_type}: {len(entities)}")
        return entities
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to search for {entity_type} with georel: {e}")
        return []
