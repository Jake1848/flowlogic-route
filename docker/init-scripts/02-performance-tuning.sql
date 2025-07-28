-- FlowLogic RouteAI Performance Tuning Configuration
-- Optimizes PostgreSQL settings for the FlowLogic RouteAI application

-- Connect to main database
\c flowlogic;

-- Performance tuning settings
-- Note: These are applied at database level, not instance level
-- for containerized environments

-- Create indexes for common query patterns if tables exist
-- These will be created when Alembic runs migrations

-- Connect to SaaS database for optimization
\c flowlogic_saas;

-- Create function to set up indexes after tables are created
CREATE OR REPLACE FUNCTION setup_performance_indexes()
RETURNS void AS $$
BEGIN
    -- Only create indexes if tables exist
    
    -- User lookup optimizations
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_firebase_uid 
        ON users(firebase_uid);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email 
        ON users(email);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active 
        ON users(is_active) WHERE is_active = true;
    END IF;

    -- API key lookup optimizations  
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'api_keys') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_key_hash 
        ON api_keys(key_hash);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_user_active 
        ON api_keys(user_id, is_active) WHERE is_active = true;
    END IF;

    -- Subscription queries
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'subscriptions') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_user_status 
        ON subscriptions(user_id, status);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_stripe_id 
        ON subscriptions(stripe_subscription_id);
    END IF;

    -- Usage tracking optimizations
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'route_logs') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_route_logs_user_date 
        ON route_logs(user_id, created_at);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_route_logs_date_success 
        ON route_logs(created_at, success);
    END IF;

    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'usage_records') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usage_records_user_month 
        ON usage_records(user_id, year, month);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usage_records_period 
        ON usage_records(year, month);
    END IF;

    -- Webhook processing
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'webhook_logs') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_webhook_logs_stripe_event 
        ON webhook_logs(stripe_event_id);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_webhook_logs_processed 
        ON webhook_logs(processed_at, success);
    END IF;

END;
$$ LANGUAGE plpgsql;

-- Create a trigger function to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Log that performance setup is complete
DO $$
BEGIN
    RAISE NOTICE 'Performance optimization functions created. Run setup_performance_indexes() after migrations.';
END $$;