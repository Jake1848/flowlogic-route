#!/bin/bash
set -e

echo "Starting FlowLogic RouteAI Services..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is ready!"

# Run database migrations
echo "Running database migrations..."
cd /app/saas
alembic upgrade head

# Create default admin user if specified
if [ "$CREATE_ADMIN" = "true" ] && [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_FIREBASE_UID" ]; then
    echo "Creating admin user..."
    python -c "
from database.database import SessionLocal
from database.models import User, Subscription
from datetime import datetime, timezone
import uuid

db = SessionLocal()
try:
    # Check if admin already exists
    existing = db.query(User).filter(User.email == '$ADMIN_EMAIL').first()
    if not existing:
        # Create admin user
        admin = User(
            id=uuid.uuid4(),
            firebase_uid='$ADMIN_FIREBASE_UID',
            email='$ADMIN_EMAIL',
            display_name='Admin User',
            is_admin=True,
            is_active=True,
            email_verified=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(admin)
        db.flush()
        
        # Create subscription
        subscription = Subscription(
            user_id=admin.id,
            tier='enterprise',
            status='active',
            monthly_route_limit=10000
        )
        db.add(subscription)
        db.commit()
        print('Admin user created successfully')
    else:
        print('Admin user already exists')
finally:
    db.close()
"
fi

# Start both services using supervisord or parallel processes
echo "Starting API services..."

# Create PID files directory
mkdir -p /var/run

# Start Core API in background
cd /app/app
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
CORE_PID=$!
echo $CORE_PID > /var/run/core-api.pid

# Start SaaS API in background
cd /app/saas
python -m uvicorn main:app --host 0.0.0.0 --port 8001 &
SAAS_PID=$!
echo $SAAS_PID > /var/run/saas-api.pid

# Function to handle shutdown
shutdown() {
    echo "Shutting down services..."
    kill -TERM $CORE_PID $SAAS_PID 2>/dev/null
    wait $CORE_PID $SAAS_PID
    echo "Services stopped."
    exit 0
}

# Trap signals for graceful shutdown
trap shutdown SIGTERM SIGINT

# Wait for both processes
echo "Services started. Core API on :8000, SaaS API on :8001"
wait $CORE_PID $SAAS_PID