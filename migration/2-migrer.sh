#!/bin/bash
# Migration Django/MySQL -> Flask/SQLite, etape 2 : arret de l'ancienne application, puis
# reprise des donnees et des fichiers dans le volume ada_data (flask importer-mysql).
#
#   migration/2-migrer.sh migration-mysql/<date>
#
# ada-mysql reste lance (lecture seule) ; les volumes db_data et uploads ne sont pas touches.
# Au moindre ecart avec les exports de l'etape 1, rien n'est garde dans ada_data (hors
# sauvegarde recopiee) : corriger, vider le volume (docker volume rm ada_data) et relancer.
set -euo pipefail

cd "$(dirname "$0")/.."

DOSSIER=$(realpath "${1:?usage : migration/2-migrer.sh migration-mysql/<date>}")
MYSQL=${ANCIEN_MYSQL:-ada-mysql}
ANCIENS=${ANCIENS_WEB:-ada-auth ada-cours}
RESEAU=${ANCIEN_RESEAU:-ada_backend}
UPLOADS=${ANCIEN_UPLOADS:-ada_uploads}
DATA=${VOLUME_DATA:-ada_data}
IMAGE=${IMAGE:-ada}

if [ ! -f "$DOSSIER/SHA256SUMS" ]; then
  echo "$DOSSIER/SHA256SUMS absent : lancer d'abord migration/1-sauvegarder-mysql.sh." >&2
  exit 1
fi
if ! docker ps --format '{{.Names}}' | grep -qx "$MYSQL"; then
  echo "Conteneur $MYSQL arrete : la base MySQL doit etre lisible." >&2
  exit 1
fi

echo "Arret de l'ancienne application (plus aucune ecriture) : $ANCIENS"
for conteneur in $ANCIENS; do
  docker stop "$conteneur" >/dev/null 2>&1 || true
done

docker build -q -t "$IMAGE" app >/dev/null
# Etiquettes compose : le volume est ensuite celui du service ada de docker-compose.yml.
docker volume create --label com.docker.compose.project=ada --label com.docker.compose.volume=data \
  "$DATA" >/dev/null

docker run --rm \
  --network "$RESEAU" \
  -v "$DATA":/data \
  -v "$UPLOADS":/ancien-uploads:ro \
  -v "$DOSSIER":/avant-migration:ro \
  -e SECRET_KEY=migration \
  -e MYSQL_HOST="$MYSQL" \
  -e MYSQL_USER="$(docker exec "$MYSQL" printenv MYSQL_USER)" \
  -e MYSQL_PASSWORD="$(docker exec "$MYSQL" printenv MYSQL_PASSWORD)" \
  -e MYSQL_DATABASE="$(docker exec "$MYSQL" printenv MYSQL_DATABASE)" \
  "$IMAGE" flask importer-mysql

cat <<FIN

Migration terminee. Ensuite (detail dans install.md) :
  1. .env : SECRET_KEY ;
  2. ./start.sh (retire ada-auth, ada-cours et ada-mysql ; leurs volumes restent) ;
  3. argos : ada.mips.science et ada.localhost vers le conteneur ada (port 8000),
     sans le fragment sites-extra (/cours/ est servi par ada), puis apply ;
  4. copier les pages de cours : docker compose cp content/. ada:/data/cours/
  5. verifier connexion, devoirs, fichiers ; plus tard seulement :
     docker volume rm ada_db_data ada_uploads
FIN
