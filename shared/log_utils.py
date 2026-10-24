import logging
from datetime import datetime


class PlatformeFormatter(logging.Formatter):
    """Format : [YYYY-MM-DD HH:MM:SS] LEVEL user=ID class=CLASSE ip=IP METHOD /path STATUS [message]"""

    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        user = getattr(record, 'user', '-')
        classe = getattr(record, 'classe', '-')
        ip = getattr(record, 'ip', '-')
        method = getattr(record, 'method', '-')
        path = getattr(record, 'path', '-')
        status = getattr(record, 'status', '-')
        message = record.getMessage()
        parts = [f"[{timestamp}] {level} user={user} class={classe} ip={ip} {method} {path} {status}"]
        if message:
            parts.append(f"[{message}]")
        return ' '.join(parts)


def configurer_logging(nom_service):
    # stdout seulement : le driver syslog du conteneur l'envoie a argos.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(PlatformeFormatter())

    logger = logging.getLogger(nom_service)
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    return logger
