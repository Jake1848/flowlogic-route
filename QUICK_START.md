# 🚀 FlowLogic Route - Quick Start Guide
## Deploy to flowlogicroute.com

### 📋 Pre-Deployment Checklist

**1. Purchase Domain**
- ✅ Buy **flowlogicroute.com** from your registrar
- Get nameservers/DNS management access

**2. Get a Server**
Choose one option:
- **DigitalOcean**: $20/month (4GB RAM, 2 CPU)
- **Linode**: $24/month (4GB RAM, 2 CPU)  
- **Vultr**: $24/month (4GB RAM, 2 CPU)
- **AWS EC2**: t3.medium (~$30/month)

**3. Server Setup**
```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again
exit
```

### 🌐 DNS Configuration

**Set these DNS records** (replace `YOUR.SERVER.IP` with actual IP):

| Type | Name    | Value          | TTL  |
|------|---------|----------------|------|
| A    | @       | YOUR.SERVER.IP | 300  |
| A    | www     | YOUR.SERVER.IP | 300  |
| A    | api     | YOUR.SERVER.IP | 300  |
| A    | core    | YOUR.SERVER.IP | 300  |
| A    | traefik | YOUR.SERVER.IP | 300  |

### 🚀 One-Command Deployment

**1. Upload Files to Server**
```bash
# On your server
git clone <your-repo-url> flowlogic
cd flowlogic
```

**2. Configure Environment**
```bash
# Copy production config
cp .env.production .env

# Get Mapbox token (free): https://account.mapbox.com/access-tokens/
nano .env
# Update MAPBOX_ACCESS_TOKEN=pk.your_token_here
```

**3. Deploy Everything**
```bash
# One command deployment
./deploy.sh
```

### 🎯 Your Live URLs

After deployment (5-10 minutes):
- **Main Website**: https://flowlogicroute.com
- **API Documentation**: https://api.flowlogicroute.com/docs
- **Core Routing API**: https://core.flowlogicroute.com
- **Admin Dashboard**: https://api.flowlogicroute.com/admin
- **Traefik Dashboard**: https://traefik.flowlogicroute.com

### 🔧 Customization Options

**Branding (in .env)**
```bash
SITE_NAME="FlowLogic Route"
# or
SITE_NAME="YourCompany Route Optimizer"
```

**API Limits**
```bash
RATE_LIMIT_FREE=60          # 60 requests/minute
RATE_LIMIT_STARTER=300      # 300 requests/minute
```

### 📊 Monitoring

**Check Status**
```bash
docker-compose ps                    # Service status
docker-compose logs -f frontend      # Frontend logs
docker-compose logs -f api          # API logs
docker stats                        # Resource usage
```

**View Live Metrics**
- SSL Status: https://traefik.flowlogicroute.com
- System Health: https://api.flowlogicroute.com/health

### 🔒 Security Features

✅ **Automatic HTTPS** with Let's Encrypt  
✅ **Rate Limiting** (configurable)  
✅ **Security Headers** (XSS, CSRF protection)  
✅ **Docker Security** (non-root containers)  
✅ **Database Encryption**  
✅ **API Authentication** (JWT tokens)

### 💾 Backup & Updates

**Automatic Backups**
- Database backed up daily
- Stored locally and optionally in S3

**Manual Backup**
```bash
docker-compose exec postgres pg_dump -U postgres flowlogic > backup.sql
```

**Update Application**
```bash
git pull origin main
./deploy.sh
```

### 💰 Total Monthly Cost: ~$25-40

- **Server**: $20-35/month
- **Domain**: $10-15/year ($1.25/month)
- **SSL Certificate**: Free (Let's Encrypt)
- **Mapbox Maps**: Free (50K requests/month)

### 🆘 Troubleshooting

**SSL Certificate Issues**
```bash
# Check Traefik logs
docker-compose logs traefik

# Verify DNS propagation
nslookup flowlogicroute.com
```

**Service Not Starting**
```bash
# Check specific service
docker-compose logs <service-name>

# Restart services
docker-compose restart
```

**Can't Access Website**
1. Check DNS propagation (24-48 hours)
2. Verify server firewall allows ports 80, 443
3. Check service status: `docker-compose ps`

### 🎉 Success Checklist

- [ ] Domain purchased and DNS configured
- [ ] Server provisioned with Docker installed
- [ ] Code deployed and services running
- [ ] HTTPS working (green padlock in browser)
- [ ] Main website accessible at https://flowlogicroute.com
- [ ] API docs working at https://api.flowlogicroute.com/docs
- [ ] Test route optimization with sample data

**🚀 Your professional route optimization platform is now live!**

### 📞 Next Steps

1. **Test the routing functionality** with real data
2. **Customize branding** and colors to match your style  
3. **Set up monitoring** alerts for uptime
4. **Consider premium features** (user accounts, billing, etc.)
5. **Marketing**: Share your new platform!

**FlowLogic Route is ready to optimize delivery routes at scale!** 🎯