# Architecture de Monitoring — InstantMusic

## Vue d'ensemble

La stack de monitoring d'InstantMusic est composée de plusieurs outils complémentaires couvrant trois besoins distincts :

| Besoin        | Outils                                        | Description                                     |
| ------------- | --------------------------------------------- | ----------------------------------------------- |
| **Métriques** | Prometheus + Grafana                          | Données numériques (requêtes/sec, latence, ...) |
| **Logs**      | ELK Stack (Elasticsearch + Logstash + Kibana) | Enregistrements des événements applicatifs      |
| **Tracing**   | Jaeger                                        | Suivi des requêtes à travers les services       |

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ARCHITECTURE DE MONITORING                              │
│                                                                                 │
│   APPLICATION                  COLLECTION              STOCKAGE     VISUALISATION│
│                                                                                 │
│   ┌──────────────┐  /metrics/  ┌──────────────┐       ┌─────────┐  ┌─────────┐│
│   │   Backend    │ ──────────► │  Prometheus  │ ─────► │ TSDB    │  │ Grafana ││
│   │   Django     │             │  (scraping)  │        │(interne)│  │ :3001   ││
│   └──────────────┘             └──────────────┘        └─────────┘  └─────────┘│
│                                                                                 │
│   ┌──────────────┐             ┌──────────────┐       ┌─────────────────────┐  │
│   │   Backend    │  JSON logs  │   Logstash   │ ─────► │   Elasticsearch    │  │
│   │   Django     │ ──────────► │  (pipeline)  │        │   (index logs)     │  │
│   └──────────────┘             └──────────────┘        └──────────┬──────────┘  │
│                                                                   │            │
│   ┌──────────────┐  /metrics/  ┌──────────────┐                   ▼            │
│   │    Redis     │ ──────────► │ Redis Export │          ┌─────────────────┐   │
│   └──────────────┘             └──────────────┘          │    Kibana       │   │
│                                                           │    :5601        │   │
│   ┌──────────────┐  /metrics/  ┌──────────────┐          └─────────────────┘   │
│   │   Système    │ ──────────► │ Node Export  │                                 │
│   │(CPU/RAM/...)  │            └──────────────┘                                 │
│                                                                                 │
│   ┌──────────────┐   traces    ┌──────────────┐          ┌─────────────────┐   │
│   │   Backend    │ ──────────► │    Jaeger    │ ─────►   │  Jaeger UI      │   │
│   └──────────────┘             └──────────────┘          │  :16686         │   │
│                                                           └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Composants de la stack

### Elasticsearch 8.13

**Qu'est-ce que c'est ?** Elasticsearch est un **moteur de recherche et d'analyse** distribué. Dans notre contexte, il sert de base de données pour stocker et indexer les logs applicatifs. Il permet de faire des recherches full-text très rapides sur des millions de lignes de logs.

```
Elasticsearch
├── Stockage des logs sous forme de documents JSON
├── Indexation automatique de tous les champs
├── Recherche full-text en millisecondes
└── Accessible via REST API (port 9200 en interne)
```

**Port** : 9200 (interne), 9300 (cluster)

### Logstash 8.13

**Qu'est-ce que c'est ?** Logstash est un **pipeline de traitement de données**. Il collecte les logs depuis diverses sources, les transforme (parsing, enrichissement) et les envoie vers Elasticsearch.

```
Logstash Pipeline
┌─────────────────────────────────────────────────────┐
│                                                     │
│  INPUT          FILTER           OUTPUT             │
│  ───────        ──────           ──────             │
│  Fichier JSON → Parsing      →  Elasticsearch       │
│  TCP/UDP      → Timestamp    →  (logs-YYYY.MM.DD)   │
│  Beats        → Enrichissement                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Port** : 5044 (Beats input), 9600 (API monitoring)

### Kibana 8.13

**Qu'est-ce que c'est ?** Kibana est l'**interface web** de visualisation d'Elasticsearch. Il permet de :
- Explorer les logs en temps réel
- Créer des dashboards de monitoring des logs
- Configurer des alertes sur des patterns de logs

**Port** : 5601 (accès direct en développement)

### Prometheus

**Qu'est-ce que c'est ?** Prometheus est un système de **surveillance et d'alerte** basé sur des métriques numériques (time series). Il collecte des métriques via un mécanisme de **scraping** (il "tire" les données depuis les applications à intervalles réguliers).

```
Prometheus scraping :

Backend Django          Prometheus
:8000/metrics/   ◄────  GET /metrics/   (toutes les 15s)
node-exporter    ◄────  GET /metrics/   (toutes les 15s)
redis-exporter   ◄────  GET /metrics/   (toutes les 15s)
```

**Port** : 9090 (UI web + API)

### Grafana 10.4.1

**Qu'est-ce que c'est ?** Grafana est l'outil de **création de dashboards** pour les métriques. Il se connecte à Prometheus comme source de données et permet de visualiser les métriques sous forme de graphiques, jauges, tableaux.

**Port** : 3001 (pour éviter le conflit avec le frontend sur 3000)

### Jaeger

**Qu'est-ce que c'est ?** Jaeger est un système de **tracing distribué**. Il permet de suivre le chemin complet d'une requête à travers tous les services (ex: une requête HTTP → Django → PostgreSQL → Redis), de mesurer le temps passé dans chaque composant, et d'identifier les goulots d'étranglement.

```
Requête utilisateur
        │
        ├─► Django View (50ms)
        │       ├─► PostgreSQL query (30ms)
        │       └─► Redis cache (2ms)
        │
        └─► Total : 82ms
