-- Multi-Agent AI System Database Schema
-- PostgreSQL 12+

-- Create database (run manually)
-- CREATE DATABASE multiagent_ai;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    picture VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_email ON users(email);

-- Personas table
CREATE TABLE IF NOT EXISTS personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_type VARCHAR(100) NOT NULL,
    tone VARCHAR(50) DEFAULT 'professional',
    verbosity VARCHAR(50) DEFAULT 'balanced',
    style_preferences JSONB DEFAULT '{}',
    accepted_responses INTEGER DEFAULT 0,
    rejected_responses INTEGER DEFAULT 0,
    regeneration_patterns JSONB DEFAULT '{}',
    preferred_structures JSONB DEFAULT '[]',
    domain_knowledge JSONB DEFAULT '[]',
    learning_goals JSONB DEFAULT '[]',
    communication_style VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_used TIMESTAMP,
    UNIQUE(user_id, agent_type)
);

CREATE INDEX idx_persona_user_agent ON personas(user_id, agent_type);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    agents_used JSONB DEFAULT '[]',
    routing_decision JSONB DEFAULT '{}',
    response_time_ms INTEGER,
    token_usage JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversation_user_date ON conversations(user_id, created_at);

-- Feedback type
CREATE TYPE feedback_action AS ENUM ('accept', 'reject', 'regenerate', 'edit');

-- Feedbacks table
CREATE TABLE IF NOT EXISTS feedbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    action feedback_action NOT NULL,
    reason TEXT,
    edits TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_feedback_conversation ON feedbacks(conversation_id);
CREATE INDEX idx_feedback_action ON feedbacks(action);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_personas_updated_at BEFORE UPDATE ON personas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
