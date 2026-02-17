# 🔐 Guide de Sécurité - InstantMusic Production

## 🎯 Checklist de Sécurité

### Avant le Déploiement

- [ ] **SECRET_KEY unique** générée avec au moins 50 caractères aléatoires
- [ ] **DEBUG=False** en production
- [ ] **ALLOWED_HOSTS** configuré avec votre domaine uniquement
- [ ] **Mots de passe forts** pour PostgreSQL (16+ caractères)
- [ ] **Certificat SSL/TLS** valide installé (Let's Encrypt)
- [ ] **CORS_ALLOWED_ORIGINS** limité à votre domaine frontend
- [ ] Fichier **.env.prod** ajouté au .gitignore
- [ ] **Clés API** sécurisées et limitées par domaine/IP

### Configuration Serveur

- [ ] **Firewall UFW** activé (ports 80, 443, 22 seulement)
- [ ] **SSH** sécurisé (clés SSH, pas de login root)
- [ ] **Fail2Ban** installé pour prévenir brute force
- [ ] **Mises à jour automatiques** activées
- [ ] **Backups automatiques** de la base de données
- [ ] **Monitoring** actif (logs, alertes)

### Docker

- [ ] Containers s'exécutent avec **utilisateur non-root**
- [ ] **Volumes** pour données persistantes uniquement
- [ ] **Networks** isolés entre services
- [ ] **Health checks** configurés
- [ ] **Restart policies** configurées (unless-stopped)
- [ ] Images Docker **à jour** régulièrement

---

## 🔑 Génération de Secrets Sécurisés

### SECRET_KEY Django

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Mot de passe PostgreSQL

```bash
openssl rand -base64 32
```

### Token API personnalisé

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🛡️ Configuration Nginx Sécurisée

### Headers de Sécurité Essentiels

```nginx
# Déjà inclus dans nginx/nginx.conf
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### Rate Limiting

```nginx
# Limiter les requêtes API
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req zone=api_limit burst=20 nodelay;
```

---

## 🔐 Configuration SSL/TLS

### Option 1: Let's Encrypt (Recommandé - Gratuit)

```bash
# Installation Certbot
sudo apt install certbot python3-certbot-nginx

# Obtenir un certificat
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Renouvellement automatique (déjà configuré)
sudo certbot renew --dry-run
```

### Option 2: Certificat Commercial

1. Acheter un certificat SSL auprès d'un CA
2. Placer les fichiers dans `nginx/ssl/`
3. Configurer dans `nginx/nginx.conf`

### Vérification SSL

- Test SSL Labs: https://www.ssllabs.com/ssltest/
- Objectif: Note A ou A+

---

## 🔒 Sécurité de la Base de Données

### PostgreSQL

```bash
# Changer le mot de passe en production
docker compose -f docker-compose.prod.yml exec db psql -U postgres
ALTER USER postgres WITH PASSWORD 'nouveau-mot-de-passe-fort';

# Créer un utilisateur dédié
CREATE USER instantmusic WITH PASSWORD 'mot-de-passe-fort';
GRANT ALL PRIVILEGES ON DATABASE instantmusic_prod TO instantmusic;
```

### Backups Chiffrés

```bash
# Backup avec chiffrement GPG
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U instantmusic instantmusic_prod | gzip | gpg -e -r your-email@example.com > backup_encrypted.sql.gz.gpg

# Restauration
gpg -d backup_encrypted.sql.gz.gpg | gunzip | docker compose -f docker-compose.prod.yml exec -T db psql -U instantmusic instantmusic_prod
```

---

## 🚨 Monitoring et Alertes

### Logs à Surveiller

```bash
# Erreurs backend
docker compose -f docker-compose.prod.yml logs backend | grep ERROR

# Accès suspicieux Nginx
docker compose -f docker-compose.prod.yml logs nginx | grep "40[0-4]\|50[0-3]"

# Tentatives de connexion échouées
sudo grep "Failed password" /var/log/auth.log
```

### Outils Recommandés

- **Sentry**: Monitoring erreurs application
- **Uptime Robot**: Monitoring disponibilité (gratuit)
- **Grafana + Prometheus**: Métriques détaillées
- **Fail2Ban**: Protection brute force automatique

---

## 🔍 Audit de Sécurité

### Vérifications Régulières (Mensuelles)

```bash
# Mises à jour système
sudo apt update && sudo apt upgrade

# Mises à jour Docker images
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# Vérifier les containers obsolètes
docker images | grep "<none>"
docker image prune -a

# Analyser les logs
docker compose -f docker-compose.prod.yml logs --since 24h | grep -i "error\|warning\|critical"
```

### Scan de Vulnérabilités

```bash
# Scanner les images Docker
docker scan instantmusic_backend_prod
docker scan instantmusic_frontend_prod

# Checker les dépendances Python
docker compose -f docker-compose.prod.yml exec backend pip list --outdated
docker compose -f docker-compose.prod.yml exec backend safety check
```

---

## 🚫 Configurations à Éviter

### ❌ Ne JAMAIS faire en Production

1. **DEBUG=True** en Django
2. **Mots de passe par défaut** (postgres/postgres)
3. **Exposer PostgreSQL/Redis** publiquement (ports 5432, 6379)
4. **Commiter .env.prod** dans Git
5. **Utiliser HTTP** sans HTTPS
6. **ALLOWED_HOSTS=['*']** ou vide
7. **Pas de limite de taux** sur les API endpoints
8. **Clés API sans restrictions** de domaine/IP
9. **Containers en mode root** sans raison
10. **Pas de backups** de la base de données

---

## 📱 APIs et OAuth - Bonnes Pratiques

### Google OAuth

```bash
# Redirect URIs autorisées uniquement:
https://yourdomain.com/api/auth/google/callback

# Domaines autorisés:
yourdomain.com

# Scopes minimaux nécessaires uniquement
```

---

## 🔐 Variables d'Environnement Sensibles

### Liste des Secrets à Protéger

```bash
# CRITIQUE - Ne JAMAIS exposer publiquement
SECRET_KEY=
POSTGRES_PASSWORD=
GOOGLE_OAUTH_CLIENT_SECRET=
EMAIL_HOST_PASSWORD=

# Gérer avec:
# - Fichiers .env.prod (gitignored)
# - Secrets Docker (docker secret)
# - Variables d'environnement serveur
# - Gestionnaires de secrets (Vault, AWS Secrets Manager)
```

---

## 🛠️ Incident Response

### En cas de Compromission Suspectée

1. **Isoler immédiatement**
   ```bash
   docker compose -f docker-compose.prod.yml down
   ```

2. **Changer tous les secrets**
   - SECRET_KEY Django
   - Mots de passe DB
   - Clés API
   - Certificats SSL

3. **Analyser les logs**
   ```bash
   # Dernières 24h
   docker compose -f docker-compose.prod.yml logs --since 24h > incident_logs.txt
   ```

4. **Vérifier les modifications**
   ```bash
   # Fichiers modifiés récemment
   find /var/www -type f -mtime -1
   ```

5. **Restaurer depuis backup**
   ```bash
   # Utiliser le dernier backup connu sain
   ./restore.sh backup_20260215.sql.gz
   ```

6. **Notifier les utilisateurs** si données compromises

---

## 📞 Ressources Supplémentaires

### Documentation Sécurité

- Django Security: https://docs.djangoproject.com/en/stable/topics/security/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Docker Security: https://docs.docker.com/engine/security/

### Outils d'Audit

- **Mozilla Observatory**: https://observatory.mozilla.org/
- **Security Headers**: https://securityheaders.com/
- **SSL Labs**: https://www.ssllabs.com/ssltest/

---

## ✅ Checklist Finale de Sécurité

Avant de mettre en production:

- [ ] SECRET_KEY unique générée
- [ ] DEBUG=False
- [ ] HTTPS activé avec certificat valide
- [ ] Firewall configuré
- [ ] SSH sécurisé
- [ ] Fail2Ban installé
- [ ] Mots de passe forts partout
- [ ] .env.prod non commité
- [ ] CORS correctement configuré
- [ ] Rate limiting activé
- [ ] Headers de sécurité Nginx
- [ ] Backups automatiques configurés
- [ ] Monitoring/alertes en place
- [ ] PostgreSQL non exposé publiquement
- [ ] Containers avec utilisateurs non-root

---

**La sécurité est un processus continu, pas un état final. Restez vigilant ! 🔒**
