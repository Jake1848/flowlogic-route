# FlowLogic RouteAI Deployment Guide

Complete guide for deploying FlowLogic RouteAI to various platforms with Docker.

## 🚀 Quick Start (Local Docker)

Deploy the entire system locally in one command:

```bash
# 1. Clone and setup
git clone <your-repo>
cd flowlogic_routeai

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Deploy everything
docker-compose up -d

# 4. Check status
docker-compose ps
```

**Access Points:**
- Core API: http://localhost:8000
- SaaS API: http://localhost:8001  
- Traefik Dashboard: http://localhost:8080
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## 📋 Prerequisites

### Required Services
- **Firebase Project**: For authentication
- **Stripe Account**: For billing (live or test mode)
- **Domain Name**: For production deployment (optional for development)

### Required Tools
- Docker & Docker Compose
- Git
- Text editor for configuration

## 🔧 Configuration

### 1. Firebase Setup

1. Create Firebase project at https://console.firebase.google.com
2. Enable Authentication with Email/Password and Google
3. Generate service account key:
   - Project Settings → Service Accounts
   - Generate new private key
   - Copy JSON content to `FIREBASE_SERVICE_ACCOUNT_JSON`

### 2. Stripe Setup

1. Create Stripe account at https://stripe.com
2. Get API keys from Dashboard → Developers → API keys
3. Create subscription products:
   ```bash
   # Create products and prices in Stripe Dashboard
   # Starter: $49/month
   # Professional: $199/month  
   # Enterprise: $999/month
   ```
4. Set webhook endpoint: `https://yourdomain.com/webhooks/stripe`
5. Copy webhook secret to `STRIPE_WEBHOOK_SECRET`

### 3. Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
# Required
POSTGRES_PASSWORD=your_secure_password
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account"...}
STRIPE_SECRET_KEY=sk_live_or_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Optional
OPENAI_API_KEY=sk-your_openai_key
GRAPHHOPPER_API_KEY=your_graphhopper_key

# Production
API_DOMAIN=api.yourdomain.com
ACME_EMAIL=admin@yourdomain.com
```

## 🏗️ Deployment Options

### Option 1: Local Development

```bash
# Standard development setup
docker-compose up -d

# With NGINX reverse proxy
docker-compose --profile nginx up -d

# With Traefik (recommended)
docker-compose --profile traefik up -d
```

### Option 2: Production with Docker

```bash
# Production deployment with SSL
docker-compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d

# With monitoring
docker-compose -f docker-compose.yml -f deploy/docker-compose.prod.yml --profile monitoring up -d

# With backup service
docker-compose -f docker-compose.yml -f deploy/docker-compose.prod.yml --profile backup up -d
```

### Option 3: Cloud Platforms

#### Railway.app
1. Connect GitHub repository
2. Configure environment variables from `.env.example`
3. Deploy automatically

#### Render.com
1. Import repository
2. Use `deploy/render.yaml` configuration
3. Set environment variables in dashboard
4. Deploy

#### Fly.io
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login and deploy
fly auth login
fly launch --config deploy/fly.toml
fly secrets set DATABASE_URL=postgresql://...
fly deploy
```

## 🔐 Security Setup

### SSL Certificates

#### Option 1: Let's Encrypt (Automatic)
```bash
# Set in .env
ACME_EMAIL=admin@yourdomain.com

# Deploy with Traefik
docker-compose --profile traefik up -d
```

#### Option 2: Manual Certificates
```bash
# Place certificates
mkdir -p docker/nginx/ssl
cp your-cert.pem docker/nginx/ssl/cert.pem
cp your-key.pem docker/nginx/ssl/key.pem

# Deploy with NGINX
docker-compose --profile nginx up -d
```

### Firewall Configuration
```bash
# Open required ports
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:8001/health

# Check Docker services
docker-compose ps
docker-compose logs api
```

### Database Backup
```bash
# Manual backup
docker-compose exec postgres pg_dump -U postgres flowlogic > backup.sql

# Automated backups (production)
docker-compose --profile backup up -d
```

