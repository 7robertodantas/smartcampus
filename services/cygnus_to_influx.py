from fastapi import FastAPI, Request
from influxdb import InfluxDBClient
from datetime import datetime
import logging

app = FastAPI()
influx = InfluxDBClient(host="influxdb", database="smartcampus")
logging.basicConfig(level=logging.INFO)

@app.post("/cygnus-webhook")
async def handle_data(request: Request):
    data = await request.json()
    logging.info("Webhook recebido: %s", data)
    
    points = []
    for entity in data:
        entity_id = entity.get("id")
        for attr in entity.get("attributes", []):
            try:
                value = float(attr["value"])
            except (ValueError, TypeError):
                continue
            point = {
                "measurement": "iot_data",
                "tags": {"entity_id": entity_id},
                "time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "fields": {attr["name"]: value}
            }
            points.append(point)

    if points:
        influx.write_points(points)
        logging.info("Dados gravados no Influx: %s", points)
    else:
        logging.warning("Nenhum ponto válido encontrado.")

    return {"status": "ok"}
