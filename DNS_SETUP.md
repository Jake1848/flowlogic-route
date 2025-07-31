# 🌐 DNS Setup for flowlogicroute.com

## Where to Set DNS Records

Go to your domain registrar where you bought flowlogicroute.com:
- **GoDaddy**: DNS Management
- **Namecheap**: Advanced DNS  
- **Cloudflare**: DNS Records
- **Google Domains**: DNS
- **Other**: Look for "DNS", "Name Servers", or "DNS Management"

## Required DNS Records

**IMPORTANT**: Set these records after you deploy to Render (Step 3). You'll get the exact URLs from Render dashboard.

### For Render.com Deployment:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | @ | `flowlogic-frontend.onrender.com` | 300 |
| CNAME | www | `flowlogic-frontend.onrender.com` | 300 |
| CNAME | api | `flowlogic-api.onrender.com` | 300 |

### Alternative (if CNAME @ doesn't work):

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | `[Render IP Address]` | 300 |
| CNAME | www | `flowlogicroute.com` | 300 |
| CNAME | api | `flowlogic-api.onrender.com` | 300 |

## 📝 DNS Setup Instructions

### GoDaddy:
1. Login to GoDaddy
2. Go to "My Products" → "DNS"
3. Find flowlogicroute.com → "Manage DNS"
4. Add the CNAME records above

### Namecheap:
1. Login to Namecheap  
2. Go to "Domain List"
3. Click "Manage" next to flowlogicroute.com
4. Go to "Advanced DNS" tab
5. Add the CNAME records above

### Cloudflare:
1. Login to Cloudflare
2. Select flowlogicroute.com domain
3. Go to "DNS" → "Records"
4. Add the CNAME records above
5. Set Proxy Status to "DNS Only" (gray cloud)

## ⏱️ DNS Propagation

- **Wait Time**: 5 minutes to 48 hours
- **Check Status**: Use https://dnschecker.org
- **Test**: `nslookup flowlogicroute.com`

## 🔍 Verification

After DNS propagates, these should work:
- ✅ https://flowlogicroute.com → Your React website
- ✅ https://www.flowlogicroute.com → Your React website  
- ✅ https://api.flowlogicroute.com → Your API

## 🆘 Troubleshooting

**"This site can't be reached"**
- DNS hasn't propagated yet (wait 2-24 hours)
- Check DNS records are correct
- Try incognito/private browser mode

**"Not Secure" warning**
- SSL certificate is being generated (wait 10-30 minutes)
- Render automatically handles SSL for custom domains

**Need Help?**
1. Check Render dashboard for exact CNAME values
2. Use DNS checker tools online
3. Contact your domain registrar support

## 🎯 Next Steps

1. ✅ Create GitHub repo (Step 1)
2. ✅ Set up Render deployment (Step 3) 
3. ✅ Get CNAME values from Render dashboard
4. ✅ Add DNS records using values above
5. ✅ Wait for DNS to propagate
6. ✅ Visit https://flowlogicroute.com - You're live! 🚀