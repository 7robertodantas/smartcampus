from pymongo import MongoClient
from influxdb import InfluxDBClient
from datetime import datetime

mongo_client = MongoClient("mongodb://mongo:27017")
mongo_db = mongo_client["orion"]
collection = mongo_db["entities"]

influx_client = InfluxDBClient(host="influxdb", port=8086)
influx_client.switch_database("smartcampus")

def convert_to_influx(doc):
    timestamp = doc.get("timestamp") or datetime.utcnow().isoformat()

    measurement = "WeatherStation"

    fields = {
        key: value for key, value in doc.items()
        if isinstance(value, (int, float)) and key not in ["_id"]
    }

    if not fields:
        return None

    point = {
        "measurement": measurement,
        "tags": {
            "entity_id": doc.get("id", "unknown")
        },
        "time": timestamp,
        "fields": fields
    }

    return point

docs = collection.find()
count = 0

for doc in docs:
    point = convert_to_influx(doc)
    if point:
        influx_client.write_points([point])
        count += 1

print(f"{count} documentos migrados do Mongo para o Influx (measurement = 'WeatherStation').")