### Log Management
```bash
# View logs
docker-compose logs -f api
docker-compose logs --tail 100 postgres

# Log rotation (production)
docker-compose --profile logging up -d
```

## 🚀 Scaling

### Horizontal Scaling
```bash
# Scale API instances
docker-compose up -d --scale api=3

# Use load balancer
docker-compose --profile traefik up -d
```

### Resource Limits
```yaml
# In docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Verify credentials
docker-compose exec postgres psql -U postgres -d flowlogic
```

#### API Not Starting
```bash
# Check API logs
docker-compose logs api

# Verify environment variables
docker-compose exec api env | grep -E "(DATABASE|REDIS)"
```

#### SSL Certificate Issues
```bash
# Check Traefik logs
docker-compose logs traefik

# Verify domain DNS
nslookup api.yourdomain.com
```

#### Stripe Webhooks Failing
```bash
# Check webhook logs
docker-compose exec api python -c "
from saas.database.database import SessionLocal
from saas.database.models import WebhookLog
db = SessionLocal()
logs = db.query(WebhookLog).order_by(WebhookLog.created_at.desc()).limit(10).all()
for log in logs:
    print(f'{log.created_at}: {log.event_type} - {log.success}')
"
```

### Performance Optimization

#### Database Tuning
```bash
# Run performance setup
docker-compose exec postgres psql -U postgres -d flowlogic -c "SELECT setup_performance_indexes();"
```

#### Redis Optimization
```bash
# Monitor Redis
docker-compose exec redis redis-cli info memory
docker-compose exec redis redis-cli info stats
```

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Configure Firebase project
- [ ] Set up Stripe account and products
- [ ] Configure domain DNS (for production)
- [ ] Prepare SSL certificates (if manual)
- [ ] Set all environment variables
- [ ] Test configuration locally

### Deployment
- [ ] Deploy database and Redis
- [ ] Deploy API services
- [ ] Configure reverse proxy
- [ ] Set up SSL certificates
- [ ] Configure monitoring
- [ ] Set up backup strategy

### Post-Deployment
- [ ] Verify health endpoints
- [ ] Test authentication flow
- [ ] Test billing integration
- [ ] Verify webhook handling
- [ ] Set up monitoring alerts
- [ ] Configure log rotation
- [ ] Test backup and restore

## 🆘 Support

### Logs Location
- API logs: `./logs/`
- Docker logs: `docker-compose logs [service]`
- Database logs: `docker-compose logs postgres`

### Useful Commands
```bash
# Complete restart
docker-compose down && docker-compose up -d

# Reset database
docker-compose down -v && docker-compose up -d

# Update images
docker-compose pull && docker-compose up -d

# Backup before update
./docker/scripts/backup.sh
```

### Getting Help
- Check logs first: `docker-compose logs api`
- Verify configuration: `docker-compose config`
- Test connectivity: `docker-compose exec api ping postgres`
- GitHub Issues: Create issue with logs and configuration

## 🔄 Updates & Maintenance

### Rolling Updates
```bash
# Pull latest images
docker-compose pull

# Rolling restart
docker-compose up -d --no-deps api

# Verify deployment
curl -f http://localhost:8001/health
```

### Database Migrations
```bash
# Run migrations manually
docker-compose exec api bash -c "cd saas && alembic upgrade head"

# Backup before migrations
./docker/scripts/backup.sh
```

### Monitoring Setup
```bash
# Deploy with monitoring
docker-compose --profile monitoring up -d

# Access Grafana
open http://localhost:3000
```

---

## 🎯 Quick Reference

| Service | Local Port | Production URL |
|---------|------------|----------------|
| Core API | 8000 | https://api.yourdomain.com/route |
| SaaS API | 8001 | https://api.yourdomain.com |
| PostgreSQL | 5432 | Internal only |
| Redis | 6379 | Internal only |
| Traefik Dashboard | 8080 | Internal only |

**One-command deployment:**
```bash
cp .env.example .env && vim .env && docker-compose up -d
```