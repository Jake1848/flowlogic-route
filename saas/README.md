# FlowLogic RouteAI SaaS Backend

Production-ready SaaS backend infrastructure for FlowLogic RouteAI with comprehensive authentication, billing, and usage management.

## 🚀 Features

### Authentication & Authorization
- **Firebase Auth Integration**: Secure user authentication with Google, email/password
- **API Key Management**: Generate, rotate, and manage API keys with IP restrictions
- **Role-Based Access**: Admin and user roles with proper permission controls
- **JWT Token Support**: Stateless authentication for API access

### Billing & Subscriptions
- **Stripe Integration**: Complete payment processing and subscription management
- **Multiple Tiers**: Free, Starter ($49/mo), Professional ($199/mo), Enterprise ($999/mo)
- **Webhook Processing**: Automated billing event handling
- **Customer Portal**: Self-service billing management

### Usage Management
- **Real-time Metering**: Track route generation, API calls, and resource usage
- **Rate Limiting**: Redis-based sliding window rate limiting per tier
- **Usage Analytics**: Comprehensive usage statistics and historical data
- **Limit Enforcement**: Automatic enforcement of tier-based usage limits

### Admin Dashboard
- **User Management**: View, edit, and manage user accounts
- **Usage Analytics**: System-wide usage statistics and trends
- **Billing Insights**: Revenue metrics and subscription analytics
- **System Health**: Monitor database, Redis, and external service health

## 📊 Subscription Tiers

| Tier | Price | Routes/Month | Features |
|------|-------|--------------|----------|
| **Free** | $0 | 10 | Basic optimization, Email support |
| **Starter** | $49 | 200 | Advanced AI, CSV upload, Priority support |
| **Professional** | $199 | 1,000 | Live re-routing, API access, Analytics |
| **Enterprise** | $999 | 10,000 | Custom deployment, SLA, Multi-tenant |

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   SaaS API      │    │   Core API      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
            ┌───────▼───┐ ┌───▼───┐ ┌───▼────┐
            │PostgreSQL │ │ Redis │ │Firebase│
            │           │ │       │ │  Auth  │
            └───────────┘ └───────┘ └────────┘
                    │
            ┌───────▼───────┐
            │    Stripe     │
            │   Webhooks    │
            └───────────────┘
```

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (optional)

### 1. Environment Setup

```bash
# Clone repository
git clone <repo-url>
cd flowlogic_routeai/saas

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required Environment Variables:**
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/flowlogic_saas

# Firebase Auth
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# Stripe
STRIPE_SECRET_KEY=sk_live_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret

# Redis
REDIS_URL=redis://localhost:6379/0
```

### 3. Database Setup

```bash
# Install Alembic for migrations
pip install alembic

# Initialize database
alembic upgrade head

# Create admin user (optional)
python scripts/create_admin.py
```

### 4. Run Application

#### Development
```bash
python -m uvicorn main:app --reload --port 8001
```

#### Production with Docker
```bash
docker-compose up -d
```

## 🔧 API Documentation

### Authentication Methods

#### 1. API Key Authentication
```bash
curl -H "Authorization: Bearer fl_live_your_api_key" \
     https://api.flowlogic.ai/users/profile
```

#### 2. Firebase Token Authentication
```bash
curl -H "Authorization: Bearer firebase_id_token" \
     https://api.flowlogic.ai/users/profile
```

### Core Endpoints

#### User Management
- `GET /users/profile` - Get user profile
- `PUT /users/profile` - Update profile
- `GET /users/api-keys` - List API keys
- `POST /users/api-keys` - Create API key
- `DELETE /users/api-keys/{id}` - Revoke API key

#### Billing
- `GET /billing/plans` - Available plans
- `GET /billing/subscription` - Current subscription
- `POST /billing/checkout` - Create checkout session
- `POST /billing/portal` - Customer portal
- `POST /billing/cancel` - Cancel subscription

#### Admin (Admin Only)
- `GET /admin/dashboard` - Dashboard stats
- `GET /admin/users` - User management
- `GET /admin/usage/overview` - Usage analytics
- `GET /admin/system/health` - System health

#### Webhooks
- `POST /webhooks/stripe` - Stripe webhook handler

## 📈 Usage Tracking

### Automatic Metering
Every route generation request is automatically tracked:

```python
# Automatically recorded per request
await usage_service.record_route_usage(
    db=db,
    user_id=user_id,
    endpoint="/route/auto",
    addresses_count=5,
    trucks_generated=2,
    stops_processed=8,
    total_miles=124.5,
    fuel_cost=67.89,
    success=True
)
```

### Rate Limiting
Redis-based sliding window rate limiting:

```python
# Per-tier rate limits (requests/minute)
limits = {
    "free": 10,
    "starter": 60,
    "professional": 300,
    "enterprise": 1000
}
```

### Usage Limits
Monthly route generation limits enforced per tier:

```python
# Check before processing
usage_check = await usage_service.check_usage_limits(db, user_id)
if not usage_check["allowed"]:
    raise HTTPException(402, "Usage limit exceeded")
