#!/bin/bash

# Script de déploiement automatique pour InstantMusic
# Usage: ./deploy.sh [development|production]

set -e

ENV=${1:-production}
COMPOSE_FILE="_devops/docker/docker-compose.yml"

if [ "$ENV" = "production" ]; then
    COMPOSE_FILE="_devops/docker/docker-compose.prod.yml"
    ENV_FILE=".env.prod"

    echo "🚀 Déploiement en PRODUCTION"

    # Vérifier que le fichier .env.prod existe
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ Erreur: Le fichier $ENV_FILE n'existe pas!"
        echo "👉 Copiez .env.prod.example vers .env.prod et configurez les variables"
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
