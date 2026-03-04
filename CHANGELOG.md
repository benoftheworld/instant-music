# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et ce projet adhère au [Versionnement Sémantique](https://semver.org/lang/fr/).

## [Non publié]

### Ajouté

- Système de boutique et bonus en partie (double points, max points, temps bonus, 50/50, vol, bouclier)
- Mode Karaoké avec paroles synchronisées via LRCLib et lecture YouTube
- Système d'invitations en partie et notifications WebSocket temps réel
- Export des données utilisateur (RGPD Art. 20) enrichi (réponses, achievements, équipes, inventaire)
- Consentement à la politique de confidentialité obligatoire à l'inscription
- Tâches Celery de purge automatique des données expirées (invitations, anciens jeux)
- Monitoring complet avec Prometheus, Grafana, ELK Stack
- Service de tokens centralisé (tokenService.ts) pour la gestion JWT frontend
- Types TypeScript pour l'API YouTube IFrame Player

### Modifié

- Séparation de `games/services.py` (1309 lignes) en 4 modules spécialisés
- Centralisation des constantes bonus (BONUS_META), modes de jeu (GAME_MODE_CONFIG), et types partagés
- Unification des interfaces `Round` et `Player` dupliquées dans le frontend
- Utilitaire `formatAnswer` partagé entre les composants
- Utilitaire `mergeUpdatedPlayers` extrait pour éviter la duplication dans GamePlayPage
- Séparation de `statsService` depuis `achievementService`
- Vérification de sécurité au démarrage pour les clés sensibles en production
- Clé JWT (`JWT_SIGNING_KEY`) séparée de `SECRET_KEY`
- Redis protégé par mot de passe en production

### Corrigé

- Exposition des erreurs internes via `str(e)` dans les réponses API (remplacé par messages génériques)
- `except: pass` silencieux remplacés par `logger.exception()` dans les services de jeu
- Endpoint `available` ne filtrait pas les parties publiques (`is_public=True`)
- Doublon `@transaction.atomic` sur `submit_answer`
- `.gitignore` corrigé (celerybeat-schedule, .DS_Store)
- Contrainte Django mise à jour de `>=4.2,<5.0` à `>=5.1,<5.2`
- Import tardif `import random` dans `shop/services.py` déplacé en haut du fichier
- Dépendances mortes (`black`, `flake8`, `isort`) retirées de requirements

### Sécurité

- Les secrets avec valeurs par défaut provoquent maintenant une erreur `ImproperlyConfigured` en production
- Permissions explicites (`AllowAny`) au lieu de `permission_classes=[]`
- Séparation des handlers d'exception JWT (warning vs exception logging)
