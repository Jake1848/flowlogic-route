# 🚀 FlowLogic RouteAI - Production Deployment Guide

## Overview
This guide will help you deploy FlowLogic RouteAI as a professional React website with your custom domain, automatic HTTPS, and production-grade infrastructure.

## 🎯 What You'll Get
- **Professional React Website** with interactive maps and routing
- **Custom Domain** with automatic HTTPS (Let's Encrypt SSL)
- **Production API Backend** with PostgreSQL database
- **Automatic Scaling** and health monitoring
- **Admin Dashboard** for managing the system

## 📋 Prerequisites

### 1. Server Requirements
- **VPS/Cloud Server** with:
  - 4GB+ RAM
  - 2+ CPU cores  
  - 50GB+ SSD storage
  - Ubuntu 20.04+ or similar
  - Docker & Docker Compose installed

### 2. Domain Name
- Purchase a domain name (e.g., `yourcompany.com`)
- Point DNS A records to your server IP:
  ```
  @ → your.server.ip.address
  www → your.server.ip.address
  api → your.server.ip.address
  traefik → your.server.ip.address
  ```

### 3. Optional Services
- **Mapbox Account** (free tier available) for maps: https://mapbox.com
- **OpenAI API Key** for natural language features (optional)

## 🚀 Quick Deploy (5 Minutes)

### Step 1: Clone and Configure
```bash
# Clone the repository
git clone <your-repo-url>
cd flowlogic_routeai

# Copy production environment file
cp .env.production .env

# Edit with your domain and settings
nano .env
```

### Step 2: Update .env File
Replace these key values in `.env`:
```bash
# Your domain
DOMAIN_NAME=yourdomain.com
ACME_EMAIL=admin@yourdomain.com
FRONTEND_API_URL=https://api.yourdomain.com

# Mapbox token (get from https://account.mapbox.com/access-tokens/)
MAPBOX_ACCESS_TOKEN=pk.your_mapbox_token

# Secure passwords
POSTGRES_PASSWORD=your_super_secure_password_123
JWT_SECRET=your_jwt_secret_key_456
```

### Step 3: Deploy Everything
```bash
# Create Docker network
docker network create flowlogic-network

# Deploy with production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check deployment status
docker-compose ps
```

### Step 4: Verify Deployment
- **Website**: https://yourdomain.com
- **API Docs**: https://api.yourdomain.com/docs
- **Traefik Dashboard**: https://traefik.yourdomain.com
- **Core API**: https://core.yourdomain.com

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Main Website** | `https://yourdomain.com` | React frontend with routing interface |
| **API Documentation** | `https://api.yourdomain.com/docs` | Interactive API documentation |
| **Core Routing API** | `https://core.yourdomain.com/route` | Direct routing algorithm access |
| **Health Check** | `https://api.yourdomain.com/health` | System health status |
| **Admin Dashboard** | `https://api.yourdomain.com/admin` | System administration |
| **Traefik Dashboard** | `https://traefik.yourdomain.com` | SSL & routing management |

## 🔧 Configuration Options

### Frontend Customization
Update these in `.env`:
```bash
SITE_NAME="Your Company RouteAI"
MAPBOX_ACCESS_TOKEN=your_token
```

### API Rate Limits
```bash
RATE_LIMIT_FREE=60          # Free tier: 60 requests/minute
RATE_LIMIT_STARTER=300      # Starter: 300 requests/minute  
RATE_LIMIT_PROFESSIONAL=1000 # Pro: 1000 requests/minute
```

### Resource Scaling
```bash
API_MEMORY_LIMIT=2g         # API service memory
POSTGRES_MEMORY_LIMIT=4g    # Database memory
REDIS_MEMORY_LIMIT=1g       # Cache memory
```

## 📊 Monitoring & Maintenance

### Check System Status
```bash
# View all services
docker-compose ps

# Check logs
docker-compose logs -f api
docker-compose logs -f frontend

# Monitor resource usage
docker stats
```

### Backup Database
```bash
# Manual backup
docker-compose exec postgres pg_dump -U postgres flowlogic > backup.sql

# Automated backups are configured to run daily
docker-compose logs backup
```

### Update Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and redeploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## 🔒 Security Features

- ✅ **Automatic HTTPS** with Let's Encrypt SSL certificates  
- ✅ **Rate Limiting** to prevent abuse
- ✅ **Security Headers** (HSTS, XSS Protection, etc.)
- ✅ **Docker Security** with non-root users
- ✅ **Database Encryption** in transit and at rest
- ✅ **API Authentication** with JWT tokens

## 🏗️ Architecture

```
Internet → Traefik (SSL/Load Balancer) → Frontend (React) → API (FastAPI) → Database (PostgreSQL)
                                      → Core API (Python) → Redis (Cache)
```

## 📱 Features

### For End Users
- **Interactive Map Interface** for route visualization
- **CSV Upload** for bulk stop imports  
- **Multiple Export Formats** (PDF, Excel, CSV)
- **Real-time Route Optimization**
- **Mobile-Responsive Design**

### For Administrators  
- **System Monitoring Dashboard**
- **User Management** (if SaaS features enabled)
- **Usage Analytics**
- **Backup Management**

## 🚦 Troubleshooting

### Common Issues

**1. SSL Certificate Issues**
```bash
# Check Traefik logs
docker-compose logs traefik

# Verify DNS is pointing to your server
nslookup yourdomain.com
```

**2. Database Connection Issues**
```bash
# Check database logs
docker-compose logs postgres

# Test database connection
docker-compose exec api python -c "from database.database import engine; print('DB OK')"
```

**3. Frontend Not Loading**
```bash
# Check frontend logs
docker-compose logs frontend

# Verify API connectivity
curl https://api.yourdomain.com/health
```

## 🔄 Scaling & Performance

### For High Traffic
1. **Increase Resource Limits** in `.env`
2. **Add Load Balancer** for multiple API instances
3. **Use Redis Clustering** for cache scaling
4. **PostgreSQL Read Replicas** for database scaling

### Monitoring
- **Built-in Health Checks** for all services
- **Traefik Metrics** dashboard
- **Database Performance** monitoring
- **API Response Time** tracking

## 💰 Cost Estimation

### Monthly Costs (USD)
- **VPS Server** (4GB RAM): $20-40/month
- **Domain Name**: $10-15/year  
- **Mapbox** (free tier): $0/month (up to 50K requests)
- **Let's Encrypt SSL**: Free
- **Total**: ~$25-45/month

## 🎉 Go Live Checklist

- [ ] Domain DNS configured and propagating
- [ ] Server provisioned with Docker installed
- [ ] `.env` file configured with your settings  
- [ ] Mapbox account created and token added
- [ ] Services deployed and running (`docker-compose ps`)
- [ ] HTTPS certificates auto-generated (check `https://yourdomain.com`)
- [ ] API documentation accessible (`https://api.yourdomain.com/docs`)
- [ ] Test routing functionality with sample data
- [ ] Backup system configured and tested

## 📞 Support

If you encounter issues:
1. Check the logs: `docker-compose logs <service-name>`
2. Verify environment configuration
3. Ensure all DNS records are properly configured
4. Test individual components separately

**You now have a production-ready route optimization platform!** 🚀