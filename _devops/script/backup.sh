#!/bin/bash

# Script de sauvegarde de la base de données
# Usage: ./backup.sh [--env-file <path>]
#
# Le script lit les credentials DB depuis le fichier .env.prod
# (par défaut : _devops/docker/.env.prod depuis la racine du dépôt).

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/_devops/docker/docker-compose.prod.yml"
BACKUP_DIR="$REPO_ROOT/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"
ENV_FILE="$REPO_ROOT/_devops/docker/.env.prod"
RETENTION_DAYS=30

# ── Parse arguments ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --env-file) ENV_FILE="$2"; shift 2 ;;
        *) echo "Option inconnue: $1" >&2; exit 1 ;;
    esac
done

# ── Charger les variables d'environnement ────────────────────────────────────
if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERREUR: Fichier d'environnement introuvable: $ENV_FILE" >&2
    echo "Copiez .env.prod.example -> .env.prod et renseignez les valeurs." >&2
    exit 1
fi

# Extraire POSTGRES_USER et POSTGRES_DB depuis le fichier .env
POSTGRES_USER=$(grep -E '^POSTGRES_USER=' "$ENV_FILE" | head -1 | cut -d'=' -f2-)
POSTGRES_DB=$(grep -E '^POSTGRES_DB=' "$ENV_FILE" | head -1 | cut -d'=' -f2-)

if [[ -z "$POSTGRES_USER" || -z "$POSTGRES_DB" ]]; then
    echo "ERREUR: POSTGRES_USER ou POSTGRES_DB non défini dans $ENV_FILE" >&2
    exit 1
fi

# ── Créer le dossier de backup ───────────────────────────────────────────────
mkdir -p "$BACKUP_DIR"

echo "Création du backup de la base de données..."
echo "  Base    : $POSTGRES_DB"
echo "  Utilisateur : $POSTGRES_USER"

# ── Dump de la base de données ───────────────────────────────────────────────
if ! docker compose -f "$COMPOSE_FILE" exec -T db pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --no-owner \
    --no-privileges \
    > "$BACKUP_FILE"; then
    echo "ERREUR: pg_dump a échoué." >&2
    rm -f "$BACKUP_FILE"
    exit 1
fi

# ── Vérification d'intégrité ────────────────────────────────────────────────
# Vérifie que le fichier n'est pas vide et contient bien un dump PostgreSQL
FILESIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || stat -f%z "$BACKUP_FILE" 2>/dev/null || echo 0)

if [[ "$FILESIZE" -lt 100 ]]; then
    echo "ERREUR: Le backup est trop petit (${FILESIZE} octets) — probablement vide ou corrompu." >&2
    rm -f "$BACKUP_FILE"
    exit 1
fi

if ! head -5 "$BACKUP_FILE" | grep -q "PostgreSQL database dump"; then
    echo "ERREUR: Le fichier ne ressemble pas à un dump PostgreSQL valide." >&2
    rm -f "$BACKUP_FILE"
    exit 1
fi

# ── Compression ──────────────────────────────────────────────────────────────
gzip "$BACKUP_FILE"
COMPRESSED_SIZE=$(du -h "$BACKUP_FILE.gz" | cut -f1)
echo "Backup créé: $BACKUP_FILE.gz ($COMPRESSED_SIZE)"

# ── Nettoyage des anciens backups ────────────────────────────────────────────
echo "Nettoyage des anciens backups (>${RETENTION_DAYS} jours)..."
DELETED=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
echo "  $DELETED ancien(s) backup(s) supprimé(s)."

echo "Backup terminé avec succès!"