```

## 🔐 Security Features

### API Key Security
- **Secure Generation**: Cryptographically secure random keys
- **Hashed Storage**: Keys stored as SHA-256 hashes
- **IP Restrictions**: Optional IP allowlisting per key
- **Expiration**: Configurable key expiration
- **Usage Tracking**: Monitor key usage patterns

### Rate Limiting
- **Sliding Window**: More accurate than fixed windows
- **Per-User Limits**: Individual user rate limiting
- **Tier-Based**: Different limits per subscription tier
- **Redis Backend**: High-performance, distributed limiting

### Authentication
- **Firebase Integration**: Secure, scalable user auth
- **Token Validation**: Real-time token verification
- **Auto-Provisioning**: Create users on first login
- **Role Management**: Admin and user roles

## 📊 Monitoring & Analytics

### Health Checks
```bash
# System health
curl http://localhost:8001/health

# Response
{
  "status": "healthy",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "stripe": "healthy"
  }
}
```

### Metrics Collection
- **Request Metrics**: Response times, success rates
- **Usage Metrics**: Route generation, API calls
- **Business Metrics**: Revenue, user growth
- **Error Tracking**: Failed requests, exceptions

### Admin Dashboard
- Real-time user statistics
- Usage trends and analytics
- Revenue and billing insights
- System performance metrics

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run
docker-compose up -d

# Scale API
docker-compose up -d --scale saas-api=3

# Check logs
docker-compose logs -f saas-api
```

### Production Checklist
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure production database
- [ ] Set up Redis cluster
- [ ] Configure Stripe live keys
- [ ] Set up SSL certificates
- [ ] Configure monitoring
- [ ] Set up backup strategy
- [ ] Configure log aggregation

### Environment Variables
```env
# Production settings
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@prod-db:5432/flowlogic
REDIS_URL=redis://prod-redis:6379/0
STRIPE_SECRET_KEY=sk_live_your_production_key
```

## 🧪 Testing

### Unit Tests
```bash
pytest tests/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Load Testing
```bash
# Using locust
pip install locust
locust -f tests/load_test.py
```

## 📝 Database Schema

### Core Tables
- **users**: User accounts and profiles
- **subscriptions**: Billing and tier information
- **api_keys**: API key management
- **route_logs**: Route generation tracking
- **usage_records**: Monthly usage aggregation
- **webhook_logs**: Stripe webhook processing

### Indexes
Optimized indexes for performance:
- User lookup by Firebase UID
- API key validation
- Usage queries by user/date
- Admin dashboard aggregations

## 🔄 Webhook Processing

### Stripe Webhooks
Handles all subscription lifecycle events:

```python
# Supported events
events = [
    "customer.subscription.created",
    "customer.subscription.updated", 
    "customer.subscription.deleted",
    "invoice.payment_succeeded",
    "invoice.payment_failed",
    "checkout.session.completed"
]
```

### Webhook Security
- Signature verification
- Idempotency handling
- Retry logic
- Error tracking

## 🤝 Integration

### Core Routing API
```python
# Usage tracking middleware
@app.middleware("http")
async def track_usage(request: Request, call_next):
    # Check auth and limits
    auth = await authenticate_request(request)
    await check_usage_limits(auth.user_id)
    
    # Process request
    response = await call_next(request)
    
    # Record usage
    await record_usage(auth.user_id, request, response)
    
    return response
```

### Frontend Integration
```typescript
// API client with auth
const api = axios.create({
  baseURL: 'https://api.flowlogic.ai',
  headers: {
    'Authorization': `Bearer ${apiKey}`
  }
});

// Usage check
const usage = await api.get('/billing/usage');
if (usage.data.usage_percentage > 90) {
  showUpgradePrompt();
}
```

## 📚 API Reference

Complete API documentation available at:
- Development: `http://localhost:8001/docs`
- Production: Contact for access

## 🆘 Support

- **Documentation**: This README and API docs
- **Issues**: GitHub Issues
- **Email**: support@flowlogic.ai
- **Discord**: FlowLogic Community

## 📄 License

This SaaS backend is proprietary software. All rights reserved.