```

**Ports** : 16686 (UI web), 14268 (réception traces HTTP), 6831 (UDP)

### Node Exporter

Exporte les **métriques système** du serveur hôte vers Prometheus : utilisation CPU, mémoire RAM, espace disque, I/O réseau.

**Port** : 9100

### Redis Exporter

Exporte les **métriques Redis** vers Prometheus : connexions actives, utilisation mémoire, hits/misses du cache, commandes par seconde.

**Port** : 9121

---

## Configuration Docker Compose

```yaml
# _devops/docker/docker-compose.monitoring.yml (structure)
services:

  # Bases de données de métriques
  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml

  # Bases de données de logs
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.13.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false  # Désactivé en dev

  logstash:
    image: docker.elastic.co/logstash/logstash:8.13.0
    volumes:
      - ./monitoring/logstash/pipeline:/usr/share/logstash/pipeline

  kibana:
    image: docker.elastic.co/kibana/kibana:8.13.0
    ports: ["5601:5601"]

  # Dashboards métriques
  grafana:
    image: grafana/grafana:10.4.1
    ports: ["3001:3000"]
    volumes:
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards

  # Tracing
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports: ["16686:16686"]

  # Exporteurs
  node-exporter:
    image: prom/node-exporter:latest
    ports: ["9100:9100"]

  redis-exporter:
    image: oliver006/redis_exporter:latest
    ports: ["9121:9121"]
    environment:
      - REDIS_ADDR=redis:6379
```

---

## Flux de données — Détail par type

### Flux des métriques (Prometheus)

```
1. Application Django génère des métriques via prometheus_client
   (Counter, Gauge, Histogram)

2. Exposition via endpoint : GET /api/metrics/
   → Retourne format text/plain (OpenMetrics)

# HELP instantmusic_games_active Parties actuellement en cours
# TYPE instantmusic_games_active gauge
instantmusic_games_active 5.0

# HELP instantmusic_http_requests_total Nombre de requêtes HTTP
# TYPE instantmusic_http_requests_total counter
instantmusic_http_requests_total{method="GET",endpoint="/api/games/",status_code="200"} 1547.0

3. Prometheus scrape toutes les 15s
   → stocke dans sa base time-series (TSDB)

4. Grafana requête Prometheus (PromQL)
   → affiche dans les dashboards
```

### Flux des logs (ELK)

```
1. Django émet des logs JSON via python-json-logger
   {
     "timestamp": "2026-03-07T10:30:00Z",
     "level": "INFO",
     "logger": "apps.games",
     "message": "Game AZERTY started",
     "game_id": 123,
     "player_count": 4
   }

2. Les logs sont écrits dans un fichier ou envoyés via socket
   → récupérés par Logstash

3. Logstash pipeline :
   - Parse le JSON
   - Ajoute des métadonnées (host, env)
   - Envoie vers Elasticsearch

4. Kibana
   → Index Pattern : instantmusic-logs-*
   → Discover : recherche full-text
   → Dashboard : graphiques d'erreurs
```

### Flux des traces (Jaeger)

```
1. Middleware Django (OpenTelemetry) instrumente automatiquement :
   - Chaque requête HTTP
   - Chaque requête SQL
   - Chaque appel Redis

2. Les spans (unités de trace) sont envoyés à Jaeger
   → POST http://jaeger:14268/api/traces

3. Jaeger UI :
   → Rechercher une trace par ID ou service
   → Voir le waterfall des spans
   → Identifier les requêtes lentes
```

---

## Accès aux interfaces de monitoring

En développement (après `make deploy-dev` + démarrage monitoring) :

| Service    | URL                    | Identifiants  |
| ---------- | ---------------------- | ------------- |
| Grafana    | http://localhost:3001  | admin / admin |
| Prometheus | http://localhost:9090  | —             |
| Kibana     | http://localhost:5601  | —             |
| Jaeger     | http://localhost:16686 | —             |

### Démarrer le monitoring

```bash
# Lancer uniquement le monitoring (en plus de l'environnement dev)
docker compose -f _devops/docker/docker-compose.monitoring.yml up -d

# Ou avec l'environnement dev complet
docker compose \
  -f _devops/docker/docker-compose.yml \
  -f _devops/docker/docker-compose.monitoring.yml \
  up -d
```

---

## Alertes recommandées

| Alerte             | Condition                        | Sévérité |
| ------------------ | -------------------------------- | -------- |
| Latence API élevée | p99 > 2s pendant 5 min           | Warning  |
| Taux d'erreur HTTP | Erreurs 5xx > 1%                 | Critical |
| Mémoire Redis      | Utilisation > 80%                | Warning  |
| CPU serveur        | Utilisation > 90% pendant 10 min | Critical |
| Elasticsearch disk | Espace disque < 20%              | Warning  |
| WebSocket drops    | Déconnexions WS > 10/min         | Warning  |
