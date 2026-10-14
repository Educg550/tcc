from datetime import datetime
import smtplib
import socket
from email.message import EmailMessage
from typing import TypedDict

from flask import json

from app.common.Result import Result
from app.exceptions.error_messages import EMAIL_ERROR, SUBMIT_EMAIL
from app.logger import Logger

DEFAULT_PORT = 587
DEFAULT_USE_TLS = False


class EmailType(TypedDict):
    to_addrs: list
    subject: str
    body: dict[str, str]
    preamble: str = None


class Email:
    def __init__(self, config):
        if "SMTP_SERVER" not in config and "SMTP_USER" not in config:
            raise Exception(__name__, "Default values for sending email not defined.")

        self.config = {
            "server": config["SMTP_SERVER"],
            "port": int(config["SMTP_PORT"]) if "SMTP_PORT" in config else DEFAULT_PORT,
            "user": config["SMTP_USER"],
            "password": config["SMTP_PASSWORD"] if "SMTP_PASSWORD" in config else None,
            "use_tls": (
                config["SMTP_USE_TLS"] if "SMTP_USE_TLS" in config else DEFAULT_USE_TLS
            ),
        }

    def send_queue(self, email_data: EmailType, priority=1) -> bool:
        from app.tasks import QUEUE_KEY, process_send_queue
        from app.extension import r

        timestamp = datetime.now().timestamp()
        score = priority * 1e10 + timestamp
        r.zadd(QUEUE_KEY, {json.dumps(email_data): score})
        process_send_queue.delay()
        return Result(True, message=SUBMIT_EMAIL())

    def send(self, email_data: EmailType) -> bool:
        to_addrs = email_data.get("to_addrs")
        subject = email_data.get("subject")
        body = email_data.get("body")
        preamble = email_data.get("preamble", None)

        server = None
        try:
            server = smtplib.SMTP(self.config["server"], self.config["port"])

            if self.config["use_tls"]:
                server.starttls()
            if self.config["password"] is not None:
                server.login(self.config["user"], self.config["password"])

            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = self.config["user"]
            msg["To"] = ", ".join(to_addrs)

            if isinstance(body, str):
                msg.set_content(body)
            elif isinstance(body, dict):
                if "default" not in body and "plain" not in body and "html" not in body:
                    raise Exception(__name__, "A valid type is required.")

                if "default" in body:
                    msg.set_content(body["default"])
                elif "plain" in body:
                    msg.set_content(body["plain"])

                if "html" in body:
                    msg.add_alternative(body["html"], subtype="html")

            if preamble is not None:
                msg.preamble = f"{preamble}\#n"

            server.send_message(msg)
        except socket.error as e:
            Logger.print.warning(e)
            return Result(message=EMAIL_ERROR())
        except Exception as e:
            Logger.print.warning(e)
            if server is not None:
                server.quit()
            return Result(message=EMAIL_ERROR())

        if server is not None:
            server.quit()
        return Result(True, message=SUBMIT_EMAIL())
