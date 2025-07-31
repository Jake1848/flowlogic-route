# 🚀 Complete Render.com Setup for FlowLogic Route

## Prerequisites
- ✅ GitHub repo created at: https://github.com/Jake1848/flowlogic-route
- ✅ Code pushed to GitHub
- ✅ Domain purchased: flowlogicroute.com

## Step 1: Create Render Account

1. Go to https://render.com
2. Click "Get Started for Free"  
3. Sign up with GitHub (easier integration)
4. Authorize Render to access your repos

## Step 2: Create Database Service

**A. Create PostgreSQL Database**
1. In Render dashboard, click "New +"
2. Select "PostgreSQL"
3. **Settings**:
   - Name: `flowlogic-db`
   - Database: `flowlogic`
   - User: `flowlogic_user`
   - Region: `Oregon (US West)`
   - Plan: `Starter ($7/month)`
4. Click "Create Database"
5. **IMPORTANT**: Copy the "External Database URL" - you'll need it!

**B. Create Redis Cache**
1. Click "New +" → "Redis"
2. **Settings**:
   - Name: `flowlogic-redis`
   - Region: `Oregon (US West)`
   - Plan: `Starter ($7/month)`
3. Click "Create Redis"
4. **IMPORTANT**: Copy the "Redis URL" - you'll need it!

## Step 3: Create Backend API Service

1. Click "New +" → "Web Service"
2. Connect your GitHub repo: `Jake1848/flowlogic-route`
3. **Settings**:
   - Name: `flowlogic-api`
   - Region: `Oregon (US West)`
   - Branch: `main`
   - Runtime: `Docker`
   - Dockerfile Path: `./docker/Dockerfile.api`
   - Plan: `Starter ($7/month)`

4. **Environment Variables** (Add these in Render):
   ```
   ENVIRONMENT = production
   DATABASE_URL = [Paste your PostgreSQL External Database URL]
   REDIS_URL = [Paste your Redis URL]
   DOMAIN_NAME = flowlogicroute.com
   JWT_SECRET = flowlogic_super_secret_jwt_key_2024
   RATE_LIMIT_FREE = 100
   RATE_LIMIT_STARTER = 500
   LOG_LEVEL = INFO
   MAX_STOPS_PER_TRUCK = 100
   DEFAULT_SERVICE_TIME_MINUTES = 15
   ```

5. **Custom Domain**:
   - Go to Settings tab
   - Click "Custom Domains"
   - Add: `api.flowlogicroute.com`
   - Copy the CNAME value (like `flowlogic-api.onrender.com`)

6. Click "Create Web Service"

## Step 4: Create Frontend Service

1. Click "New +" → "Web Service"
2. Same GitHub repo: `Jake1848/flowlogic-route`
3. **Settings**:
   - Name: `flowlogic-frontend`
   - Region: `Oregon (US West)`
   - Branch: `main`
   - Runtime: `Docker`
   - Dockerfile Path: `./frontend/Dockerfile`
   - Plan: `Starter ($7/month)`

4. **Environment Variables**:
   ```
   REACT_APP_API_URL = https://api.flowlogicroute.com
   REACT_APP_SITE_NAME = FlowLogic Route
   REACT_APP_MAPBOX_TOKEN = [Get from Step 5 below]
   ```

5. **Custom Domains**:
   - Go to Settings tab
   - Click "Custom Domains"
   - Add: `flowlogicroute.com`
   - Add: `www.flowlogicroute.com`
   - Copy the CNAME values

6. Click "Create Web Service"

## Step 5: Get Mapbox Token (Free)

1. Go to https://www.mapbox.com
2. Click "Get started for free"
3. Create account (free tier: 50,000 requests/month)
4. Go to https://account.mapbox.com/access-tokens/
5. Copy your "Default public token" (starts with `pk.`)
6. **Add to Frontend Environment Variables**:
   - Go back to Render dashboard
   - Click on `flowlogic-frontend` service
   - Environment tab
   - Update: `REACT_APP_MAPBOX_TOKEN = pk.your_mapbox_token_here`

## Step 6: Configure DNS Records

**Get CNAME Values from Render**:
- Frontend: `flowlogic-frontend.onrender.com`
- API: `flowlogic-api.onrender.com`

**Set DNS Records** (at your domain registrar):

| Type | Name | Value |
|------|------|-------|
| CNAME | @ | `flowlogic-frontend.onrender.com` |
| CNAME | www | `flowlogic-frontend.onrender.com` |
| CNAME | api | `flowlogic-api.onrender.com` |

## Step 7: Wait for Deployment

**Timeline**:
- Database creation: 2-3 minutes
- Backend deployment: 5-10 minutes  
- Frontend deployment: 3-5 minutes
- DNS propagation: 5 minutes - 24 hours

**Monitor Progress**:
- Check Render dashboard for build logs
- All services should show "Live" status
- Test internal URLs first:
  - `https://flowlogic-api.onrender.com/health`
  - `https://flowlogic-frontend.onrender.com`

## Step 8: Verify Your Live Website

**Test These URLs** (after DNS propagates):
- ✅ https://flowlogicroute.com (main website)
- ✅ https://www.flowlogicroute.com (should redirect)
- ✅ https://api.flowlogicroute.com/docs (API documentation)
- ✅ https://api.flowlogicroute.com/health (health check)

## 📊 Monthly Costs Breakdown

| Service | Cost | Purpose |
|---------|------|---------|
| PostgreSQL | $7/month | Database storage |
| Redis | $7/month | Caching & performance |
| Backend API | $7/month | Route optimization engine |
| Frontend | $7/month | React website |
| **Total** | **$28/month** | Complete platform |

## 🎉 Success Checklist

- [ ] Render account created
- [ ] PostgreSQL database deployed
- [ ] Redis cache deployed
- [ ] Backend API service deployed and "Live"
- [ ] Frontend service deployed and "Live"
- [ ] Mapbox token added to frontend
- [ ] Custom domains configured in Render
- [ ] DNS records set at domain registrar
- [ ] https://flowlogicroute.com loads successfully
- [ ] API docs accessible at https://api.flowlogicroute.com/docs
- [ ] Test route optimization with sample data

## 🆘 Troubleshooting

**Build Failed?**
```bash
# Check the build logs in Render dashboard
# Common issues:
- Wrong Dockerfile path
- Missing environment variables
- Database connection issues
```

**Domain Not Working?**
```bash
# Check DNS propagation
nslookup flowlogicroute.com

# Verify CNAME records
dig flowlogicroute.com CNAME
```

**API Errors?**
```bash
# Test direct Render URL first
curl https://flowlogic-api.onrender.com/health

# Check environment variables in Render dashboard
# Verify database connection string
```

## 🔄 Future Updates

**To update your website**:
1. Push changes to GitHub
2. Render automatically rebuilds and deploys
3. Zero-downtime updates

**Scaling Options**:
- Upgrade to Standard plan ($25/month per service) for more resources
- Add multiple backend instances for high traffic
- Use Render's built-in monitoring and alerts

## 🎯 You're Live!

Once everything is deployed:

🌐 **https://flowlogicroute.com** - Your professional route optimization platform  
📊 **$28/month** total cost  
🚀 **Ready for customers** and revenue  
💰 **Million-dollar potential** with modern tech stack  

**Congratulations! You now have a production-ready route optimization SaaS platform!** 🎉