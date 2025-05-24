import requests
import json
import time
from datetime import datetime, timezone
import random

ORION_URL = "http://localhost:1026/v2"
ENTITY_ID = "WeatherStation:CampusNatal"
CALLBACK_URL = "http://weather-context-enricher:5000/notify-weather"
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

    url = f"{ORION_URL}/entities"
    res = requests.post(url, headers=HEADERS, json=entity)
    if res.status_code in [201, 204]:
        print("[OK] Entidade criada com sucesso.")
    elif res.status_code == 422:
        print("[AVISO] Entidade já existe.")
    else:
        print(f"[ERRO] Criando entidade: {res.status_code}")
        print(res.text)


def upsert_weather_station(weathercode, timestamp):
    attrs = {
        "weathercode": {"type": "Number", "value": weathercode},
        "timestamp": {"type": "DateTime", "value": timestamp},
        "location": {
            "type": "geo:json",
            "value": {"type": "Point", "coordinates": COORDS},
        },
    }

    url = f"{ORION_URL}/entities/{ENTITY_ID}/attrs"
    res = requests.post(url, headers=HEADERS, json=attrs)
    if res.status_code in [204, 201]:
        print(
            f"[{timestamp}] [OK] Atualizado: {ENTITY_ID} com weathercode {weathercode}"
        )
    else:
        print(f"[ERRO] {res.status_code} - {res.text}")


def simulate_weather_loop():
    print("[INFO] Simulando 100 atualizações de clima...")

    chuva_codes = [61, 80]
    sol_codes = [0, 1]

    for i in range(100):
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        if i % 2 == 0:
            weathercode = random.choice(chuva_codes)
        else:
            weathercode = random.choice(sol_codes)

        upsert_weather_station(weathercode, timestamp)
        time.sleep(5)


def main():
    create_entity()
    simulate_weather_loop()


if __name__ == "__main__":
    main()
