import logging
import sys
import json
import os
import requests
from datetime import datetime, timedelta, timezone
from flask import Flask, request
import fiware

app = Flask(__name__)

ENTITY_ID = "WeatherStation:CampusNatal"
ORION_URL = os.environ.get("ORION_URL")
CALLBACK_URL = os.environ.get("CALLBACK_URL")
subscription_created = False

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False


@app.route("/notify", methods=["POST"])
def notify_weather():
    payload = request.json
    logger.info("\n[RECEBIDO] /notify:")
    logger.info(json.dumps(payload, indent=2))

    if "data" not in payload:
        logger.warning("[AVISO] Payload não contém chave 'data'")
        return "", 204

    agora = datetime.now(timezone.utc)
    daqui_5h = agora + timedelta(hours=5)
    dia_semana = daqui_5h.strftime("%A")
    hora_verificada = daqui_5h.strftime("%H:%M")
    logger.info(f"Verificando turmas para {dia_semana} às {hora_verificada}")

    for entity in payload["data"]:
        coords = entity.get("location", {}).get("value", {}).get("coordinates")
        if not coords:
            logger.warning("[AVISO] Coordenadas ausentes no payload")
            continue

        lat, lon = coords[1], coords[0]
        logger.debug(f"Localização do clima: lat={lat}, lon={lon}")

        course_instances = buscar_turmas_proximas_ou_relacionadas(lat, lon)
        logger.info(f"{len(course_instances)} turmas encontradas próximas")

        for turma in course_instances:
            nome_turma = turma.get("className", {}).get("value", "Desconhecida")
            logger.info(f"Verificando horários da turma: {nome_turma}")

            horarios = turma.get("classSchedule", {}).get("value", [])
            for horario in horarios:
                logger.debug(f"Horário da turma: {horario}")
                if (
                    horario["day"] == dia_semana
                    and horario["startTime"] == hora_verificada
                ):
                    logger.debug(
                        f"ALERTA: Aula da turma '{nome_turma}' ocorrerá daqui a 5h."
                    )
                    # Aqui você pode acionar outra função de notificação (ex: enviar_push(turma))
                    break

    return "", 200


def buscar_turmas_proximas_ou_relacionadas(
    latitude: float, longitude: float, raio_metros: int = 1000, filtros: dict = None
):
    logger.debug("\nIniciando busca por turmas próximas...")
    logger.debug(f"Latitude recebida: {latitude}")
    logger.debug(f"Longitude recebida: {longitude}")
    logger.debug(f"Raio: {raio_metros} metros")
    logger.debug(f"Filtros recebidos: {filtros}")

    params = {
        "type": "CourseInstance",
        "georel": f"near;maxDistance:{raio_metros}",
        "geometry": "point",
        "coords": f"{latitude},{longitude}",
    }

    if filtros:
        condicoes = [f"{k}=={v}" for k, v in filtros.items()]
        params["q"] = ";".join(condicoes)

    try:
        response = requests.get(f"{ORION_URL}/entities", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Falha na requisição: {e}")
        return []


def register_subscription():
    global subscription_created
    if subscription_created:
        return

    subscription = {
        "description": "Alerta de tempo para aulas",
        "subject": {
            "entities": [{"id": ENTITY_ID, "type": "WeatherStation"}],
            "condition": {"attrs": ["weathercode"]},
        },
        "notification": {
            "http": {"url": CALLBACK_URL},
            "attrs": ["weathercode", "timestamp", "location"],
        },
        "throttling": 5,
    }

    subscription_created = fiware.register_subscription(subscription)


with app.app_context():
    register_subscription()

if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
