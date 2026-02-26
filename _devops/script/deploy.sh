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
#   --help         Affiche cette aide
#
# Exemples:
#   ./deploy.sh production
#   ./deploy.sh development --no-pull
#   ./deploy.sh production --status
#   ./deploy.sh production --logs backend
#   ./deploy.sh production --rollback

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
OPT_LOGS=false
OPT_LOGS_SVC=""

shift || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-pull)   OPT_NO_PULL=true ;;
        --no-cache)  OPT_NO_CACHE=true ;;
        --status)    OPT_STATUS=true ;;
        --rollback)  OPT_ROLLBACK=true ;;
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

DC="docker compose -f $COMPOSE_FILE $COMPOSE_EXTRA"

# ─── Vérification SSL (production uniquement) ─────────────────────────────────
if [[ "$ENV" == "production" ]]; then
    # Cherche les certs dans le volume Docker ou le dossier nginx/ssl/
    LETSENCRYPT_CERT_CHECK="$DEVOPS_DIR/nginx/ssl/live"
    CERT_MISSING=false

    # Vérification via docker volume (si le volume letsencrypt existe)
    if docker volume ls --format '{{.Name}}' 2>/dev/null | grep -q "instantmusic_letsencrypt"; then
        # Volume existe — vérifier qu'un cert y est présent
        CERT_FOUND=$(docker run --rm -v instantmusic_letsencrypt:/etc/letsencrypt:ro \
            alpine:3 ls /etc/letsencrypt/live/ 2>/dev/null | grep -v "README" | head -1)
        if [[ -z "$CERT_FOUND" ]]; then
            CERT_MISSING=true
        fi
    else
        CERT_MISSING=true
    fi

    if [[ "$CERT_MISSING" == "true" ]]; then
        echo ""
        echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║  ATTENTION : Aucun certificat SSL détecté                   ║${NC}"
        echo -e "${YELLOW}╠══════════════════════════════════════════════════════════════╣${NC}"
        echo -e "${YELLOW}║  nginx ne démarrera pas sans les certificats Let's Encrypt. ║${NC}"
        echo -e "${YELLOW}║                                                              ║${NC}"
        echo -e "${YELLOW}║  Obtenir le certificat avant de déployer :                  ║${NC}"
        echo -e "${YELLOW}║                                                              ║${NC}"
        echo -e "${YELLOW}║  make ssl-init DOMAIN=votre-domaine.com EMAIL=you@mail.com  ║${NC}"
        echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${YELLOW}Continuer quand même sans nginx ? (les autres services démarreront)${NC}"
        read -r -p "Continuer ? [y/N] " CONTINUE_WITHOUT_SSL
        if [[ "${CONTINUE_WITHOUT_SSL,,}" != "y" ]]; then
            exit 1
        fi
        log_warn "Déploiement sans nginx — lancez 'make ssl-init' puis 'make deploy-prod'."
    fi
fi

if [[ "$OPT_STATUS" == "true" ]]; then
    log_section "Etat des services"
    $DC ps
    echo ""
    log_section "Test de sante de l'API"
    BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
    if curl -sf "$BACKEND_URL/api/health/" >/dev/null 2>&1; then
        log_success "Backend repond sur $BACKEND_URL/api/health/"
    else
        log_warn "Backend inaccessible sur $BACKEND_URL/api/health/"
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
if [[ "$ENV" == "production" || "$OPT_NO_CACHE" == "true" ]]; then
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
