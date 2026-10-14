from app import create_app
from app.config import load_config
from app.extension import celery, r
from celery.utils.log import get_task_logger

from .services.file_service import UPLOAD_FOLDER
from .persistence.db import db
from flask import json
import os

logger = get_task_logger(__name__)

QUEUE_KEY = "email_queue_prioritized"

flask_app = create_app()


config = load_config()


@celery.task(rate_limit="12/m")
def process_send_queue():
    from app.services.email_service import Email

    email = Email(config)

    items = r.zrange(QUEUE_KEY, 0, 0)
    if not items:
        return "Fila vazia"

    email_json = items[0]
    email_data = json.loads(email_json)

    r.zrem(QUEUE_KEY, email_json)

    email.send(email_data)

    if r.zcard(QUEUE_KEY) > 0:
        process_send_queue.delay()


@celery.task
def unused_uploads():
    logger.info("Periodic Task...")

    all_uploads_file = []
    folder = ""
    for root, _, files in os.walk(UPLOAD_FOLDER):
        folder = root
        for file in files:
            all_uploads_file.append(file)

    sql_string = """
        select responses.value from responses
        inner join form_field
            on responses.field_id = form_field.id
        where
            form_field.type = 'File'
    """
    all_uploads_db = []
    with db.transaction() as f:
        raw = f.sql_dict(sql_string, (), callback=lambda x: x.fetchall())
        all_uploads_db = [value["value"] for value in raw if value["value"]]

    for upload_file in all_uploads_file:
        filepath = os.path.join(folder, upload_file)
        if upload_file not in all_uploads_db:
            os.remove(filepath)
            logger.info(
                f"[Limpeza] {upload_file} arquivo não usado removido de {folder}"
            )
    for upload_db in all_uploads_db:
        if upload_db not in all_uploads_file:
            logger.info(f"[Limpeza] {upload_db} arquivo sem referência em {folder}")

    logger.info(
        f"[Limpeza] {len(all_uploads_file)} arquivos e {len(all_uploads_db)} referências"
    )


celery.conf.beat_schedule = {
    "unused_uploads": {
        "task": "app.tasks.unused_uploads",
        # 'schedule': crontab(hour=0, minute=0),
        "schedule": 60.0 * 60.0,
        "args": (),
    },
}
