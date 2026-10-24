FROM python:3.12-slim

# TZ : heure des journaux. Les dates en base sont en UTC (ada/temps.py).
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=ada \
    DATA_ROOT=/data \
    TZ=Europe/Paris

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ada ada
COPY wsgi.py .

# Le volume de données est initialisé avec ce dossier (et son propriétaire) au premier montage.
RUN useradd --uid 1000 --create-home ada && mkdir -p /data && chown ada:ada /data
USER ada

EXPOSE 8000

# Bases au dernier schéma (sauvegarde avant toute migration), puis le serveur.
CMD ["sh", "-c", "flask migrer && exec gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 3 --access-logfile -"]
