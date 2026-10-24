import os
from datetime import timedelta


def _entier(nom, defaut):
    return int(os.environ.get(nom, '') or defaut)


def depuis_environnement():
    domaine = os.environ.get('DOMAIN', 'localhost')
    max_mo = _entier('MAX_UPLOAD_SIZE_MB', 10)
    securise = os.environ.get('SESSION_COOKIE_SECURE', '1') == '1'
    return {
        'SECRET_KEY': os.environ.get('SECRET_KEY', ''),
        'DEBUG': os.environ.get('DEBUG', '0') == '1',
        'DOMAIN': domaine,
        'TRUSTED_HOSTS': [domaine, 'localhost', '127.0.0.1', 'ada'],
        # Tout est sous DATA_ROOT : ada.db, classes/, cours/, sauvegardes/, exports/
        'DATA_ROOT': os.environ.get('DATA_ROOT', '/data'),
        'SESSION_COOKIE_NAME': 'ada',
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'SESSION_COOKIE_SECURE': securise,
        'PERMANENT_SESSION_LIFETIME': timedelta(weeks=2),
        'METHODE_HACHAGE': 'scrypt',
        'ALLOWED_EXTENSIONS': tuple(
            ext.strip().lower().lstrip('.')
            for ext in os.environ.get(
                'ALLOWED_EXTENSIONS', 'pdf,zip,tar.gz,py,java,c,cpp,txt'
            ).split(',')
            if ext.strip()
        ),
        'MAX_UPLOAD_SIZE_MB': max_mo,
        'MAX_UPLOAD_FILES': _entier('MAX_UPLOAD_FILES', 10),
        # Au-delà, 413 : le formulaire et ses champs passent en plus du fichier.
        'MAX_CONTENT_LENGTH': (max_mo + 1) * 1024 * 1024,
    }
