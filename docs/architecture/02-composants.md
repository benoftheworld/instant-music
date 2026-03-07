# Architecture — Interactions entre composants

> Ce document explique comment les differents services d'InstantMusic communiquent entre eux, par quel reseau, et avec quels protocoles.

---

## Sommaire

- [Le reseau Docker](#le-reseau-docker)
- [Schema des dependances](#schema-des-dependances)
- [Flux d'une requete HTTP](#flux-dune-requete-http)
- [Flux d'une connexion WebSocket](#flux-dune-connexion-websocket)
- [Flux d'une tache Celery](#flux-dune-tache-celery)
- [Matrice de communication](#matrice-de-communication)

---

## Le reseau Docker

### Comment Docker isole les services

Quand vous lancez `make deploy-dev`, Docker Compose cree un reseau virtuel prive (`instant-music_default`). Tous les conteneurs sont dans ce reseau et peuvent se parler en utilisant leur **nom de service** comme adresse.

C'est comme un intranet d'entreprise ou chaque employe a son nom (le nom du service) et son poste de travail (le conteneur).

```
┌────────────────────────────────────────────────────────────────────────┐
│                   RESEAU DOCKER (instant-music_default)                 │
│                                                                          │
│   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌─────────────────┐  │
│   │ frontend  │   │  backend  │   │    db     │   │     redis       │  │
│   │           │   │           │   │           │   │                 │  │
│   │ :3000     │   │  :8000    │   │  :5432    │   │  :6379          │  │
│   └───────────┘   └───────────┘   └───────────┘   └─────────────────┘  │
│                                                                          │
│   ┌───────────────┐   ┌────────────────┐                                │
│   │    celery     │   │  celery-beat   │                                │
│   │               │   │                │                                │
│   │  (pas de port)│   │  (pas de port) │                                │
│   └───────────────┘   └────────────────┘                                │
│                                                                          │
│  Communication interne : http://backend:8000, postgresql://db:5432/...  │
└──────────────────────────────────────────────────────────────────────---┘

Ports exposes vers l'hote (machine developpeur) :
  localhost:3000  →  frontend:3000
  localhost:8000  →  backend:8000
  localhost:5433  →  db:5432
  localhost:6379  →  redis:6379
```

> Note : les ports internes Docker (5432 pour PostgreSQL) different parfois des ports exposes sur l'hote (5433). C'est pour eviter les conflits si vous avez deja une instance locale de PostgreSQL.

### Isolation des ports en production

En production, seul Nginx expose des ports vers l'exterieur (80 et 443). Tous les autres services (backend, db, redis...) sont uniquement accessibles depuis l'interieur du reseau Docker. C'est une mesure de securite importante.

```
INTERNET
    │
    │ :80 / :443 seulement
    ▼
┌───────────────────────────────────────────────────────┐
│                   NGINX                                │
│                                                        │
│  Acces a l'interieur du reseau Docker :               │
│  http://frontend:80                                   │
│  http://backend:8000                                  │
└────────────────────────────────────────────────────---┘
    │ (reseau Docker prive — pas accessible depuis internet)
    ▼
┌──────────────────────────────────────────────┐
│  backend, frontend, db, redis, celery, beat  │
└──────────────────────────────────────────────┘
```

---

## Schema des dependances

Ce schema montre qui depend de qui. Une fleche `A → B` signifie "A a besoin que B soit demarré pour fonctionner".

```
                              ┌───────────────┐
                              │   POSTGRESQL  │
                              │   (db)        │
                              └───────┬───────┘
                                      │ depende par
                                      │
              ┌───────────────────────┼────────────────────────┐
              │                       │                         │
              ▼                       ▼                         ▼
     ┌────────────────┐      ┌────────────────┐      ┌────────────────┐
     │    BACKEND     │      │    CELERY      │      │  CELERY-BEAT   │
     │    (backend)   │      │    (worker)    │      │  (beat)        │
     └────────┬───────┘      └────────┬───────┘      └────────┬───────┘
              │                       │                         │
              │ depende par           │ depende par             │ depende par
              │                       │                         │
              └───────────────────────┼─────────────────────────┘
                                      │
                               ┌──────▼───────┐
                               │     REDIS    │
                               │    (redis)   │
                               └──────────────┘

     ┌────────────────┐
     │    FRONTEND    │   ← depend uniquement du backend (appels API)
     │    (frontend)  │     mais pas au niveau Docker (demarrage independant)
     └────────────────┘
```

**Consequence pratique :** `make deploy-dev` demarre les services dans le bon ordre grace aux `depends_on` du Docker Compose. Redis et PostgreSQL demarrent en premier, puis le backend, puis les workers Celery.

---

## Flux d'une requete HTTP

### Exemple : connexion d'un joueur (`POST /api/auth/login/`)

Ce flux montre le chemin complet d'une requete HTTP, de l'envoi par le navigateur jusqu'a la reponse.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 1 : Le navigateur envoie la requete                                       │
│                                                                                  │
│  POST http://localhost:8000/api/auth/login/                                     │
│  Body: { "username": "alice", "password": "secret" }                           │
│                                                                                  │
│  En prod : POST https://instantmusic.fr/api/auth/login/                        │
│            → Nginx recoit en HTTPS, dechiffre SSL, passe au backend en HTTP    │
└───────────────────────────────────────────────────────────────────────────────-┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 2 : Nginx route la requete (prod uniquement)                              │
│                                                                                  │
│  Nginx voit : /api/   →  proxy_pass http://backend:8000                        │
│  Ajoute des en-tetes : X-Real-IP, X-Forwarded-For, X-Forwarded-Proto          │
└───────────────────────────────────────────────────────────────────────────────-┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 3 : Django recoit la requete                                               │
│                                                                                  │
│  URLs → config/urls.py → /api/auth/ → apps/authentication/urls.py              │
│  View : LoginView (DRF APIView)                                                 │
└───────────────────────────────────────────────────────────────────────────────-┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 4 : Traitement par le backend                                              │
│                                                                                  │
│  a) Deserialisation du JSON (LoginSerializer)                                   │
│  b) Validation des donnees (username non vide, password non vide...)            │
│  c) Authentification : SELECT * FROM users WHERE username='alice'               │
│     → Requete vers PostgreSQL                                                   │
│  d) Verification du mot de passe (bcrypt)                                       │
│  e) Generation des tokens JWT (access + refresh)                                │
└───────────────────────────────────────────────────────────────────────────────-┘
              │                               │
              ▼                               ▼
┌──────────────────────┐         ┌───────────────────────┐
│   POSTGRESQL         │         │   REDIS (cache)        │
│                       │         │                        │
│  Lecture utilisateur  │         │  Stockage du token     │
│  depuis la table      │         │  en liste noire        │
│  auth_user            │         │  (si logout precedent) │
└──────────────────────┘         └───────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 5 : Reponse JSON                                                           │
│                                                                                  │
│  HTTP 200 OK                                                                    │
│  {                                                                              │
│    "access": "eyJhbGciOiJIUzI1NiJ9...",                                        │
│    "refresh": "eyJhbGciOiJIUzI1NiJ9..."                                        │
│  }                                                                              │
└───────────────────────────────────────────────────────────────────────────────-┘
                              │
                              ▼
              React stocke le token et redirige vers /dashboard
```

---

## Flux d'une connexion WebSocket

### Exemple : un joueur rejoint une salle (`/ws/game/ABC123/`)

Les WebSockets etablissent une connexion persistante entre le navigateur et le serveur. C'est different des requetes HTTP qui sont "une requete, une reponse, terminee".

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 1 : Ouverture de la connexion WebSocket                                    │
│                                                                                   │
│  Le navigateur envoie une requete HTTP speciale "Upgrade" :                      │
│  GET ws://localhost:8000/ws/game/ABC123/?token=eyJhbGciOiJIUzI1NiJ9...         │
│  Headers : Upgrade: websocket, Connection: Upgrade                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 2 : Nginx upgarde la connexion (prod)                                      │
│                                                                                   │
│  Nginx detecte les headers WebSocket et passe en mode "tunnel" :                 │
│  proxy_http_version 1.1;                                                         │
│  proxy_set_header Upgrade $http_upgrade;                                         │
│  proxy_set_header Connection "upgrade";                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 3 : ASGI et Django Channels routing                                        │
│                                                                                   │
│  config/asgi.py → routing.py → GameConsumer                                     │
│  GameConsumer.connect() est appele                                               │
│                                                                                   │
│  a) Extraction du token depuis le query param                                    │
│  b) Validation JWT → identification de l'utilisateur                             │
│  c) Verification que la salle ABC123 existe                                      │
│  d) Verification que le joueur a le droit de rejoindre                           │
└─────────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 4 : Ajout au groupe Redis                                                   │
│                                                                                   │
│  self.channel_layer.group_add("game_ABC123", self.channel_name)                  │
│                                                                                   │
│  Redis stocke la correspondance :                                                 │
│  groupe "game_ABC123" → [channel_alice, channel_bob, channel_charlie]           │
└─────────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 5 : Broadcast de l'evenement "joueur rejoint"                              │
│                                                                                   │
│  channel_layer.group_send("game_ABC123", {                                       │
│    "type": "player_join",                                                        │
│    "payload": { "username": "alice", "players": [...] }                          │
│  })                                                                              │
│                                                                                   │
│  Redis distribue ce message a TOUS les consumers du groupe                       │
│  → Les navigateurs de Bob et Charlie recoivent la mise a jour                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 6 : La connexion reste ouverte                                              │
│                                                                                   │
│  La connexion WebSocket est maintenant etablie. Elle restera ouverte jusqu'a    │
│  ce que le joueur quitte la partie ou ferme son navigateur.                      │
│                                                                                   │
│  Pendant toute la partie, les messages circulent en temps reel via cette         │
│  connexion persistante sans re-etablir de connexion a chaque fois.               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Flux d'une tache Celery

### Exemple : attribution des succes apres une partie

Ce flux montre comment une operation lourde est delegue a un worker sans bloquer le serveur web.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 1 : Declenchement depuis le backend (non-bloquant)                          │
│                                                                                    │
│  # Dans GameConsumer.finish_game() :                                              │
│  from apps.achievements.tasks import check_and_award                              │
│  check_and_award.delay(game_id=42)   # .delay() = asynchrone, retourne tout de   │
│                                       # suite sans attendre le resultat           │
└──────────────────────────────────────────────────────────────────────────────────┘
                                │
                                │ Serialise le message JSON et l'envoie a Redis
                                ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 2 : Message dans la file Redis                                               │
│                                                                                    │
│  Redis DB 0 (broker Celery)                                                       │
│  File "celery" :                                                                  │
│  [                                                                                 │
│    {                                                                               │
│      "task": "achievements.check_and_award",                                      │
│      "args": [],                                                                   │
│      "kwargs": {"game_id": 42},                                                   │
│      "id": "d3b07384-..."                                                         │
│    }                                                                               │
│  ]                                                                                 │
│                                                                                    │
│  Le serveur web a deja rendu la reponse a l'utilisateur et est libre de          │
│  traiter d'autres requetes. La tache attend son tour dans la file.               │
└──────────────────────────────────────────────────────────────────────────────────┘
                                │
                                │ Le worker surveille la file en continu
                                ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 3 : Execution par le Celery Worker                                           │
│                                                                                    │
│  Le worker depile la tache et l'execute :                                         │
│                                                                                    │
│  def check_and_award(game_id):                                                    │
│    game = Game.objects.get(id=game_id)                                            │
│    for player in game.players.all():                                              │
│      # Calcule le score, nombre de bonnes reponses, etc.                          │
│      # Verifie chaque critere de succes                                           │
│      # Cree des enregistrements Achievement si conditions remplies               │
│      # Ecrit dans PostgreSQL                                                      │
└──────────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ ETAPE 4 : Resultat stocke et notification                                          │
│                                                                                    │
│  Le resultat est stocke dans Redis (result backend)                               │
│                                                                                    │
│  Optionnellement : le worker peut envoyer une notification WebSocket              │
│  aux joueurs concernes via le channel layer Redis                                 │
│  → "Felicitations ! Vous avez debloque le succes 'Premiere victoire' !"          │
└──────────────────────────────────────────────────────────────────────────────────┘

CHRONOLOGIE :

  t=0ms   GameConsumer envoie finish_game aux clients
  t=1ms   Tache placee dans Redis
  t=2ms   GameConsumer a fini, libre pour d'autres connexions
  t=150ms Celery Worker traite la tache
  t=300ms Succes ecrits en base
  t=301ms Notification WS envoyee aux joueurs
```

---

## Matrice de communication

Ce tableau recapitule qui communique avec qui, et comment.

| De          | Vers     | Protocole        | Port interne | Description                            |
| ----------- | -------- | ---------------- | ------------ | -------------------------------------- |
| Nginx       | frontend | HTTP             | 80 / 3000    | Servir l'application React             |
| Nginx       | backend  | HTTP / WS        | 8000         | Proxy API et WebSocket                 |
| frontend    | backend  | HTTP (Axios)     | 8000         | Appels API REST                        |
| frontend    | backend  | WebSocket (WS)   | 8000         | Temps reel jeu et notifications        |
| backend     | db       | TCP (PostgreSQL) | 5432         | Lecture/ecriture donnees               |
| backend     | redis    | TCP (Redis)      | 6379         | Cache, channel layer, broker           |
| celery      | db       | TCP (PostgreSQL) | 5432         | Ecriture des succes, anonymisation     |
| celery      | redis    | TCP (Redis)      | 6379         | Consommer les taches, ecrire resultats |
| celery-beat | redis    | TCP (Redis)      | 6379         | Planifier les taches periodiques       |
| celery      | redis    | TCP (Redis)      | 6379         | Envoyer des notifications WS           |

### Sens des dependances au demarrage

```
redis
  ├── backend (attend redis)
  ├── celery  (attend redis + db)
  └── celery-beat (attend redis + celery)

db
  ├── backend (attend db)
  └── celery  (attend db)

backend
  └── (rien n'attend backend au demarrage Docker)

frontend
  └── (rien n'attend frontend au demarrage Docker)
```
