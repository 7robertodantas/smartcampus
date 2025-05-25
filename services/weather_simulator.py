import requests
import time
import logging
import os
from datetime import datetime, timezone
import random
import fiware

# Configuração de logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False

ORION_URL = os.environ.get("ORION_URL")
ENTITY_ID = "WeatherStation:CampusNatal"
COORDS = [-35.2035, -5.8365]

HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}


def create_entity():
    entity = {
        "id": ENTITY_ID,
        "type": "WeatherStation",
        "weathercode": {"type": "Number", "value": 0},
        "timestamp": {
            "type": "DateTime",
            "value": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "location": {
            "type": "geo:json",
            "value": {"type": "Point", "coordinates": COORDS},
        },
    }

    fiware.create_entity(entity)


def upsert_weather_station(weathercode, timestamp):
    attrs = {
        "weathercode": {"type": "Number", "value": weathercode},
        "timestamp": {"type": "DateTime", "value": timestamp},
        "location": {
            "type": "geo:json",
            "value": {"type": "Point", "coordinates": COORDS},
        },
    }

    url = f"{ORION_URL}/v2/entities/{ENTITY_ID}/attrs"
    try:
        res = requests.post(url, headers=HEADERS, json=attrs)
        if res.status_code in [204, 201]:
            logger.info(
                f"[{timestamp}] Atualizado: {ENTITY_ID} com weathercode {weathercode}"
            )
        else:
            logger.error(f"{res.status_code} - {res.text}")
    except Exception as e:
        logger.exception(f"Erro ao atualizar entidade: {e}")


def simulate_weather_loop():
    logger.info("Simulando atualizações de clima...")

    chuva_codes = [61, 80]
    sol_codes = [0, 1]

    i = 1
    while True:
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        if i % 2 == 0:
            weathercode = random.choice(chuva_codes)
        else:
            weathercode = random.choice(sol_codes)

        upsert_weather_station(weathercode, timestamp)
        time.sleep(random.randint(5, 10))
        i += 1


def main():
    fiware.wait_for_orion()
    create_entity()
    simulate_weather_loop()


if __name__ == "__main__":
    main()
