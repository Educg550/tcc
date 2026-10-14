import os
import logging
from logging.handlers import RotatingFileHandler


class LevelFilter(object):
    def __init__(self, level):

        self.level = []
        if isinstance(level, list):
            for local_level in level:
                self.level.append(logging._checkLevel(local_level))
        else:
            self.level.append(logging._checkLevel(level))

    def filter(self, record):
        isFiltered = False
        for local_level in self.level:
            if record.levelno == local_level:
                isFiltered = True
        return isFiltered


class Logger:
    @staticmethod
    def config(app, foldername="logs"):
        app.logger.setLevel(logging.INFO)

        os.makedirs(foldername, exist_ok=True)

        Logger.print = app.logger
        handler = RotatingFileHandler(
            os.path.join(foldername, "app.log"), maxBytes=10000, backupCount=5
        )
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(module)s:%(funcName)s - %(message)s"
        )
        handler.addFilter(LevelFilter(["ERROR", "CRITICAL"]))
        handler.setFormatter(formatter)
        Logger.print.addHandler(handler)
        return Logger.print
