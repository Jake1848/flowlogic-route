-- FlowLogic RouteAI Database Initialization Script
-- This script creates necessary databases, users, and initial configuration

-- Create databases if they don't exist
SELECT 'CREATE DATABASE flowlogic_saas'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'flowlogic_saas')\gexec

SELECT 'CREATE DATABASE flowlogic_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'flowlogic_test')\gexec

-- Create application user with appropriate permissions
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'flowlogic_user') THEN

      CREATE ROLE flowlogic_user LOGIN PASSWORD 'flowlogic_secure_password';
   END IF;
END
$do$;

-- Grant permissions to flowlogic_user
GRANT CONNECT ON DATABASE flowlogic TO flowlogic_user;
GRANT CONNECT ON DATABASE flowlogic_saas TO flowlogic_user;
GRANT CONNECT ON DATABASE flowlogic_test TO flowlogic_user;

-- Connect to main database and set up schema
\c flowlogic;

-- Grant schema permissions
GRANT ALL PRIVILEGES ON SCHEMA public TO flowlogic_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO flowlogic_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO flowlogic_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO flowlogic_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO flowlogic_user;

-- Connect to SaaS database and set up schema
\c flowlogic_saas;

-- Grant schema permissions
GRANT ALL PRIVILEGES ON SCHEMA public TO flowlogic_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO flowlogic_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO flowlogic_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO flowlogic_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO flowlogic_user;

-- Connect to test database and set up schema
\c flowlogic_test;

-- Grant schema permissions
GRANT ALL PRIVILEGES ON SCHEMA public TO flowlogic_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO flowlogic_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO flowlogic_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO flowlogic_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO flowlogic_user;

-- Create extensions that might be needed
\c flowlogic;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

\c flowlogic_saas;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

\c flowlogic_test;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";