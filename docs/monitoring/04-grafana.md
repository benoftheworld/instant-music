# Grafana — Dashboards et Alertes

## Introduction à Grafana

### Qu'est-ce que c'est ?

Grafana est une **plateforme open source de visualisation et d'observabilité**. C'est l'outil qui transforme les données brutes de Prometheus (métriques) ou d'Elasticsearch (logs) en **dashboards visuels** compréhensibles.

```
Prometheus     ──┐
                 ├──► Grafana ──► Dashboards visuels
Elasticsearch  ──┘
```

**Grafana ne stocke pas de données** : il se connecte à des sources de données (Prometheus, Elasticsearch, PostgreSQL, etc.) et affiche ce qu'il y trouve.

### Accès

- URL : `http://localhost:3001` (développement)
- Identifiants par défaut : `admin` / `admin`
- Port 3001 (pour éviter le conflit avec le frontend React sur 3000)

---

## Sources de données (Datasources)

Les datasources sont les connexions de Grafana vers les systèmes de données. Elles sont **provisionnées automatiquement** via des fichiers YAML.

### Configuration automatique (provisioning)

```yaml
# _devops/monitoring/grafana/provisioning/datasources/datasources.yml

apiVersion: 1

datasources:

  # Source 1 : Prometheus (métriques)
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  # Source 2 : Elasticsearch (logs)
  - name: Elasticsearch
    type: elasticsearch
    access: proxy
    url: http://elasticsearch:9200
    database: "instantmusic-logs-*"  # Pattern d'index
    jsonData:
      timeField: "@timestamp"
      esVersion: "8.13.0"
    editable: false
```

---

## Dashboards provisionnés

Deux dashboards sont provisionnés automatiquement au démarrage de Grafana.

### Dashboard 1 — `application-overview.json`

Vue d'ensemble de l'application InstantMusic. Ce dashboard est le **premier à consulter** pour avoir une image globale de la santé de l'application.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  InstantMusic — Application Overview                    Last 1h  Auto  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │   Req/sec    │ │  Latence p95 │ │   Taux erreur│ │ Parties act. │  │
│  │    42.3      │ │    145ms     │ │    0.2%      │ │     8        │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Requêtes HTTP par seconde (stacked par endpoint)                │  │
│  │                                                                  │  │
│  │  50 ┤          ░░                                                │  │
│  │  40 ┤       ░░░░░░░░░░░░                                         │  │
│  │  30 ┤    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                                     │  │
│  │  20 ┤ ████████████████████████████████████                       │  │
│  │  10 ┤─────────────────────────────────────────────────           │  │
│  │     └─────────────────────────────────────────────►  temps       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────┐ ┌────────────────────────────┐   │
│  │  Latence par percentile         │ │  WebSocket connexions act. │   │
│  │  p50 ─────────────── 45ms       │ │         ██████             │   │
│  │  p95 ─────────────── 145ms      │ │     ████████████           │   │
│  │  p99 ─────────────── 380ms      │ │ ████████████████████       │   │
│  └─────────────────────────────────┘ └────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Réponses aux questions — Taux de réussite par mode              │  │
│  │  Classique  ████████████████████████████░░  82%                  │  │
│  │  Rapide     ████████████████████░░░░░░░░░░  61%                  │  │
│  │  Génération █████████████████████████░░░░░  75%                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

**Panels du dashboard Application Overview** :

| Panel            | Type        | Métrique PromQL                                   | Description               |
| ---------------- | ----------- | ------------------------------------------------- | ------------------------- |
| Requêtes/sec     | Stat        | `sum(rate(instantmusic_http_requests_total[1m]))` | RPS global                |
| Latence p95      | Stat        | `histogram_quantile(0.95, ...)`                   | Latence 95e percentile    |
| Taux d'erreur    | Stat        | `rate(5xx) / rate(all)`                           | % erreurs HTTP            |
| Parties actives  | Stat        | `instantmusic_games_active`                       | Parties en cours          |
| RPS par endpoint | Time series | `sum by (endpoint) (rate(...))`                   | Évolution par endpoint    |
| Heatmap latence  | Heatmap     | `instantmusic_http_request_duration_seconds`      | Distribution des latences |
| WS connexions    | Time series | `instantmusic_ws_connections_active`              | Évolution connexions WS   |
| Taux de réussite | Bar chart   | `answers_total by mode`                           | Précision par mode de jeu |
| Erreurs Celery   | Time series | `celery_tasks_total{status="failure"}`            | Échecs tâches async       |
| API Deezer santé | Stat        | `external_api_errors / external_api_requests`     | Santé API Deezer          |

