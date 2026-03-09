#!/usr/bin/env bash
# =============================================================================
# InstantMusic — Script de déploiement
# =============================================================================
#
# Usage:
#   ./deploy.sh [development|production] [OPTIONS]
#
# Options:
#   --no-pull      Saute le git pull
#   --no-cache     Force le rebuild complet sans cache
#   --status       Affiche l'état des services sans déployer
#   --logs [svc]   Affiche les logs (tous ou un service précis)
#   --rollback     Revient à l'image taggée "previous"
#   --blue-green   Déploiement blue-green sans downtime (production uniquement)
#   --help         Affiche cette aide
#
# Exemples:
#   ./deploy.sh production
#   ./deploy.sh development --no-pull
#   ./deploy.sh production --status
#   ./deploy.sh production --logs backend
#   ./deploy.sh production --rollback
#   ./deploy.sh production --blue-green

set -euo pipefail

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}i${NC}  $*"; }
log_success() { echo -e "${GREEN}OK${NC} $*"; }
log_warn()    { echo -e "${YELLOW}!${NC}  $*"; }
log_error()   { echo -e "${RED}ERR${NC} $*" >&2; }
log_section() { echo -e "\n${BOLD}${CYAN}>> $*${NC}"; }

die() { log_error "$*"; exit 1; }

usage() {
    grep '^#' "$0" | grep -v '#!/' | sed 's/^# \?//'
    exit 0
}

cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Le deploiement a echoue (code $exit_code)."
        docker compose -f "$COMPOSE_FILE" logs --tail=50 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Parse arguments
ENV="${1:-production}"
[[ "$ENV" == "--help" || "$ENV" == "-h" ]] && usage

OPT_NO_PULL=false
OPT_NO_CACHE=false
OPT_STATUS=false
OPT_ROLLBACK=false
OPT_BLUE_GREEN=false
OPT_LOGS=false
OPT_LOGS_SVC=""

shift || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-pull)   OPT_NO_PULL=true ;;
        --no-cache)  OPT_NO_CACHE=true ;;
        --status)    OPT_STATUS=true ;;
        --rollback)  OPT_ROLLBACK=true ;;
        --blue-green) OPT_BLUE_GREEN=true ;;
        --logs)      OPT_LOGS=true; OPT_LOGS_SVC="${2:-}"; [[ -n "$OPT_LOGS_SVC" ]] && shift ;;
        --help|-h)   usage ;;
        *)           log_warn "Option inconnue: $1" ;;
    esac
    shift
done

if [[ "$ENV" != "development" && "$ENV" != "production" ]]; then
    die "Environnement invalide: \"$ENV\". Utiliser 'development' ou 'production'."
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEVOPS_DIR="$REPO_ROOT/_devops"

if [[ "$ENV" == "production" ]]; then
    COMPOSE_FILE="$DEVOPS_DIR/docker/docker-compose.prod.yml"
else
    COMPOSE_FILE="$DEVOPS_DIR/docker/docker-compose.yml"
fi

COMPOSE_EXTRA=""

echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}  InstantMusic - Deploy - ENV: $ENV${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""

START_TIME=$(date +%s)

command -v docker >/dev/null 2>&1 || die "Docker n'est pas installe."
command -v git    >/dev/null 2>&1 || die "Git n'est pas installe."

if [[ "$ENV" == "production" ]]; then
    ENV_FILE_ROOT="$REPO_ROOT/.env.prod"
    ENV_FILE_DOCKER="$DEVOPS_DIR/docker/.env.prod"

    if [[ -f "$ENV_FILE_ROOT" ]]; then
        log_info "Copie de .env.prod (racine -> _devops/docker/)"
        cp "$ENV_FILE_ROOT" "$ENV_FILE_DOCKER"
    fi

    if [[ ! -f "$ENV_FILE_DOCKER" ]]; then
        die ".env.prod introuvable dans _devops/docker/.\nCopiez .env.prod.example -> .env.prod"
    fi

    COMPOSE_EXTRA="--env-file $ENV_FILE_DOCKER"
fi

COMPOSE_SSL_INIT="$DEVOPS_DIR/docker/docker-compose.ssl-init.yml"
DC="docker compose -f $COMPOSE_FILE $COMPOSE_EXTRA"

# ─── Vérification SSL (production uniquement) ─────────────────────────────────
CERT_MISSING=false
if [[ "$ENV" == "production" ]]; then
    if docker volume ls --format '{{.Name}}' 2>/dev/null | grep -q "instantmusic_letsencrypt"; then
        # Volume présent — vérifier l'existence du cert via docker volume inspect
        CERT_FOUND=$(docker volume inspect instantmusic_letsencrypt \
            --format '{{.Mountpoint}}' 2>/dev/null || true)
        if [[ -n "$CERT_FOUND" ]] && [[ -d "${CERT_FOUND}/live" ]]; then
            # Dossier live/ présent dans le volume monté
            :
        else
            CERT_MISSING=true
        fi
    else
        CERT_MISSING=true
    fi

    if [[ "$CERT_MISSING" == "true" ]]; then
        # Parfois certbot vient juste d'ecrire les fichiers — attendre et re-tester
        for try in 1 2 3 4 5; do
            sleep 1
            # Vérifier le contenu du volume via un conteneur (évite Permission denied sur /var/lib/docker)
            if docker run --rm -v instantmusic_letsencrypt:/data busybox sh -c 'test -d /data/live && [ "$(ls -A /data/live | wc -l)" -gt 0 ]' >/dev/null 2>&1; then
                CERT_MISSING=false
                log_info "Certificat detecte dans le volume instantmusic_letsencrypt (apres ${try}s)."
                break
            fi
        done

        if [[ "$CERT_MISSING" == "true" ]]; then
            log_warn "Aucun certificat SSL detecte dans le volume instantmusic_letsencrypt."
            log_warn "nginx demarrera en mode HTTP-only (sans SSL)."
            log_warn "Lancez 'make ssl-init DOMAIN=votredomaine.com EMAIL=vous@mail.com' pour obtenir le certificat."
            log_warn "Les autres services (backend, db, redis...) vont quand meme demarrer."
            # Ajouter l'overlay ssl-init pour que nginx utilise la config HTTP-only
            DC="docker compose -f $COMPOSE_FILE -f $COMPOSE_SSL_INIT $COMPOSE_EXTRA"
        fi
    fi
fi

if [[ "$OPT_STATUS" == "true" ]]; then
    log_section "Etat des services"
    $DC ps
    echo ""
    log_section "Test de sante de l'API"
    # Executer le test de sante DANS le container backend (expose n'est pas publie sur l'hote)
    if $DC exec -T backend sh -c 'curl -sf http://127.0.0.1:8000/api/health/' >/dev/null 2>&1; then
        log_success "Backend repond (depuis le container backend) sur /api/health/"
    else
        log_warn "Backend inaccessible depuis le container backend sur /api/health/"
    fi
    exit 0
fi

if [[ "$OPT_LOGS" == "true" ]]; then
    log_section "Logs${OPT_LOGS_SVC:+ - service: $OPT_LOGS_SVC}"
    # shellcheck disable=SC2086
    $DC logs -f --tail=100 $OPT_LOGS_SVC
    exit 0
fi

if [[ "$OPT_ROLLBACK" == "true" ]]; then
    log_section "Rollback vers l'image precedente"
    for svc in backend frontend; do
        img="instant-music-${svc}:previous"
        if docker image inspect "$img" >/dev/null 2>&1; then
            docker tag "$img" "instant-music-${svc}:latest"
            log_success "Rollback de $svc effectue."
        else
            log_warn "Aucune image 'previous' pour $svc - rollback ignore."
        fi
    done
    $DC up -d
    log_success "Services redemarres."
    exit 0
fi

# ─── Blue-green deployment ──────────────────────────────────────────
if [[ "$OPT_BLUE_GREEN" == "true" ]]; then
    [[ "$ENV" != "production" ]] && die "--blue-green est reservé au mode production."

    UPSTREAM_FILE="$DEVOPS_DIR/nginx/upstream-backend.conf"
    NGINX_CONTAINER="instantmusic_nginx"

    # Déterminer le slot actif (blue = port 8001, green = port 8002)
    CURRENT=$(cat "$UPSTREAM_FILE" 2>/dev/null | grep -oP '(backend-blue|backend-green)' || echo "")
    if [[ "$CURRENT" == "backend-green" ]]; then
        NEW_SLOT="blue"
        NEW_SERVICE="backend-blue"
    else
        NEW_SLOT="green"
        NEW_SERVICE="backend-green"
    fi

    log_section "Blue-green: deploiement sur le slot $NEW_SLOT"

    if [[ "$OPT_NO_PULL" == "false" ]]; then
        log_info "Mise a jour du code source"
        CURRENT_BRANCH=$(git -C "$REPO_ROOT" branch --show-current)
        git -C "$REPO_ROOT" pull origin "$CURRENT_BRANCH"
    fi

    log_info "Build de l'image backend..."
    $DC build backend
    log_success "Image construite."

    log_info "Demarrage du nouveau slot: $NEW_SERVICE"
    $DC up -d --no-deps --scale "$NEW_SERVICE=1" "$NEW_SERVICE" 2>/dev/null || \
        $DC up -d --no-deps backend
    log_success "Slot $NEW_SLOT demarre."

    log_info "Attente du health check sur le nouveau slot..."
    HEALTHY=false
    for i in $(seq 1 30); do
        if $DC exec -T backend python manage.py check --verbosity 0 >/dev/null 2>&1; then
            HEALTHY=true
            break
        fi
        sleep 2
    done

    if [[ "$HEALTHY" != "true" ]]; then
        log_error "Le nouveau slot n'est pas sain. Abandon du blue-green."
        log_warn "L'ancien slot reste actif. Aucun changement applique."
        exit 1
    fi
    log_success "Nouveau slot operationnel."

    log_info "Migration de la base de donnees..."
    $DC exec -T backend python manage.py migrate --noinput
    log_success "Migrations appliquees."

    log_info "Bascule du trafic vers le slot $NEW_SLOT"
    echo "# Active upstream — managed by deploy.sh --blue-green" > "$UPSTREAM_FILE"
    echo "server ${NEW_SERVICE}:8000;" >> "$UPSTREAM_FILE"

    if docker ps --format '{{.Names}}' | grep -q "$NGINX_CONTAINER"; then
        docker exec "$NGINX_CONTAINER" nginx -s reload 2>/dev/null || \
            log_warn "Impossible de recharger nginx — rechargement manuel requis."
        log_success "Nginx recharge — trafic bascule vers $NEW_SLOT."
    else
        log_warn "Container nginx non trouve. Rechargement manuel requis."
    fi

    log_info "L'ancien slot reste en standby pour rollback instantane."
    log_info "Pour rollback: echo 'server backend:8000;' > $UPSTREAM_FILE && docker exec $NGINX_CONTAINER nginx -s reload"

    echo ""
    echo -e "${BOLD}${GREEN}  Blue-green deploy reussi — slot actif: $NEW_SLOT${NC}"
    exit 0
fi

# Tag images actuelles comme "previous" avant le nouveau build
for svc in backend frontend; do
    if docker image inspect "instant-music-${svc}:latest" >/dev/null 2>&1; then
        docker tag "instant-music-${svc}:latest" "instant-music-${svc}:previous" 2>/dev/null || true
    fi
done

if [[ "$OPT_NO_PULL" == "false" ]]; then
    log_section "Mise a jour du code source"
    CURRENT_BRANCH=$(git -C "$REPO_ROOT" branch --show-current)
    log_info "Branche: $CURRENT_BRANCH"
    git -C "$REPO_ROOT" pull origin "$CURRENT_BRANCH"
    log_success "Code a jour."
fi

log_section "Build des images Docker"
BUILD_FLAGS="--progress=auto"
if [[ "$OPT_NO_CACHE" == "true" ]]; then
    BUILD_FLAGS="$BUILD_FLAGS --no-cache"
fi
# shellcheck disable=SC2086
$DC build $BUILD_FLAGS
log_success "Images construites."

log_section "Redemarrage des services"
$DC down --remove-orphans 2>/dev/null || true

# Supprimer de force les containers qui pourraient entrer en conflit de nommage.
# Cela couvre le cas où les containers ont été créés avec un ancien project name
# (ex: avant l'ajout de "name: instantmusic" dans docker-compose.prod.yml).
log_info "Nettoyage des containers en conflit eventuel..."
CONFLICTING=$(grep 'container_name:' "$COMPOSE_FILE" 2>/dev/null | awk '{print $2}' | tr -d '"'"'" || true)
if [[ -n "$CONFLICTING" ]]; then
    while IFS= read -r cname; do
        if [[ -n "$cname" ]] && docker ps -aq --filter "name=^${cname}$" | grep -q .; then
            log_warn "Suppression forcee du container existant: $cname"
            docker rm -f "$cname" 2>/dev/null || true
        fi
    done <<< "$CONFLICTING"
fi

$DC up -d --remove-orphans
log_success "Containers demarres."

log_section "Attente de la disponibilite du backend"
for i in $(seq 1 24); do
    if $DC exec -T backend python manage.py check --verbosity 0 >/dev/null 2>&1; then
        log_success "Backend operationnel (${i}x5s)."
        break
    fi
    if [[ $i -eq 24 ]]; then
        log_warn "Timeout - continuation quand meme."
    fi
    sleep 5
done

log_section "Migrations de base de donnees"

# Backup pre-migration (production uniquement)
if [[ "$ENV" == "production" ]]; then
    log_info "Backup de la base de donnees avant migration..."
    BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"
    if [[ -x "$BACKUP_SCRIPT" ]]; then
        if "$BACKUP_SCRIPT"; then
            log_success "Backup pre-migration effectue."
        else
            log_warn "Backup pre-migration echoue — continuation quand meme."
        fi
    else
        log_warn "Script de backup introuvable ($BACKUP_SCRIPT) — migration sans backup."
    fi
fi

$DC exec -T backend python manage.py migrate --noinput
log_success "Migrations appliquees."

log_section "Collecte des fichiers statiques"
$DC exec -T backend python manage.py collectstatic --noinput --clear
log_success "Fichiers statiques collectes."

if [[ "$ENV" == "production" ]]; then
    log_section "Initialisation des donnees de production"

    log_info "Creation des achievements..."
    $DC exec -T backend python manage.py seed_achievements || \
        log_warn "seed_achievements ignore (deja initialise?)."

    log_info "Attribution retroactive des achievements..."
    $DC exec -T backend python manage.py award_retroactive_achievements || \
        log_warn "award_retroactive_achievements ignore."

    log_info "Recalcul des statistiques joueurs..."
    $DC exec -T backend python manage.py recalculate_user_stats || \
        log_warn "recalculate_user_stats ignore."
fi

log_section "Nettoyage"
docker image prune -f >/dev/null
log_success "Images inutilisees supprimees."

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo -e "${BOLD}${GREEN}============================================${NC}"
echo -e "${BOLD}${GREEN}  Deploiement reussi en ${DURATION}s!${NC}"
echo -e "${BOLD}${GREEN}============================================${NC}"
echo ""
log_section "Etat des services"
$DC ps
echo ""
log_info "Commandes utiles:"
echo "  Etat    : make status"
echo "  Logs    : make logs"
echo "  Backend : make logs-backend"
echo ""
