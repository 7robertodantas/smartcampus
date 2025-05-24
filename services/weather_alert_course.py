import logging
import sys
import json
import os
import requests
from datetime import datetime, timedelta, timezone
from flask import Flask, request
import fiware
import time
import unicodedata


app = Flask(__name__)

ENTITY_ID = "WeatherStation:CampusNatal"
ORION_URL = os.environ.get("ORION_URL")
CALLBACK_URL = os.environ.get("CALLBACK_URL")
subscription_created = False

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False

HEADERS = {"Content-Type": "application/json"}


def remover_acentos(texto):
    return (
        unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    )


def formatar_iso_utc(hora_str: str) -> str:
    dt = datetime.strptime(hora_str, "%H:%M").replace(
        year=datetime.now().year,
        month=datetime.now().month,
        day=datetime.now().day,
        tzinfo=timezone.utc,
    )
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


@app.route("/notify", methods=["POST"])
def notify_weather():
    payload = request.json
    logger.info("[RECEBIDO] /notify:")
    logger.info(json.dumps(payload, indent=2))

    if "data" not in payload:
        logger.warning("Payload não contém chave 'data'")
        return "", 204

    for entity in payload["data"]:
        coords = entity.get("location", {}).get("value", {}).get("coordinates")
        if not coords:
            logger.warning("Coordenadas ausentes no payload")
            continue

        lat, lon = coords[1], coords[0]
        dia_semana = datetime.now(timezone.utc).strftime("%A")
        logger.info(f"Localização do clima: lat={lat}, lon={lon}")

        course_instances = buscar_turmas_proximas_ou_relacionadas(lat, lon)
        logger.info(f"{len(course_instances)} turmas encontradas próximas")

        for turma in course_instances:
            horarios = turma.get("classSchedule", {}).get("value", [])
            if not isinstance(horarios, list):
                logger.error(
                    f"'classSchedule.value' não é uma lista na turma {turma.get('id')}"
                )
                continue

            agora = datetime.now(timezone.utc)
            encontrou_aula_valida = False
            qtd_horas = 24
            for horario in horarios:
                dia_turma = horario.get("day")
                tempo_inicio = horario.get("startTime")
                tempo_fim = horario.get("endTime")

                if not dia_turma or not tempo_inicio or not tempo_fim:
                    logger.warning(f"Dados incompletos na turma {turma.get('id')}")
                    continue

                if dia_turma != dia_semana:
                    continue

                try:
                    inicio_horario = datetime.strptime(tempo_inicio, "%H:%M").replace(
                        year=agora.year,
                        month=agora.month,
                        day=agora.day,
                        tzinfo=timezone.utc,
                    )
                    fim_horario = datetime.strptime(tempo_fim, "%H:%M").replace(
                        year=agora.year,
                        month=agora.month,
                        day=agora.day,
                        tzinfo=timezone.utc,
                    )
                except ValueError as e:
                    logger.error(
                        f"Erro ao converter horários na turma {turma.get('id')}: {e}"
                    )
                    continue

                if (
                    agora + timedelta(hours=qtd_horas) >= inicio_horario
                    and agora <= fim_horario
                ):
                    nome_turma = turma.get("className", {}).get("value", "Desconhecida")
                    logger.info(
                        f"Turma '{nome_turma}' com aula em até {qtd_horas}h ({tempo_inicio} - {tempo_fim})"
                    )
                    encontrou_aula_valida = True
                    enviar_alerta(turma, tempo_inicio, tempo_fim)
                    logger.warning(
                        f"Enviando alerta para a turma {turma.get('id')} ({nome_turma})"
                    )
                    break

            if not encontrou_aula_valida:
                logger.info(
                    f"Nenhuma aula válida em até {qtd_horas}h na turma {turma.get('id')}"
                )

    return "", 200