### Dashboard 2 — `system-overview.json`

Vue d'ensemble de l'infrastructure (métriques système via Node Exporter).

```
┌─────────────────────────────────────────────────────────────────────────┐
│  InstantMusic — System Overview                         Last 1h  Auto  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │   CPU Usage  │ │  RAM Usage   │ │  Disk Usage  │ │  Redis Mem.  │  │
│  │    23%       │ │  2.1 GB/8GB  │ │  45%         │ │  234 MB      │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  CPU utilisation (toutes les cores)                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────┐  ┌──────────────────────────────────┐ │
│  │  RAM : utilisée vs dispo    │  │  Redis : mémoire et connexions   │ │
│  └─────────────────────────────┘  └──────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Réseau : octets entrants/sortants                               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

**Panels du dashboard System Overview** :

| Panel          | Métrique                                                                         | Description           |
| -------------- | -------------------------------------------------------------------------------- | --------------------- |
| CPU usage      | `100 - (avg by(instance)(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` | Utilisation CPU       |
| RAM usage      | `node_memory_MemUsed_bytes / node_memory_MemTotal_bytes * 100`                   | RAM utilisée          |
| Disk usage     | `(1 - node_filesystem_free_bytes / node_filesystem_size_bytes) * 100`            | Espace disque         |
| Load average   | `node_load1`                                                                     | Charge système (1min) |
| Redis mémoire  | `redis_memory_used_bytes`                                                        | RAM Redis             |
| Redis hit rate | `redis_keyspace_hits / (redis_keyspace_hits + redis_keyspace_misses)`            | Hit/miss ratio        |
| DB connexions  | `pg_stat_activity_count`                                                         | Connexions PostgreSQL |

---

## Créer un nouveau Dashboard

### Étapes de base

```
1. Aller dans → Dashboards → New Dashboard
2. Cliquer "Add visualization"
3. Choisir la datasource (Prometheus ou Elasticsearch)
4. Configurer la requête
5. Choisir le type de visualisation
6. Configurer l'affichage
7. Sauvegarder
```

### Exemple : Créer un panel "Parties créées par mode"

```
1. Datasource : Prometheus

2. Requête PromQL :
   sum by (mode) (increase(instantmusic_games_created_total[24h]))

3. Type de visualisation : Bar chart

4. Configuration :
   - Title: "Parties créées par mode (24h)"
   - Legend: visible, en bas
   - Axes: Y label "Nombre de parties"

5. Résultat :
   ┌──────────────────────────────────────────────────────┐
   │  Parties créées par mode (24h)                       │
   │                                                      │
   │  100 ┤                  ███                          │
   │   80 ┤      ████        ███                          │
   │   60 ┤      ████  ███   ███                          │
   │   40 ┤      ████  ███   ███  ███                     │
   │   20 ┤ ███  ████  ███   ███  ███  ███                │
   │    0 └─────────────────────────────────────────      │
   │     class rapide paroles génér. karaok mollo         │
   └──────────────────────────────────────────────────────┘
```

### Types de visualisations disponibles

| Type            | Usage                                        |
| --------------- | -------------------------------------------- |
| **Time series** | Évolution d'une métrique dans le temps       |
| **Stat**        | Valeur unique (dernière valeur)              |
| **Bar chart**   | Comparaison entre catégories                 |
| **Gauge**       | Jauge (0-100%)                               |
| **Heatmap**     | Distribution 2D (ex: latence par heure)      |
| **Table**       | Tableau de données                           |
| **Pie chart**   | Répartition en secteurs                      |
| **Logs**        | Visualisation de logs (depuis Elasticsearch) |

---

## Système d'alertes

### Pourquoi les alertes ?

Les dashboards permettent de **surveiller** manuellement. Les alertes permettent d'être **notifié automatiquement** quand quelque chose ne va pas, même sans regarder Grafana.

### Configuration d'une alerte

```
1. Ouvrir un panel existant
2. Onglet "Alert" → "New alert rule"

Exemple : Alerte si taux d'erreur HTTP > 1%

Conditions :
  Query A : rate(instantmusic_http_requests_total{status_code=~"5.."}[5m])
  Query B : rate(instantmusic_http_requests_total[5m])
  Expression : A / B * 100 > 1

Timing :
  Evaluate every : 1m
  For             : 5m  (doit être vrai pendant 5 minutes consécutives)

Labels :
  severity : critical
  team     : backend
```

### Alertes recommandées pour InstantMusic

```yaml
# Alertes critiques

- name: "Taux erreur HTTP élevé"
  condition: >
    sum(rate(instantmusic_http_requests_total{status_code=~"5.."}[5m]))
    / sum(rate(instantmusic_http_requests_total[5m])) * 100 > 1
  for: 5m
  severity: critical

- name: "Latence API élevée"
  condition: >
    histogram_quantile(0.99,
      rate(instantmusic_http_request_duration_seconds_bucket[5m])
    ) > 2
  for: 5m
  severity: warning

- name: "Parties bloquées"
  condition: instantmusic_games_active > 50
  for: 10m
  severity: warning

- name: "Celery tâches en échec"
  condition: >
    rate(instantmusic_celery_tasks_total{status="failure"}[5m]) > 0.1
  for: 5m
  severity: warning

- name: "API Deezer indisponible"
  condition: >
    rate(instantmusic_external_api_errors_total{service="deezer"}[5m])
    / rate(instantmusic_external_api_requests_total{service="deezer"}[5m]) > 0.5
  for: 3m
  severity: critical

- name: "CPU élevé"
  condition: >
    100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
  for: 10m
  severity: critical
```

### Canaux de notification (Contact Points)

```
1. Menu → Alerting → Contact points → New contact point

Types disponibles :
  ├── Email
  ├── Slack
  ├── PagerDuty
  ├── Discord
  ├── Telegram
  ├── Webhook (custom HTTP)
  └── ...

Exemple Slack :
  Name       : "Slack Backend Team"
  Type       : Slack
  Webhook URL: https://hooks.slack.com/services/...
  Channel    : #monitoring-alerts
```

---

## Provisioning automatique des dashboards

Les dashboards sont versionnés dans Git et chargés automatiquement au démarrage de Grafana.

```yaml
# _devops/monitoring/grafana/provisioning/dashboards/dashboards.yml

apiVersion: 1

providers:
  - name: "InstantMusic Dashboards"
    orgId: 1
    folder: "InstantMusic"
    type: file
    disableDeletion: false
    updateIntervalSeconds: 60  # Reload si fichier modifié
    options:
      path: /etc/grafana/provisioning/dashboards
```

Les fichiers JSON des dashboards sont dans :
```
_devops/monitoring/grafana/dashboards/
├── application-overview.json
└── system-overview.json
```

Pour exporter un dashboard modifié dans Grafana :
```
Dashboard → Settings (engrenage) → JSON Model → Copier
→ Coller dans le fichier .json correspondant
→ Commit dans Git
```

---

## Bonnes pratiques

### 1. Conventions de nommage

```
Dashboards :
  "InstantMusic — [Nom]"  ex: "InstantMusic — Application Overview"

Panels :
  "[Métrique] ([unité])"  ex: "Latence p95 (ms)", "Requêtes/sec"
```

### 2. Variables de template

Les variables permettent de filtrer un dashboard sans modifier la requête :

```
Variable "instance" :
  Query: label_values(instantmusic_http_requests_total, instance)
  → Ajoute un filtre dropdown en haut du dashboard
  → Permet de filtrer par serveur en multi-instance
```

### 3. Annotations

Les annotations marquent des événements importants sur les graphiques :

```
Annotation "Déploiements" :
  Query: rate(instantmusic_http_requests_total[5m]) == 0
  → Marque les redémarrages de l'application
  → Visible comme une ligne verticale sur les graphiques
```
