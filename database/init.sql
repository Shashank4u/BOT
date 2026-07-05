-- AI Trading Assistant — PostgreSQL initialization
-- Extensions and schema setup for production database

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE trading_assistant TO trading_user;

-- Note: Tables are created by Alembic migrations or SQLAlchemy in development.
-- This file ensures the database is ready for the application.

COMMENT ON DATABASE trading_assistant IS 'AI Trading Assistant production database';
