#!/bin/bash
# Migration Django/MySQL -> Flask/SQLite, etape 1 : sauvegardes et exports de l'ancienne
# version, pendant qu'elle tourne encore (conteneurs ada-mysql et ada-auth).
#
#   migration/1-sauvegarder-mysql.sh [dossier]     (defaut : migration-mysql/<date>)
#
# Produit : mysql.sql.gz (dump complet), uploads.tar.gz (volume uploads),
# exports/classe-<id>.zip (archive de chaque classe par l'ancien archiver_classe),
# SHA256SUMS. L'etape 2 verifie ces sommes, recopie le dossier dans le nouveau volume
# et compare chaque classe migree a son export.
#
# Enchainer avec l'etape 2 sans laisser les etudiants deposer entre les deux (page de
# maintenance d'argos, ou hors des heures de cours) : un rendu depose apres l'export
# fait echouer la comparaison, et il faut recommencer l'etape 1.
set -euo pipefail

cd "$(dirname "$0")/.."

MYSQL=${ANCIEN_MYSQL:-ada-mysql}
AUTH=${ANCIEN_AUTH:-ada-auth}

for conteneur in "$MYSQL" "$AUTH"; do
  if ! docker ps --format '{{.Names}}' | grep -qx "$conteneur"; then
    echo "Conteneur $conteneur arrete : l'ancienne version doit tourner pour cette etape." >&2
    exit 1
  fi
done

DOSSIER=${1:-migration-mysql/$(date +%Y%m%d-%H%M%S)}
if [ -e "$DOSSIER" ] && [ -n "$(ls -A "$DOSSIER")" ]; then
  echo "$DOSSIER existe et n'est pas vide." >&2
  exit 1
fi
mkdir -p "$DOSSIER/exports"

echo "Dump MySQL..."
docker exec "$MYSQL" sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysqldump -uroot --single-transaction \
  --routines --triggers --default-character-set=utf8mb4 "$MYSQL_DATABASE"' | gzip > "$DOSSIER/mysql.sql.gz"
if ! gzip -dc "$DOSSIER/mysql.sql.gz" | tail -n 1 | grep -q 'Dump completed'; then
  echo "Dump MySQL incomplet." >&2
  exit 1
fi

echo "Fichiers deposes (volume uploads)..."
docker exec "$AUTH" tar -C /uploads -cf - . | gzip > "$DOSSIER/uploads.tar.gz"
gzip -t "$DOSSIER/uploads.tar.gz"

echo "Export de chaque classe..."
# Marqueur : selon la version, « manage.py shell » ecrit aussi sur la sortie standard.
ids=$(docker exec "$AUTH" python manage.py shell -c \
  "from core.models import Classe; print('IDS:', *Classe.objects.order_by('id').values_list('id', flat=True))" \
  | sed -n 's/^IDS://p')
for id in $ids; do
  docker exec "$AUTH" python manage.py archiver_classe "$id" > "$DOSSIER/exports/classe-$id.zip"
done

(cd "$DOSSIER" && find . -type f ! -name SHA256SUMS -printf '%P\n' | sort | xargs -r sha256sum > SHA256SUMS)

echo
echo "Sauvegarde et exports dans $DOSSIER :"
(cd "$DOSSIER" && du -h mysql.sql.gz uploads.tar.gz && echo "$(echo $ids | wc -w) classe(s) exportee(s)")
echo "Copier ce dossier hors du serveur, puis : migration/2-migrer.sh $DOSSIER"
