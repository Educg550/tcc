from flask import g, request, has_request_context
from app.config import load_config
from flask_babel import Babel
from flask_seasurf import SeaSurf
from senhaunicapy import SenhaUnica
from celery import Celery
import redis

LANGUAGES = ["pt", "en"]


def get_locale():
    if not has_request_context():
        return "pt"

    if g.get("lang_code") in LANGUAGES:
        return g.lang_code

    best_match_language = request.accept_languages.best_match(LANGUAGES)
    if best_match_language is None:
        return "pt"

    return best_match_language


babel = Babel(locale_selector=get_locale)
csrf = SeaSurf()
senhaunica = SenhaUnica()

config = load_config()

celery = Celery("mailer", broker=config["REDIS_URL"], backend=config["REDIS_URL"])
r = redis.Redis.from_url(config["REDIS_URL"])
