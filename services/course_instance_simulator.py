import logging
import os
import json
import fiware
from datetime import datetime, timedelta, timezone
import time

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False

ENTITY_TYPE = "CourseInstance"
ENTITIES_DIR = os.environ.get("ENTITIES_DIR")

headers = {"Content-Type": "application/json", "Accept": "application/json"}

get_delete_headers = {"Accept": "application/json"}


def create_entity_from_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            entity = json.load(file)
            fiware.create_entity(entity)
    except Exception as e:
        logger.error(f"Error processing {filepath}: {e}")


def update_course_schedule():
    course_id = "CourseInstance:UFRN:PPGTI3004:2025.1"  # Change to your course ID

    logger.info(f"Updating schedule for course {course_id}...")

    now = datetime.now(timezone.utc)
    new_day = now.strftime("%A")
    new_start = (now + timedelta(hours=1, minutes=30)).strftime("%H:%M")
    new_end = (now + timedelta(hours=2, minutes=30)).strftime("%H:%M")

    logger.info(f"New day: {new_day}")
    logger.info(f"Start time: {new_start}")
    logger.info(f"End time: {new_end}")

    new_schedule = {
        "classSchedule": {
            "value": [{"day": new_day, "startTime": new_start, "endTime": new_end}],
            "type": "StructuredValue",
        }
    }

    try:
        fiware.update_entity(course_id, new_schedule)
        logger.info(f"Schedule for course {course_id} updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update schedule for course {course_id}.")


def main():
    if not os.path.isdir(ENTITIES_DIR):
        logger.error(f"Folder '{ENTITIES_DIR}' not found.")
        return

    fiware.delete_all_entities(ENTITY_TYPE)

    logger.info("Waiting for 1 second before creating entities...")
    time.sleep(1)

    for filename in os.listdir(ENTITIES_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(ENTITIES_DIR, filename)
            create_entity_from_file(filepath)

    update_course_schedule()
    logger.info("All entities created and updated successfully.")


if __name__ == "__main__":
    fiware.wait_for_orion()
    main()
