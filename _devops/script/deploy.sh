#!/bin/bash

# Script de déploiement automatique pour InstantMusic
# Usage: ./deploy.sh [development|production]

set -e

ENV=${1:-production}
COMPOSE_FILE="_devops/docker/docker-compose.yml"
COMPOSE_EXTRA=""

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

    # Pass .env.prod as the env-file so Docker Compose can substitute ${VITE_API_URL}
    # and ${VITE_WS_URL} as build args for the frontend image
    COMPOSE_EXTRA="--env-file $ENV_FILE_DOCKER"
else
    echo "🔧 Déploiement en DÉVELOPPEMENT"
fi

echo "📦 Pull des dernières modifications..."
CURRENT_BRANCH=$(git branch --show-current)
git pull origin $CURRENT_BRANCH

echo "🏗️  Build des images Docker..."
docker compose -f $COMPOSE_FILE $COMPOSE_EXTRA build --no-cache --progress=auto

echo "🛑 Arrêt des anciens containers..."
docker compose -f $COMPOSE_FILE $COMPOSE_EXTRA down

echo "🚀 Démarrage des nouveaux containers..."
docker compose -f $COMPOSE_FILE $COMPOSE_EXTRA up -d

echo "⏳ Attente du démarrage des services..."
sleep 10

echo "🗄️  Application des migrations..."
docker compose -f $COMPOSE_FILE $COMPOSE_EXTRA exec -T backend python manage.py migrate --noinput

echo "📦 Collecte des fichiers statiques..."
docker compose -f $COMPOSE_FILE $COMPOSE_EXTRA exec -T backend python manage.py collectstatic --noinput

if [ "$ENV" = "production" ]; then
    echo "🔔 Initialisation des achievements (seed)..."
    docker compose -f $COMPOSE_FILE $COMPOSE_EXTRA exec -T backend python manage.py seed_achievements || true

    echo "🔁 Attribution rétroactive des achievements aux joueurs (peut prendre du temps)..."
    docker compose -f $COMPOSE_FILE $COMPOSE_EXTRA exec -T backend python manage.py award_retroactive_achievements || true

    echo "🔁 Mise à jour des statistiques joueurs"
    docker compose -f $COMPOSE_FILE $COMPOSE_EXTRA exec -T backend python manage.py recalculate_user_stats || true
fi

echo "🧹 Nettoyage des images Docker inutilisées..."
docker image prune -f

echo ""
echo "✅ Déploiement terminé avec succès!"
echo ""
echo "📊 Status des containers:"
docker compose -f $COMPOSE_FILE $COMPOSE_EXTRA ps

echo ""
echo "📝 Pour voir les logs:"
echo "   docker compose -f $COMPOSE_FILE logs -f"
echo ""
echo "🌐 Pour créer un superuser:"
echo "   docker compose -f $COMPOSE_FILE exec backend python manage.py createsuperuser"
