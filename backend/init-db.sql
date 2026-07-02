-- ValuerOS — Initial PostgreSQL + PostGIS setup
-- This runs automatically on first container start

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set statement timeout for long-running queries
ALTER DATABASE valueros SET statement_timeout = '300s';