import logging
import sys
import json
import os
from datetime import datetime, timedelta, timezone
from flask import Flask, request
import fiware
import unicodedata

app = Flask(__name__)

ENTITY_ID = "WeatherStation:CampusNatal"
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


def remove_accents(text):
    return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII")


def format_iso_utc(time_str: str) -> str:
    dt = datetime.strptime(time_str, "%H:%M").replace(
        year=datetime.now().year,
        month=datetime.now().month,
        day=datetime.now().day,
        tzinfo=timezone.utc,
    )
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


@app.route("/notify", methods=["POST"])
def notify_weather():
    payload = request.json
    logger.info("[RECEIVED] /notify:")
    logger.info(json.dumps(payload, indent=2))

    if "data" not in payload:
        logger.warning("Payload does not contain 'data' key")
        return "", 204

    for entity in payload["data"]:
        coords = entity.get("location", {}).get("value", {}).get("coordinates")
        if not coords:
            logger.warning("Coordinates missing in payload")
            continue

        lat, lon = coords[1], coords[0]
        weekday = datetime.now(timezone.utc).strftime("%A")
        logger.info(f"Weather location: lat={lat}, lon={lon}")

        course_instances = find_nearby_or_related_courses(lat, lon)
        logger.info(f"{len(course_instances)} nearby courses found")

        for course in course_instances:
            schedules = course.get("classSchedule", {}).get("value", [])
            if not isinstance(schedules, list):
                logger.error(
                    f"'classSchedule.value' is not a list in course {course.get('id')}"
                )
                continue

            now = datetime.now(timezone.utc)
            found_valid_class = False
            hours_ahead = 24
            for schedule in schedules:
                course_day = schedule.get("day")
                start_time = schedule.get("startTime")
                end_time = schedule.get("endTime")

                if not course_day or not start_time or not end_time:
                    logger.warning(f"Incomplete data in course {course.get('id')}")
                    continue

                if course_day != weekday:
                    continue

                try:
                    start_dt = datetime.strptime(start_time, "%H:%M").replace(
                        year=now.year,
                        month=now.month,
                        day=now.day,
                        tzinfo=timezone.utc,
                    )
                    end_dt = datetime.strptime(end_time, "%H:%M").replace(
                        year=now.year,
                        month=now.month,
                        day=now.day,
                        tzinfo=timezone.utc,
                    )
                except ValueError as e:
                    logger.error(
                        f"Error converting times in course {course.get('id')}: {e}"
                    )
                    continue

                if now + timedelta(hours=hours_ahead) >= start_dt and now <= end_dt:
                    course_id = course.get("id", "Unknown")
                    logger.info(
                        f"Course '{course_id}' with class within {hours_ahead}h ({start_time} - {end_time})"
                    )
                    found_valid_class = True
                    send_alert(course, start_time, end_time)
                    logger.warning(
                        f"Sending alert for course {course.get('id')} ({course_id})"
                    )
                    break

            if not found_valid_class:
                logger.info(
                    f"No valid class within {hours_ahead}h in course {course.get('id', 'Unknown')}"
                )

    return "", 200


def send_alert(course, start_time: str, end_time: str) -> None:
    course_id = course.get("id", "Unknown")
    course_id_value = course.get("id", "Unknown")
    coordinates = course.get("location", {}).get("value", {}).get("coordinates", [])
    if not coordinates:
        logger.error(f"Coordinates missing for course {course_id}")
        return

    raw_description = f"Possible rain during the class of course '{course_id_value}' between {start_time} and {end_time}."
    description = remove_accents(raw_description).replace('"', "").replace("'", "")

    alert_id = f"Alert:Weather:{course_id}"
    full_alert = {
        "id": alert_id,
        "type": "Alert",
        "category": {"value": "weather", "type": "Text"},
        "subCategory": {"value": "rainfall", "type": "Text"},
        "description": {"value": description, "type": "Text"},
        "location": {
            "type": "geo:json",
            "value": {"type": "Point", "coordinates": coordinates},
        },
        "dateIssued": {
            "type": "DateTime",
            "value": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "validFrom": {"type": "DateTime", "value": format_iso_utc(start_time)},
        "validTo": {"type": "DateTime", "value": format_iso_utc(end_time)},
        "alertSource": {"value": "Weather Monitoring System", "type": "Text"},
        "severity": {"value": "medium"},
        "affectedEntity": {"type": "Relationship", "value": course_id},
    }

    logger.warning(f"Sending alert for course {course_id} ({course_id_value})")

    try:
        fiware.upsert_entity(full_alert)
        logger.info(f"Alert processed successfully for course '{course_id_value}'.")
    except Exception as exc:
        logger.exception(f"Error sending/updating alert: {exc}")


def find_nearby_or_related_courses(
    latitude: float, longitude: float, radius_meters: int = 5000
):
    return fiware.find_entities_nearby(
        "CourseInstance", latitude, longitude, radius_meters
    )


def register_subscription():
    global subscription_created
    if subscription_created:
        return

    subscription = {
        "description": "Weather alert for classes",
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
        logger.info("Subscription created successfully.")
    else:
        logger.error("Failed to create subscription.")


with app.app_context():
    register_subscription()

if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
