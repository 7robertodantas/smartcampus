import time
import logging
import sys
import json
import os
import requests
from datetime import datetime, timedelta, timezone
from requests.exceptions import ConnectionError, HTTPError, Timeout, RequestException
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
    print("\n[RECEBIDO] /notify:")
    print(json.dumps(payload, indent=2))

    if "data" not in payload:
        print("[AVISO] Payload não contém chave 'data'")
        return "", 204

    agora = datetime.now(timezone.utc)
    daqui_5h = agora + timedelta(hours=5)
    dia_semana = daqui_5h.strftime("%A")
    hora_verificada = daqui_5h.strftime("%H:%M")
    print(f"[INFO] Verificando turmas para {dia_semana} às {hora_verificada}")

    for entity in payload["data"]:
        coords = entity.get("location", {}).get("value", {}).get("coordinates")
        if not coords:
            print("[AVISO] Coordenadas ausentes no payload")
            continue

        lat, lon = coords[1], coords[0]
        print(f"[INFO] Localização do clima: lat={lat}, lon={lon}")

        course_instances = buscar_turmas_proximas_ou_relacionadas(lat, lon)
        print(f"[INFO] {len(course_instances)} turmas encontradas próximas")

        for turma in course_instances:
            nome_turma = turma.get("className", {}).get("value", "Desconhecida")
            print(f"[INFO] Verificando horários da turma: {nome_turma}")

            horarios = turma.get("classSchedule", {}).get("value", [])
            for horario in horarios:
                print(f"[DEBUG] Horário da turma: {horario}")
                if (
                    horario["day"] == dia_semana
                    and horario["startTime"] == hora_verificada
                ):
                    print(
                        f"⚠️ ALERTA: Aula da turma '{nome_turma}' ocorrerá daqui a 5h."
                    )
                    # Aqui você pode acionar outra função de notificação (ex: enviar_push(turma))
                    break

    return "", 200


# def buscar_turmas_proximas_ou_relacionadas(latitude: float, longitude: float, raio_metros: int = 1000, filtros: dict = None):
#     params = {
#         "type": "CourseInstance",
#         "georel": f"near;maxDistance:{raio_metros}",
#         "geometry": "point",
#         "coords": f"{longitude},{latitude}"
#     }

#     if filtros:
#         condicoes = [f"{k}=={v}" for k, v in filtros.items()]
#         params["q"] = ";".join(condicoes)

#     try:
#         response = requests.get(f"{ORION_URL}/entities", params=params)
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"[ERRO] Falha na requisição: {e}")
#         return []


def buscar_turmas_proximas_ou_relacionadas(
    latitude: float, longitude: float, raio_metros: int = 1000, filtros: dict = None
):
    print("\n[DEBUG] Iniciando busca por turmas próximas...")
    print(f"[DEBUG] Latitude recebida: {latitude}")
    print(f"[DEBUG] Longitude recebida: {longitude}")
    print(f"[DEBUG] Raio: {raio_metros} metros")
    print(f"[DEBUG] Filtros recebidos: {filtros}")

    # 1️⃣ TESTE SEM georel (apenas type=CourseInstance)
    print("[DEBUG] TESTE 1: Buscando todas as entidades CourseInstance sem georel...")
    try:
        response_tipo = requests.get(
            f"{ORION_URL}/entities", params={"type": "CourseInstance"}
        )
        print(f"[DEBUG] Status HTTP (sem georel): {response_tipo.status_code}")
        print(f"[DEBUG] Resultado bruto (sem georel): {response_tipo.text}")
        response_tipo.raise_for_status()
        entidades_sem_georel = response_tipo.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Erro ao buscar entidades apenas por tipo: {e}")
        return []

    # 2️⃣ TESTE COM georel
    params_geo = {
        "type": "CourseInstance",
        "georel": f"near;maxDistance:{raio_metros}",
        "geometry": "point",
        "coords": f"{longitude},{latitude}",
    }

    print(f"[DEBUG] Parâmetros da requisição com georel: {params_geo}")
    try:
        response_geo = requests.get(f"{ORION_URL}/entities", params=params_geo)
        print(f"[DEBUG] Status HTTP (com georel): {response_geo.status_code}")
        print(f"[DEBUG] Resultado bruto (com georel): {response_geo.text}")
        response_geo.raise_for_status()
        entidades_com_georel = response_geo.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Erro ao buscar entidades com georel: {e}")
        return []

    # 3️⃣ COMPARAÇÃO
    print(
        f"[RESULTADO] Total de entidades CourseInstance (sem georel): {len(entidades_sem_georel)}"
    )
    print(
        f"[RESULTADO] Total de entidades encontradas (com georel): {len(entidades_com_georel)}"
    )

    # 4️⃣ Retorno final: prioriza georel se existir
    if entidades_com_georel:
        return entidades_com_georel
    elif entidades_sem_georel:
        print(
            "[AVISO] Entidades existem, mas não foram retornadas via georel. Verifique índice geo."
        )
        return entidades_sem_georel
    else:
        print("[AVISO] Nenhuma entidade CourseInstance encontrada no Orion.")
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
