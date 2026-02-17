#!/bin/bash

# Script de déploiement automatique pour InstantMusic
# Usage: ./deploy.sh [development|production]

set -e

ENV=${1:-production}
COMPOSE_FILE="_devops/docker/docker-compose.yml"

if [ "$ENV" = "production" ]; then
    COMPOSE_FILE="_devops/docker/docker-compose.prod.yml"
    # Allow .env.prod either at repo root or in the _devops/docker folder
    ENV_FILE_ROOT=".env.prod"
    ENV_FILE_DOCKER="_devops/docker/.env.prod"

    echo "🚀 Déploiement en PRODUCTION"

    # If .env.prod exists at repo root, copy it to _devops/docker for the compose file
    if [ -f "$ENV_FILE_ROOT" ]; then
        echo "ℹ️  Found $ENV_FILE_ROOT at repo root — copying to _devops/docker/.env.prod"
        mkdir -p _devops/docker
        cp "$ENV_FILE_ROOT" "$ENV_FILE_DOCKER"
    fi

    # Verify .env.prod exists in the compose folder
    if [ ! -f "$ENV_FILE_DOCKER" ]; then
        echo "❌ Erreur: Le fichier .env.prod n'a pas été trouvé dans _devops/docker/"
        echo "👉 Copiez .env.prod.example vers .env.prod puis placez-le à la racine du repo ou dans _devops/docker/"
        exit 1
    fi
else
    echo "🔧 Déploiement en DÉVELOPPEMENT"
fi

echo "📦 Pull des dernières modifications..."
CURRENT_BRANCH=$(git branch --show-current)
git pull origin $CURRENT_BRANCH

echo "🏗️  Build des images Docker..."
docker compose -f $COMPOSE_FILE build --no-cache

echo "🛑 Arrêt des anciens containers..."
docker compose -f $COMPOSE_FILE down

echo "🚀 Démarrage des nouveaux containers..."
docker compose -f $COMPOSE_FILE up -d

echo "⏳ Attente du démarrage des services..."
sleep 10

echo "🗄️  Application des migrations..."
docker compose -f $COMPOSE_FILE exec -T backend python manage.py migrate --noinput

echo "📦 Collecte des fichiers statiques..."
docker compose -f $COMPOSE_FILE exec -T backend python manage.py collectstatic --noinput

echo "🧹 Nettoyage des images Docker inutilisées..."
docker image prune -f

echo ""
echo "✅ Déploiement terminé avec succès!"
echo ""
echo "📊 Status des containers:"
docker compose -f $COMPOSE_FILE ps

echo ""
echo "📝 Pour voir les logs:"
echo "   docker compose -f $COMPOSE_FILE logs -f"
echo ""
echo "🌐 Pour créer un superuser:"
echo "   docker compose -f $COMPOSE_FILE exec backend python manage.py createsuperuser"