def enviar_alerta(turma, tempo_inicio: str, tempo_fim: str) -> None:
    turma_id = turma.get("id")
    nome_turma = turma.get("className", {}).get("value", "Desconhecida")
    coordenadas = turma.get("location", {}).get("value", {}).get("coordinates", [])
    if not coordenadas:
        logger.error(f"Coordenadas ausentes para a turma {turma_id}")
        return

    descricao_raw = f"Possivel chuva durante a aula da turma '{nome_turma}' entre {tempo_inicio} e {tempo_fim}."
    descricao = remover_acentos(descricao_raw).replace('"', "").replace("'", "")

    alerta = {
        "id": f"Alert:Weather:{turma_id}",
        "type": "Alert",
        "category": {"value": "weather", "type": "Text"},
        "subCategory": {"value": "rainfall", "type": "Text"},
        "description": {"value": descricao, "type": "Text"},
        "location": {
            "type": "geo:json",
            "value": {"type": "Point", "coordinates": coordenadas},
        },
        "dateIssued": {
            "type": "DateTime",
            "value": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "validFrom": {"type": "DateTime", "value": formatar_iso_utc(tempo_inicio)},
        "validTo": {"type": "DateTime", "value": formatar_iso_utc(tempo_fim)},
        "alertSource": {"value": "Sistema de Monitoramento de Clima", "type": "Text"},
        "severity": {"value": "medium"},
        "affectedEntity": {"type": "Relationship", "value": turma_id},
    }

    logger.warning(f"Enviando alerta para a turma {turma_id} ({nome_turma})")
    try:
        resp = requests.post(
            "http://orion:1026/v2/entities", headers=HEADERS, json=alerta
        )
        if resp.status_code in (201, 204):
            logger.info(f"Alerta enviado para a turma '{nome_turma}'.")
        else:
            logger.error(f"Falha ao enviar alerta: {resp.status_code}\n{resp.text}")
    except Exception as exc:
        logger.exception(f"Erro ao enviar alerta: {exc}")


def buscar_turmas_proximas_ou_relacionadas(
    latitude: float, longitude: float, raio_metros: int = 5000
):
    logger.info(
        f"Buscando turmas próximas a: lat={latitude}, lon={longitude}, raio={raio_metros}m"
    )
    try:
        params_geo = {
            "type": "CourseInstance",
            "georel": f"near;maxDistance:{raio_metros}",
            "geometry": "point",
            "coords": f"{latitude},{longitude}",
        }
        response_geo = requests.get(f"{ORION_URL}/entities", params=params_geo)
        response_geo.raise_for_status()
        turmas_geo = response_geo.json()
        logger.info(f"Total de turmas próximas: {len(turmas_geo)}")

        for i, turma in enumerate(turmas_geo, start=1):
            nome = turma.get("className", {}).get("value", "Desconhecida")
            coords = turma.get("location", {}).get("value", {}).get("coordinates")
            if coords:
                lat, lon = coords[1], coords[0]
                logger.info(f"{i}. {nome} → Coordenadas: lat={lat}, lon={lon}")
            else:
                logger.warning(f"{i}. {nome} → Coordenadas ausentes")
    except requests.exceptions.RequestException as e:
        logger.error(f"Falha ao buscar turmas com georel: {e}")
        turmas_geo = []

    return turmas_geo


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

    if subscription_created:
        logger.info("Inscrição criada com sucesso.")
    else:
        logger.error("Falha ao criar inscrição.")


def esperar_orion_disponivel(max_tentativas=100, intervalo=5):
    logger.info("Verificando disponibilidade do Orion...")
    url_teste = "http://orion:1026/version"
    for tentativa in range(max_tentativas):
        try:
            resposta = requests.get(url_teste)
            if resposta.status_code == 200:
                logger.info(f"Orion respondeu na tentativa {tentativa + 1}")
                return
        except requests.exceptions.RequestException as e:
            logger.info(f"Orion ainda não está pronto: {e}")
        time.sleep(intervalo)
    logger.error("Orion não respondeu a tempo.")
    sys.exit(1)
