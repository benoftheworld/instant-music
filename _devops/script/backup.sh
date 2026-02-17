#!/bin/bash

# Script de sauvegarde de la base de données
# Usage: ./backup.sh

set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

# Créer le dossier de backup s'il n'existe pas
mkdir -p $BACKUP_DIR

echo "📦 Création du backup de la base de données..."

# Backup de la base de données
docker compose -f _devops/docker/docker-compose.prod.yml exec -T db pg_dump -U instantmusic_user instantmusic_prod > $BACKUP_FILE

# Compresser le backup
gzip $BACKUP_FILE

echo "✅ Backup créé: $BACKUP_FILE.gz"

# Nettoyer les backups de plus de 30 jours
echo "🧹 Nettoyage des anciens backups (>30 jours)..."
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "✅ Backup terminé avec succès!"
