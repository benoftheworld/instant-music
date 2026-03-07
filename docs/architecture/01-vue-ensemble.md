# Architecture — Vue d'ensemble

> Ce document decrit l'architecture globale d'InstantMusic : les services qui la composent, comment ils communiquent, et pourquoi ces choix techniques ont ete faits.

---

## Sommaire

- [Vue generale](#vue-generale)
- [Schema de l'architecture complete](#schema-de-larchitecture-complete)
- [Role de chaque conteneur](#role-de-chaque-conteneur)
- [Flux de donnees principaux](#flux-de-donnees-principaux)
- [Choix techniques](#choix-techniques)
- [Environnement de developpement vs production](#environnement-de-developpement-vs-production)

---

## Vue generale

InstantMusic est construite autour d'une architecture **microservices legere** : au lieu d'avoir un seul programme qui fait tout, on a plusieurs services specialises qui tournent en parallele dans des conteneurs Docker.

Chaque service a une responsabilite unique et bien definie. Cette approche offre plusieurs avantages :
- On peut mettre a l'echelle independamment chaque service (ex : plus de workers Celery si besoin)
- Un service qui plante n'entraine pas toute l'application
- Chaque service peut utiliser la technologie la plus adaptee a son besoin

### Les grandes families de services

```
UTILISATEURS
    │
    ▼
COUCHE D'ACCES (Nginx)      ← Unique point d'entree
    │
    ├── INTERFACE (Frontend) ← Ce que l'utilisateur voit
    │
    ├── LOGIQUE METIER (Backend Django) ← Regles du jeu, API
    │       │
    │       ├── BASE DE DONNEES (PostgreSQL)  ← Persistance long terme
    │       ├── CACHE / TEMPS REEL (Redis)    ← Rapidite + WebSocket
    │       └── TACHES ASYNC (Celery)         ← Travail en arriere-plan
    │
    └── OBSERVATION (Monitoring)  ← Logs, metriques, tracing
```

---

## Schema de l'architecture complete

### Environnement de developpement

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  MACHINE DEVELOPPEUR                                 │
│                                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐     │
│  │                          RESEAU DOCKER (instant-music_default)               │     │
│  │                                                                               │     │
│  │  ┌───────────────────┐    ┌────────────────────────────────────────────┐     │     │
│  │  │   FRONTEND        │    │                 BACKEND                    │     │     │
│  │  │                   │    │                                            │     │     │
│  │  │  React 18 + Vite  │    │  Django 5.1 + DRF + Channels              │     │     │
│  │  │  TypeScript       │◄───┤  Uvicorn ASGI                             │     │     │
│  │  │                   │    │                                            │     │     │
│  │  │  Port expose :    │    │  Port expose :                            │     │     │
│  │  │  localhost:3000   │    │  localhost:8000                           │     │     │
│  │  └───────────────────┘    └──────────────┬─────────────────────────--┘     │     │
│  │                                           │                                  │     │
│  │                           ┌──────────────┤                                  │     │
│  │                           │              │                                  │     │
│  │                ┌──────────▼──────┐  ┌────▼──────────────────────────┐      │     │
│  │                │  POSTGRESQL 15  │  │         REDIS 7               │      │     │
│  │                │                 │  │                                │      │     │
│  │                │  Base de donnees│  │  DB 0 → Broker Celery         │      │     │
│  │                │  principale     │  │  DB 1 → Cache Django          │      │     │
│  │                │                 │  │  DB 2 → Channel Layer WS      │      │     │
│  │                │  Port expose :  │  │                                │      │     │
│  │                │  localhost:5433 │  │  Port expose :                 │      │     │
│  │                └─────────────────┘  │  localhost:6379               │      │     │
│  │                                     └────────────┬──────────────────┘      │     │
│  │                                                   │                          │     │
│  │                                     ┌─────────────┴──────────────┐          │     │
│  │                                     │                             │          │     │
│  │                          ┌──────────▼──────────┐  ┌─────────────▼─────┐    │     │
│  │                          │  CELERY WORKER       │  │  CELERY BEAT      │    │     │
│  │                          │                      │  │                   │    │     │
│  │                          │  Execute les taches  │  │  Planificateur    │    │     │
│  │                          │  asynchrones         │  │  (cron-like)      │    │     │
│  │                          │  - achievements      │  │  - RGPD purge     │    │     │
│  │                          │  - RGPD              │  │  - anonymisation  │    │     │
│  │                          └──────────────────────┘  └───────────────────┘   │     │
│  │                                                                               │     │
│  └───────────────────────────────────────────────────────────────────────────--┘     │
│                                                                                       │
└───────────────────────────────────────────────────────────────────────────────────---┘
```

### Environnement de production

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                    INTERNET                                       │
└──────────────────────────────┬───────────────────────────────────────────────────┘
                               │ HTTPS :443 / HTTP :80
                               ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      SERVEUR DE PRODUCTION (VPS / Cloud)                          │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                      NGINX (ports 80 + 443)                                │  │
│  │                   Reverse Proxy + SSL Termination                           │  │
│  │                                                                              │  │
│  │    /           → frontend:80                                                │  │
│  │    /api/       → backend:8000                                               │  │
│  │    /ws/        → backend:8000 (upgrade WebSocket)                          │  │
│  │    /admin/     → backend:8000                                               │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│         │                        │                         │                       │
│         ▼                        ▼                         │                       │
│  ┌──────────────┐    ┌─────────────────────────┐          │                       │
│  │  FRONTEND    │    │        BACKEND           │          │                       │
│  │              │    │                           │          │                       │
│  │  Nginx:alpine│    │  Gunicorn + Uvicorn       │          │                       │
│  │  (SPA React) │    │  Workers                 │          │                       │
│  │  port: 80    │    │  port: 8000              │          │                       │
│  └──────────────┘    └──────────┬──────────────┘          │                       │
│                                 │                           │                       │
│                    ┌────────────┘                           │                       │
│                    │                                        │                       │
│       ┌────────────▼───────┐    ┌──────────────────┐       │                       │
│       │    POSTGRESQL 15   │    │    REDIS 7        │       │                       │
│       │    (non expose)    │    │    (non expose)   │◄──────┘                       │
│       └────────────────────┘    └────────┬──────────┘                              │
│                                          │                                          │
│                           ┌──────────────┘                                         │
│                           │                                                         │
│              ┌────────────▼──────────┐    ┌──────────────────┐                    │
│              │   CELERY WORKER       │    │   CELERY BEAT    │                    │
│              └───────────────────────┘    └──────────────────┘                    │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                         CERTBOT (Let's Encrypt)                             │  │
│  │                    Renouvellement SSL automatique                            │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### Monitoring (optionnel)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             STACK DE MONITORING                                   │
│                                                                                   │
│  LOGS                              METRIQUES                  TRACING             │
│  ────                              ─────────                  ───────             │
│                                                                                   │
│  ┌──────────────────┐              ┌──────────────────┐      ┌──────────────┐    │
│  │  Elasticsearch   │              │   Prometheus     │      │   Jaeger     │    │
│  │  8.13            │              │   (:9090)        │      │   (:16686)   │    │
│  │  (:9200)         │              └────────┬─────────┘      └──────────────┘    │
│  └────────┬─────────┘                       │                                     │
│           │                      ┌──────────▼──────────┐                         │
│  ┌────────▼─────────┐            │   Grafana 10.4.1    │                         │
│  │  Kibana 8.13     │            │   (:3001)           │                         │
│  │  (:5601)         │            └──────────────────---┘                         │
│  └──────────────────┘                                                             │
│           ▲                               ▲                                        │
│  ┌────────┴─────────┐            ┌────────┴──────────┐                           │
│  │  Logstash 8.13   │            │  Node Exporter    │                           │
│  │  (pipeline logs) │            │  Redis Exporter   │                           │
│  └──────────────────┘            └───────────────────┘                           │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## Role de chaque conteneur

### `frontend` — Interface utilisateur

**Technologie :** React 18 + TypeScript + Vite
**Port dev :** 3000

C'est tout ce que l'utilisateur voit et avec quoi il interagit : les pages, les boutons, le lecteur audio, les questions de quiz, le tableau des scores en direct.

En developpement, Vite sert les fichiers avec rechargement a chaud (hot reload). En production, les fichiers sont compiles en HTML/CSS/JS statiques et servis par nginx.

### `backend` — Cerveau de l'application

**Technologie :** Django 5.1 + Django REST Framework + Django Channels
**Port dev :** 8000

Le backend gere deux types de communications :
- **Requetes HTTP** (via DRF) : inscription, connexion, recuperation des playlists, historique des scores...
- **WebSocket** (via Channels) : communication temps reel pendant le jeu

En developpement, c'est Uvicorn (serveur ASGI) qui execute le backend. En production, Gunicorn orchestre plusieurs workers Uvicorn pour supporter plus de connexions simultanees.

### `db` — Base de donnees

**Technologie :** PostgreSQL 15
**Port dev :** 5433 (5432 en interne Docker)

Stocke toutes les donnees persistantes : utilisateurs, parties, scores, succes, playlists... C'est la "memoire longue duree" de l'application. Les donnees survivent aux redemarrages.

### `redis` — Memoire rapide et messager

**Technologie :** Redis 7
**Port dev :** 6379

Redis joue trois roles simultanement dans ce projet :

1. **Cache** : stocker temporairement des donnees calculees pour repondre plus vite (ex : classement)
2. **Channel Layer** : transporter les messages WebSocket entre les joueurs (le "systeme nerveux" du temps reel)
3. **Broker Celery** : file d'attente des taches asynchrones

Plus de details dans [04 - Redis](./04-redis.md).

### `celery` — Travailleur de l'arriere-plan

**Technologie :** Celery 5 (worker)

Executes des taches qui prennent du temps sans bloquer le serveur web. Par exemple : verifier quels succes ont ete debloques apres une partie.

### `celery-beat` — Planificateur

**Technologie :** Celery Beat

Lance automatiquement certaines taches a des horaires definis, comme un `cron`. Par exemple : supprimer les invitations expirees tous les jours.

### `nginx` — Aiguilleur du trafic (prod uniquement)

**Technologie :** Nginx
**Ports prod :** 80 (HTTP) + 443 (HTTPS)

Point d'entree unique de l'application. Regarde l'URL de la requete et la redirige vers le bon service. Gere aussi le SSL/TLS.

### `certbot` — Gestionnaire SSL (prod uniquement)

**Technologie :** Certbot (Let's Encrypt)

Obtient et renouvelle automatiquement les certificats SSL gratuits. En production, c'est ce qui fait fonctionner le HTTPS.

---

## Flux de donnees principaux

### 1. Requete HTTP classique

Exemple : un joueur consulte son profil (`GET /api/users/me/`)

```
Navigateur
    │
    │ 1. GET /api/users/me/ (avec JWT dans l'en-tete Authorization)
    ▼
Nginx
    │
    │ 2. Route /api/ → backend:8000
    ▼
Backend Django (DRF)
    │
    │ 3. Verifie le JWT (valid ? expire ?)
    │ 4. Identifie l'utilisateur
    │
    ├─── 5. Verif cache Redis → pas de cache
    │
    ├─── 6. Requete SQL → PostgreSQL
    │           │
    │           │ 7. Retourne les donnees du profil
    │           ▼
    │    Mise en cache Redis (TTL 5 min)
    │
    │ 8. Serialise en JSON
    ▼
Nginx
    │
    │ 9. Retourne la reponse JSON
    ▼
Navigateur (React met a jour l'UI)
```

### 2. Connexion WebSocket pour un jeu

Exemple : un joueur rejoint une salle de quiz

```
Navigateur
    │
    │ 1. WS /ws/game/ABC123/?token=<jwt>
    ▼
Nginx
    │
    │ 2. Route /ws/ → backend:8000 (upgrade HTTP → WS)
    ▼
Backend Django Channels (GameConsumer)
    │
    │ 3. Verifie le JWT (depuis le query param)
    │ 4. Ajoute le channel au groupe Redis "game_ABC123"
    │
    │ 5. Envoie {type: "player_join", ...} a tous les membres du groupe
    ▼
Redis (Channel Layer)
    │
    │ 6. Distribue le message a tous les consumers connectes au groupe
    ▼
Backend Django Channels (tous les consumers du groupe)
    │
    │ 7. Chaque consumer envoie le message a son client via WS
    ▼
Navigateurs de tous les joueurs (mise a jour simultanee)
```

### 3. Tache asynchrone Celery

Exemple : attribution des succes apres une partie

```
Backend Django
    │
    │ 1. La partie se termine (finish_game)
    │ 2. Appel : achievements.check_and_award.delay(game_id)
    │    (non-bloquant : retourne immediatement)
    ▼
Redis (broker)
    │
    │ 3. Message place dans la file d'attente
    ▼
Celery Worker
    │
    │ 4. Recoit la tache depuis Redis
    │ 5. Calcule quels succes ont ete debloques
    │ 6. Ecrit dans PostgreSQL
    │ 7. Envoie une notification via WebSocket (optionnel)
    ▼
Resultat stocke dans Redis (result backend)
    │
    │ 8. (si besoin) le backend peut consulter le resultat
    ▼
Fin
```

---

## Choix techniques

### Pourquoi Django + Django Channels ?

Django est un framework Python mature avec un ecosysteme riche (ORM, admin, auth). Django Channels l'etend pour supporter les WebSockets, indispensables pour le temps reel sans polling.

L'alternative aurait ete Node.js (Express + Socket.io), mais Django offre un meilleur support natif des taches async avec Celery et une meilleure integration avec PostgreSQL.

### Pourquoi Redis pour le Channel Layer ?

Le channel layer est la colle entre les WebSocket consumers. Quand le joueur A envoie une reponse, Redis se charge de la distribuer instantanement a tous les autres joueurs de la salle.

On pourrait utiliser une autre solution (InMemory channel layer), mais Redis permet de scaler horizontalement : on peut avoir plusieurs instances du backend et elles partageront le meme channel layer.

### Pourquoi Celery ?

Les taches longues ou periodiques (calcul de succes, nettoyage RGPD) ne doivent pas bloquer le serveur web. Si la verification des succes prenait 2 secondes et bloquait la reponse HTTP, l'experience serait degradee. Celery permet d'executer ces taches en arriere-plan, dans un process separe.

### Pourquoi PostgreSQL ?

Base de donnees relationnelle robuste, open-source, excellente avec Django (migrations, ORM). Les donnees du jeu (parties, scores, utilisateurs) ont des relations claires entre elles, ce qui correspond bien au modele relationnel.

### Pourquoi Nginx ?

Nginx est un serveur web/proxy tres performant. Il sert de "portier" : il recoit toutes les requetes et les redirige vers le bon service. Sans Nginx, il faudrait exposer tous les services directement sur internet, ce qui est un risque de securite. Nginx gere aussi le SSL, la compression, et le rate limiting.

---

## Environnement de developpement vs production

| Aspect          | Developpement                              | Production                                    |
| --------------- | ------------------------------------------ | --------------------------------------------- |
| Serveur ASGI    | Uvicorn (1 worker, rechargement auto)      | Gunicorn + N workers Uvicorn                  |
| Frontend        | Vite dev server (HMR)                      | Nginx servant des fichiers statiques compiles |
| Nginx           | Absent (acces direct aux ports)            | Present (reverse proxy + SSL)                 |
| SSL             | HTTP uniquement                            | HTTPS avec Let's Encrypt                      |
| PostgreSQL port | 5433 (expose sur l'hote)                   | Non expose (interne Docker)                   |
| Redis port      | 6379 (expose sur l'hote)                   | Non expose (interne Docker)                   |
| Debug           | `DEBUG=True`                               | `DEBUG=False`                                 |
| Volumes         | Montes depuis le code source (live reload) | Images Docker buildees                        |
| Logs            | Console (stdout)                           | Fichiers + Logstash → Elasticsearch           |
| Monitoring      | Optionnel                                  | Recommande                                    |
