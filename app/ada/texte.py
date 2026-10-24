import re
import unicodedata


def slugify(valeur):
    """Comme django.utils.text.slugify : les noms des archives déjà produites restent les mêmes."""
    valeur = unicodedata.normalize('NFKD', str(valeur)).encode('ascii', 'ignore').decode('ascii')
    valeur = re.sub(r'[^\w\s-]', '', valeur.lower())
    return re.sub(r'[-\s]+', '-', valeur).strip('-_')
