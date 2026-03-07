# Changelog

Toutes les modifications notables apportees a ce projet sont documentees dans ce fichier.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet respecte la [gestion semantique de version](https://semver.org/lang/fr/).

---

## [Non publie]

### Ajoute
- Documentation technique complete dans `docs/`

---

## [1.0.0] - 2026-03-01

Publication officielle de la version stable.

### Ajoute
- Mode de jeu **Karaoke** : paroles synchronisees avec la video YouTube
- Mode de jeu **Mollo** : lecture audio ralentie et pitch-shiftee
- **Systeme de boutique** complet avec 8 types de bonus (double_points, max_points, time_bonus, fifty_fifty, steal, shield, fog, joker)
- Integration **YouTube** pour les extraits video du mode Karaoke
- **Systeme d'amities** : inviter des amis, liste d'amis, statut en ligne
- **Systeme d'equipes** : creer et rejoindre des equipes, classement par equipe
- Application `shop` : gestion des bonus, historique d'achats, solde de coins
- Middleware de **maintenance** : bloquer l'acces au site via l'interface admin
- Pages legales : mentions legales, CGU, politique de confidentialite
- **Tracing distribue** avec Jaeger (OpenTelemetry)
- Support **SSL/TLS automatique** avec Let's Encrypt et Certbot
- Configuration monitoring complete : ELK Stack (Elasticsearch 8.13, Logstash, Kibana), Prometheus, Grafana 10.4.1, Node Exporter, Redis Exporter

### Modifie
- Architecture Celery : ajout de Celery Beat pour les taches planifiees
- Configuration Nginx production : rate limiting renforce, headers de securite CSP et HSTS
- Modele utilisateur : ajout des champs `coins`, `avatar`, `bio`, `equipe`
- Systeme de scoring : prise en compte des bonus actifs lors du calcul

### Securite
- Ajout des headers de securite HTTP dans Nginx (CSP, HSTS, X-Frame-Options)
- Rate limiting sur les routes API et WebSocket
- Validation renforcee des tokens JWT sur les connexions WebSocket
- Audit bandit passe sans erreurs critiques

---

## [0.9.0] - 2026-01-15

### Ajoute
- **Systeme de succès/badges** (`achievements`) : 20+ succes deblocables
  - Premier quiz gagne, serie de victoires, score parfait, etc.
  - Attribution automatique via tache Celery apres chaque partie
- **Statistiques joueurs** detaillees : taux de bonnes reponses, historique des parties, classement global
- Mode de jeu **Paroles** : systeme de texte a trou (fill-in-blank) synchronise avec les paroles
- **Notifications temps reel** via nouveau consumer WebSocket `/ws/notifications/`
  - Notification d'invitation a une partie
  - Notification de succes debloque
  - Notification de defi recu
- Tache RGPD : `rgpd.purge_expired_invitations` — suppression des invitations > 7 jours
- Tache RGPD : `rgpd.anonymize_old_game_data` — anonymisation des donnees > 365 jours
- Endpoint `/api/stats/leaderboard/` : classement global des joueurs
- Endpoint `/api/stats/me/` : statistiques personnelles du joueur connecte

### Modifie
- Refactorisation du `GameConsumer` : separation de la logique en services dedies
- Amelioration du calcul de score : prise en compte du temps de reponse (score decroissant)
- Format des messages WebSocket standardise avec champ `type` et `payload`

### Corrige
- Fuite de connexions WebSocket lors d'une deconnexion abrupte du client
- Race condition lors de la soumission simultanee de plusieurs reponses au meme round
- Erreur 500 lors de la creation d'une salle avec une playlist Deezer privee

---

## [0.8.0] - 2025-11-20

### Ajoute
- Mode de jeu **Generation** : deviner l'annee de sortie du morceau
- **Integration Deezer** complete : recherche de playlists, recuperation des extraits audio (30 secondes)
- **Gestion des playlists** : creer, modifier, supprimer des playlists personnalisees
- Ajout de morceaux depuis la recherche Deezer vers une playlist
- Mode **Rapide** : variante du mode Classique avec timer reduit (10 secondes)
- **Google OAuth 2.0** : connexion via compte Google
- Refresh token automatique JWT (rotation des tokens)
- Application `administration` avec panneau de controle admin Jazzmin
- Rate limiting WebSocket : fenetre glissante Lua (Redis)

### Modifie
- Remplacement de Django WSGI par **ASGI** (uvicorn) pour le support WebSocket
- Passage de Django Channels 3.x a 4.x
- Configuration Redis : separation des bases (cache=1, channels=2, celery=0)
- Refactorisation du systeme d'authentification : separation JWT / OAuth dans des serializers dedies

### Corrige
- Tokens JWT non invalides lors de la deconnexion (ajout d'une blacklist)
- Plantage du Celery worker si Redis est indisponible au demarrage
- Calcul errone des scores en cas de deconnexion/reconnexion en cours de partie

### Supprime
- Authentification par session Django (remplacee integralement par JWT)

---

## [0.7.0] - 2025-09-10

### Ajoute
- **Systeme de rooms** (salles de jeu) : creer une salle avec un code unique, inviter des joueurs
- **GameConsumer** WebSocket initial : gestion des connexions, join, start, answer
- Messages WebSocket : `player_join`, `start_game`, `player_answer` (client → serveur)
- Messages WebSocket : `start_round`, `end_round`, `next_round`, `finish_game` (serveur → client)
- Modeles Django : `Game`, `GameRound`, `GamePlayer`, `GameAnswer`
- Mode de jeu **Classique** : QCM 4 choix (titre ou artiste)
- **Celery** + Redis broker : tache `debug_task` de verification de connectivite
- Configuration **Docker Compose** developpement avec tous les services
- **Django Admin** avec interface Jazzmin
- Documentation API automatique avec `drf-spectacular` (Swagger + ReDoc)
- Health check endpoint : `GET /api/health/`

### Modifie
- Structure du projet reorganisee en applications Django modulaires (`apps/`)
- Split des settings Django par environnement (`base`, `development`, `production`)

---

## [0.6.0] - 2025-07-05

Initialisation du projet.

### Ajoute
- Structure initiale du projet (Django backend + React frontend)
- Application `users` : modele utilisateur custom (`AbstractUser`)
- Application `authentication` : JWT avec `djangorestframework-simplejwt`
  - Endpoints : `POST /api/auth/login/`, `POST /api/auth/register/`, `POST /api/auth/refresh/`
- Application `core` : endpoint de health check
- Configuration **PostgreSQL 15** en base de donnees principale
- Configuration **Redis** comme backend de cache
- Fichiers Docker : `Dockerfile` backend, `Dockerfile` frontend
- Premier squelette Docker Compose (`db`, `redis`, `backend`, `frontend`)
- **Makefile** avec commandes essentielles (deploy-dev, migrate, shell)
- Configuration **ruff** et **bandit** dans `pyproject.toml`
- Pipeline CI/CD GitHub Actions (lint + tests)
- Configuration **Nginx** de base comme reverse proxy
- Frontend React 18 + TypeScript + Vite + Tailwind CSS
- Routage React initial : page d'accueil, connexion, inscription
- Gestion des tokens JWT cote client (localStorage + intercepteur Axios)

---

[Non publie]: https://github.com/votre-org/instant-music/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/votre-org/instant-music/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/votre-org/instant-music/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/votre-org/instant-music/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/votre-org/instant-music/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/votre-org/instant-music/releases/tag/v0.6.0
