import requests
import json

real_temperature = 28.9
real_weathercode = 4

payload = {
    "temperature": {"value": real_temperature, "type": "Float"},
    "weathercode": {"value": real_weathercode, "type": "Integer"}
}

url = "http://orion:1026/v2/entities/WeatherStation:CampusNatal/attrs"
headers = {"Content-Type": "application/json"}

response = requests.patch(url, headers=headers, json=payload)
print(f"[{response.status_code}] {response.text}")
