from pymongo import MongoClient
from influxdb import InfluxDBClient
from datetime import datetime
import time

mongo_client = MongoClient("mongodb://mongo:27017")
mongo_db = mongo_client["orion"]
collection = mongo_db["entities"]

influx_client = InfluxDBClient(host="influxdb", port=8086)
influx_client.switch_database("smartcampus")

def convert_to_influx(doc):
    _id = doc.get("_id", {})
    entity_id = _id.get("id", "unknown")
    measurement = _id.get("type", "UnknownType")
    attrs = doc.get("attrs", {})

    timestamp = None
    if "timestamp" in attrs and "value" in attrs["timestamp"]:
        try:
            ts_val = attrs["timestamp"]["value"]
            timestamp = datetime.utcfromtimestamp(ts_val).isoformat()
        except:
            timestamp = datetime.utcnow().isoformat()
    else:
        timestamp = datetime.utcnow().isoformat()

    fields = {}
    for key, val in attrs.items():
        value = val.get("value")
        if isinstance(value, (int, float, str, bool)):
            fields[key] = value
        elif isinstance(value, dict):
            # Converte dicts geo para string
            fields[key] = str(value)

    if not fields:
        print(f"[IGNORADO] {entity_id} - Nenhum campo numérico ou textual válido.")
        return None

    point = {
        "measurement": measurement,
        "tags": {
            "entity_id": entity_id
        },
        "time": timestamp,
        "fields": fields
    }
    return point

print("Inspeção do primeiro documento:")
first_doc = collection.find_one()
print(first_doc)

docs = collection.find()
count = 0

for doc in docs:
    point = convert_to_influx(doc)
    if point:
        influx_client.write_points([point])
        count += 1

print(f"\n{count} documentos migrados do Mongo para o Influx.")

def main_loop():
    print("Starting continuous sync between MongoDB and InfluxDB...")
    while True:
        for doc in collection.find():
            point = convert_to_influx(doc)
            if point:
                influx_client.write_points([point])
        print("Waiting 30 seconds...")
        time.sleep(30)

if __name__ == "__main__":
    main_loop()