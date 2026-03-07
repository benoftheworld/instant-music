# Architecture — Nginx

> Ce document explique ce qu'est Nginx, son role dans InstantMusic, et comment il est configure.

---

## Sommaire

- [Qu'est-ce que Nginx ?](#quest-ce-que-nginx-)
- [Son role dans InstantMusic](#son-role-dans-instantmusic)
- [Schema du routage](#schema-du-routage)
- [Configuration des routes](#configuration-des-routes)
- [Gestion du WebSocket](#gestion-du-websocket)
- [SSL/TLS avec Let's Encrypt](#ssltls-avec-lets-encrypt)
- [Rate limiting](#rate-limiting)
- [Headers de securite](#headers-de-securite)
- [Difference dev vs prod](#difference-dev-vs-prod)

---

## Qu'est-ce que Nginx ?

Nginx (prononce "engine-x") est un **logiciel serveur web** tres populaire. Il peut jouer plusieurs roles :

- **Serveur web** : distribuer des fichiers HTML/CSS/JS directement aux navigateurs
- **Reverse proxy** : recevoir des requetes et les transmettre a un autre serveur
- **Load balancer** : repartir la charge entre plusieurs serveurs

Une analogie simple : Nginx est comme le **standard telephonique** d'une grande entreprise. Quand quelqu'un appelle le numero principal, le standard ecoute sa demande ("je veux le service comptabilite") et le redirige vers le bon poste sans que l'appelant sache combien de personnes travaillent dans l'entreprise ou quels sont leurs numeros directs.

### Pourquoi un "reverse proxy" ?

Dans une architecture classique sans proxy, le navigateur appelle directement le serveur backend :

```
Navigateur → Backend Django (port 8000)
Navigateur → Frontend Nginx (port 3000)
Navigateur → (doit connaitre tous les ports !)
```

Avec un reverse proxy Nginx :

```
Navigateur → Nginx (port 80/443 uniquement)
                │
                ├─ /api/   → Backend Django (port 8000, interne)
                ├─ /ws/    → Backend Django (port 8000, interne)
                └─ /       → Frontend (port 3000, interne)
```

Avantages :
- Un seul point d'entree pour l'utilisateur (un seul port, une seule URL)
- Les services internes ne sont pas exposes directement sur internet
- Nginx peut optimiser les connexions (compression, keep-alive, cache de fichiers statiques)
- SSL gere en un seul endroit

---

## Son role dans InstantMusic

Dans InstantMusic, Nginx remplit 4 fonctions :

1. **Routage** : analyser l'URL et envoyer la requete au bon service
2. **Proxy WebSocket** : etablir le "tunnel" pour les connexions temps reel
3. **SSL Termination** : dechiffrer le HTTPS entrant, communiquer en HTTP avec les services internes
4. **Securite** : rate limiting, headers de protection, filtrage

---

## Schema du routage

```
                           INTERNET
                               │
                    ┌──────────▼──────────┐
                    │                      │
                    │   NGINX :80 / :443   │
                    │                      │
                    │  Analyse l'URL :     │
                    │                      │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼──────────────────────┐
          │                    │                        │
          │                    │                        │
   /api/... ou          /ws/...               / (tout le reste)
   /admin/...                  │                        │
          │                    │                        │
          ▼                    ▼                        ▼
  ┌───────────────┐   ┌────────────────┐    ┌──────────────────┐
  │    BACKEND    │   │    BACKEND     │    │    FRONTEND      │
  │  Django DRF   │   │  Django Chann. │    │  React SPA       │
  │  :8000        │   │  :8000 (WS)   │    │  nginx:80        │
  │               │   │               │    │                  │
  │  Requetes     │   │  Connexions   │    │  Fichiers HTML   │
  │  REST/HTTP    │   │  persistantes │    │  CSS/JS statiq.  │
  └───────────────┘   └───────────────┘    └──────────────────┘


Routes supplementaires (prod) :
  /grafana/     → Grafana :3001 (monitoring)
  /prometheus/  → Prometheus :9090 (metriques)
```

---

## Configuration des routes

### Route `/` — Application React (SPA)

```nginx
location / {
    proxy_pass http://frontend:80;
    # ou en prod, servir les fichiers statiques directement :
    # root /usr/share/nginx/html;
    # try_files $uri $uri/ /index.html;  # Important pour React Router !
}
```

Le `try_files` est crucial pour les Single Page Applications (SPA). React Router gere la navigation cote client. Si quelqu'un acce a `https://instantmusic.fr/game/ABC123`, Nginx doit servir `index.html` (pas un fichier `game/ABC123.html` qui n'existe pas) pour que React prenne la main.

### Route `/api/` — API REST Django

```nginx
location /api/ {
    proxy_pass http://backend:8000;

    # Headers importants pour que Django sache l'IP reelle du client
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Timeout pour les longues requetes
    proxy_connect_timeout 60s;
    proxy_read_timeout 60s;
}
```

### Route `/ws/` — WebSocket

```nginx
location /ws/ {
    proxy_pass http://backend:8000;

    # Ces 3 lignes sont OBLIGATOIRES pour les WebSockets
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Timeout plus long : les WebSockets restent ouverts longtemps
    proxy_read_timeout 86400s;  # 24 heures
    proxy_send_timeout 86400s;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Route `/admin/` — Interface d'administration Django

```nginx
location /admin/ {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Acces restreint aux IPs autorisees (optionnel mais recommande)
    # allow 192.168.1.0/24;
    # deny all;
}
```

### Route `/grafana/` — Tableau de bord de monitoring

```nginx
location /grafana/ {
    proxy_pass http://grafana:3000/;
    proxy_set_header Host $host;
    # Rewrite pour enlever le prefixe /grafana/ dans les requetes internes
    rewrite ^/grafana/(.*) /$1 break;
}
```

### Route `/prometheus/` — Metriques Prometheus

```nginx
location /prometheus/ {
    proxy_pass http://prometheus:9090/prometheus/;
    # Acces restreint : Prometheus ne doit pas etre public
    # allow 10.0.0.0/8;
    # deny all;
}
```

---

## Gestion du WebSocket

### Pourquoi les WebSockets necessitent une configuration speciale ?

Par defaut, HTTP est un protocole "sans etat" : chaque requete est independante. Le WebSocket demande une connexion **persistante** entre le client et le serveur. Pour etablir cette connexion, le client envoie une requete HTTP speciale avec un header `Upgrade: websocket`.

Sans la configuration speciale, Nginx fermerait cette connexion comme n'importe quelle requete HTTP.

```
Client          Nginx           Backend
  │                │                │
  │ GET /ws/       │                │
  │ Upgrade: ws    │                │
  │─────────────→  │                │
  │                │ proxy_pass     │
  │                │ + Upgrade: ws  │
  │                │───────────────→│
  │                │                │
  │                │  101 Switching │
  │                │  Protocols     │
  │                │←───────────────│
  │ 101 OK         │                │
  │←────────────── │                │
  │                │                │
  │══════════════WebSocket tunnel══════════════│
  │   Messages bidirectionnels en temps reel   │
```

---

## SSL/TLS avec Let's Encrypt

### C'est quoi SSL/TLS ?

SSL/TLS est le protocole qui "chiffre" les communications entre le navigateur et le serveur. Sans lui, n'importe qui sur le meme reseau Wi-Fi pourrait lire les requetes.

En pratique : `http://` = non chiffre, `https://` = chiffre avec SSL/TLS.

### Let's Encrypt et Certbot

Let's Encrypt est une autorite de certification **gratuite** qui emet des certificats SSL. Certbot est l'outil qui automatise l'obtention et le renouvellement.

```
┌─────────────────────────────────────────────────────────────────────┐
│ PROCESSUS D'OBTENTION DU CERTIFICAT                                  │
│                                                                       │
│  1. Certbot dit a Let's Encrypt : "Je gere instantmusic.fr"         │
│                                                                       │
│  2. Let's Encrypt cree un challenge :                                │
│     "Prouve-le en servant ce fichier a cette URL :                   │
│      http://instantmusic.fr/.well-known/acme-challenge/TOKEN"        │
│                                                                       │
│  3. Nginx sert le fichier de challenge depuis le volume certbot     │
│     (configuration speciale pour /.well-known/acme-challenge/)      │
│                                                                       │
│  4. Let's Encrypt verifie → emit le certificat SSL                  │
│                                                                       │
│  5. Nginx est rechargee avec le nouveau certificat                   │
│                                                                       │
│  6. Certbot recommence automatiquement tous les 60 jours             │
│     (certificats valides 90 jours)                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Configuration Nginx pour SSL

```nginx
# Redirection HTTP → HTTPS
server {
    listen 80;
    server_name instantmusic.fr www.instantmusic.fr;

    # Pour le challenge Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Rediriger tout le reste vers HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# Serveur HTTPS principal
server {
    listen 443 ssl http2;
    server_name instantmusic.fr www.instantmusic.fr;

    ssl_certificate /etc/letsencrypt/live/instantmusic.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/instantmusic.fr/privkey.pem;

    # Configuration SSL moderne et securisee
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;

    # ... routes ci-dessus ...
}
```

---

## Rate limiting

### Pourquoi limiter le debit ?

Sans rate limiting, un attaquant pourrait envoyer des milliers de requetes par seconde pour :
- Saturer le serveur (DDoS)
- Tester des mots de passe en masse (brute force)
- Extraire des donnees en masse (scraping)

### Configuration

```nginx
# Definir les zones de limitation
# Zone API : 20 requetes/seconde par IP
http {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=20r/s;

    # Zone auth (login/register) : plus stricte
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;

    # Zone WebSocket
    limit_conn_zone $binary_remote_addr zone=ws_limit:10m;
}

# Application sur les routes
location /api/ {
    limit_req zone=api_limit burst=50 nodelay;
    limit_req_status 429;  # HTTP 429 Too Many Requests
    # ...
}

location /api/auth/ {
    limit_req zone=auth_limit burst=10;
    limit_req_status 429;
    # ...
}

location /ws/ {
    limit_conn ws_limit 10;  # Max 10 connexions WS simultanées par IP
    # ...
}
```

### Rate limiting WebSocket (Redis Lua)

En plus du rate limiting Nginx, le GameConsumer implemente un rate limiting applicatif via un script Lua executé dans Redis (sliding window). Cela permet de limiter le nombre de messages envoyés par un client sur la WebSocket, independamment de Nginx.

---

## Headers de securite

### A quoi servent ces headers ?

Les headers HTTP de securite sont des instructions envoyees par le serveur au navigateur pour lui dire comment se comporter. Ils protegent contre des attaques courantes.

```nginx
server {
    # Content Security Policy : autorise seulement les ressources de notre domaine
    add_header Content-Security-Policy
        "default-src 'self';
         script-src 'self' 'unsafe-inline';
         style-src 'self' 'unsafe-inline';
         img-src 'self' data: https:;
         media-src 'self' https://cdns-preview.dzcdn.net;  # Deezer previews
         connect-src 'self' wss://instantmusic.fr;
         frame-ancestors 'none';"
        always;

    # HSTS : force le HTTPS pour les 2 prochaines annees
    add_header Strict-Transport-Security
        "max-age=63072000; includeSubDomains; preload"
        always;

    # Interdit au navigateur d'afficher la page dans une iframe
    # (protection contre le clickjacking)
    add_header X-Frame-Options "DENY" always;

    # Empeche le navigateur de "deviner" le type MIME
    # (protection contre certaines attaques par injection)
    add_header X-Content-Type-Options "nosniff" always;

    # Referrer Policy : ne pas envoyer l'URL de la page precedente
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Permissions Policy : desactiver les APIs inutiles
    add_header Permissions-Policy
        "geolocation=(), microphone=(), camera=()"
        always;
}
```

| Header                           | Protection contre                                   |
| -------------------------------- | --------------------------------------------------- |
| Content-Security-Policy (CSP)    | Injection de scripts malveillants (XSS)             |
| Strict-Transport-Security (HSTS) | Attaques "man in the middle", downgrade vers HTTP   |
| X-Frame-Options                  | Clickjacking (pieger l'utilisateur dans une iframe) |
| X-Content-Type-Options           | MIME sniffing attacks                               |
| Referrer-Policy                  | Fuite d'informations dans l'en-tete Referer         |
| Permissions-Policy               | Acces non voulu a la camera, micro, GPS             |

---

## Difference dev vs prod

En **developpement**, Nginx n'est pas present. Le navigateur accede directement aux services par leurs ports :

```
http://localhost:3000  →  conteneur frontend (Vite dev server)
http://localhost:8000  →  conteneur backend (uvicorn)
```

Cette simplicite accelere le developpement : moins de configuration, rechargement plus rapide, logs plus clairs.

En **production**, Nginx est indispensable :

```
https://instantmusic.fr/         →  Nginx → frontend
https://instantmusic.fr/api/...  →  Nginx → backend
https://instantmusic.fr/ws/...   →  Nginx → backend (WebSocket)
```

| Aspect                   | Developpement        | Production                   |
| ------------------------ | -------------------- | ---------------------------- |
| Nginx present            | Non                  | Oui                          |
| HTTPS                    | Non (HTTP seulement) | Oui (Let's Encrypt)          |
| Rate limiting            | Non                  | Oui                          |
| Headers securite         | Non                  | Oui                          |
| Compression gzip         | Non                  | Oui                          |
| Cache fichiers statiques | Non                  | Oui (1 mois pour les assets) |
| Logs Nginx               | -                    | /var/log/nginx/              |
| Fichier de config        | -                    | `_devops/nginx/nginx.conf`   |
