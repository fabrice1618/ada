"""Dates : stockées en UTC (texte ISO 8601, microsecondes fixes : l'ordre du texte est
celui du temps), affichées et saisies à l'heure de Paris."""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

FUSEAU = ZoneInfo('Europe/Paris')


def maintenant():
    return datetime.now(timezone.utc)


def iso(valeur):
    if valeur is None:
        return None
    if valeur.tzinfo is None:
        raise ValueError(f"date sans fuseau : {valeur!r}")
    return valeur.astimezone(timezone.utc).isoformat(timespec='microseconds')


def lire(texte):
    return datetime.fromisoformat(texte) if texte else None


def lire_jour(texte):
    return date.fromisoformat(texte) if texte else None


def local(valeur):
    return valeur.astimezone(FUSEAU)


def depuis_saisie(texte, formats=('%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S')):
    """Champ datetime-local (heure de Paris) -> date UTC ; None s'il est illisible."""
    for fmt in formats:
        try:
            return datetime.strptime(texte, fmt).replace(tzinfo=FUSEAU)
        except (TypeError, ValueError):
            continue
    return None
