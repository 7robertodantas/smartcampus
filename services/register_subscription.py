import requests
import time

subscription = {
    "description": "Cygnus WeatherStation updates",
    "subject": {
        "entities": [{"idPattern": ".*", "type": "WeatherStation"}],
        "condition": {"attrs": ["temperature", "weathercode"]}
    },
    "notification": {
        "http": {"url": "http://cygnus:5050/notify"},
        "attrsFormat": "legacy"
    },
    "throttling": 1
}

orion_url = "http://orion:1026/v2/subscriptions"

for _ in range(30):
    try:
        r = requests.get(orion_url)
        if r.status_code == 200:
            break
    except Exception:
        pass
    time.sleep(2)
else:
    print("Orion não respondeu a tempo.")
    exit(1)

r = requests.post(orion_url, json=subscription, headers={"Content-Type": "application/json"})
if r.status_code in [200, 201]:
    print("Subscription criada com sucesso.")
else:
    print(f"Erro ao criar subscription: {r.status_code} - {r.text}")
