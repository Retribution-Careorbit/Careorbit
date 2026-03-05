-- CareOrbit MVP — PostgreSQL Schema v0.3.0
-- Azure PostgreSQL Flexible Server + pgcrypto + uuid-ossp
-- HIPAA-compliant: PII encrypted at rest via pgp_sym_encrypt

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enum Types
CREATE TYPE subscription_tier AS ENUM ('free', 'premium_individual', 'premium_family');
CREATE TYPE document_type AS ENUM ('prescription', 'lab_report', 'medicine_strip');
CREATE TYPE document_status AS ENUM ('success', 'needs_confirmation', 'failed');
CREATE TYPE node_type AS ENUM ('medication', 'condition', 'lab_result', 'allergy', 'procedure');
CREATE TYPE permission_level AS ENUM ('view', 'edit', 'full');
CREATE TYPE caregiver_relationship AS ENUM ('spouse', 'son', 'daughter', 'parent', 'sibling', 'other');

-- Users table — PII fields encrypted with pgcrypto
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email BYTEA NOT NULL,                -- pgp_sym_encrypt(email, key)
    email_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 for lookups
    phone_number BYTEA,                  -- pgp_sym_encrypt(phone, key)
    password_hash VARCHAR(255) NOT NULL, -- bcrypt
    date_of_birth DATE,
    gender VARCHAR(10),
    city VARCHAR(100),
    state VARCHAR(100),
    preferred_language VARCHAR(5) DEFAULT 'en',
    tier subscription_tier DEFAULT 'free',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email_hash ON users(email_hash);

-- Refresh Tokens — SHA-256 hashed, supports rotation + revocation
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,   -- SHA-256 of raw token
    issued_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,                   -- NULL = active
    ip_address INET,
    user_agent TEXT,
    replaced_by UUID REFERENCES refresh_tokens(id) -- rotation chain
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);

-- Audit Log — APPEND-ONLY (NO updated_at column)
-- This table should NEVER have UPDATE or DELETE permissions
-- for application users — it's append-only for integrity.
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    patient_id UUID,
    action VARCHAR(50) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
    -- NO updated_at — append-only by design (HIPAA compliance)
);

CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_patient ON audit_log(patient_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);

-- Patient Profiles — extended demographic data
CREATE TABLE patient_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    conditions JSONB DEFAULT '[]'::jsonb,
    allergies JSONB DEFAULT '[]'::jsonb,
    emergency_contact BYTEA,              -- encrypted
    blood_type VARCHAR(5),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents — uploaded prescriptions, lab reports, medicine strips
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_type document_type NOT NULL,
    file_url TEXT NOT NULL,               -- Azure Blob Storage URL
    original_filename VARCHAR(255),
    content_type VARCHAR(50) NOT NULL,
    file_size_bytes INTEGER,
    ocr_text TEXT,
    ocr_confidence FLOAT,
    structured_data JSONB,
    processing_status document_status NOT NULL DEFAULT 'failed',
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_documents_patient ON documents(patient_id);
CREATE INDEX idx_documents_status ON documents(processing_status);

-- PHIG Nodes — Patient Health Information Graph
CREATE TABLE phig_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id),
    node_type node_type NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    rxnorm_code VARCHAR(20),
    loinc_code VARCHAR(20),
    icd10_code VARCHAR(20),
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    value FLOAT,
    unit VARCHAR(50),
    reference_range_low FLOAT,
    reference_range_high FLOAT,
    is_abnormal BOOLEAN,
    confidence_score FLOAT NOT NULL,
    confidence_source VARCHAR(50),        -- e.g. prescription_photo, patient_confirmed
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_phig_nodes_patient ON phig_nodes(patient_id);
CREATE INDEX idx_phig_nodes_type ON phig_nodes(node_type);
CREATE INDEX idx_phig_nodes_rxnorm ON phig_nodes(rxnorm_code);
CREATE INDEX idx_phig_nodes_active ON phig_nodes(is_active);

-- PHIG Edges — relationships between nodes (drug interactions, care gaps)
CREATE TABLE phig_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_node_id UUID NOT NULL REFERENCES phig_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES phig_nodes(id) ON DELETE CASCADE,
    edge_type VARCHAR(50) NOT NULL,       -- interaction, care_gap, contraindication
    severity VARCHAR(20),                 -- low, moderate, high, critical
    description TEXT,
    clinical_action TEXT,
    metadata JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_phig_edges_patient ON phig_edges(patient_id);
CREATE INDEX idx_phig_edges_source ON phig_edges(source_node_id);
CREATE INDEX idx_phig_edges_target ON phig_edges(target_node_id);

-- Medication Reminders
CREATE TABLE medication_reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    medication_node_id UUID NOT NULL REFERENCES phig_nodes(id) ON DELETE CASCADE,
    reminder_time TIME NOT NULL,
    days_of_week INTEGER[] DEFAULT '{1,2,3,4,5,6,7}',  -- ISO: 1=Mon, 7=Sun
    is_active BOOLEAN DEFAULT TRUE,
    last_sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reminders_patient ON medication_reminders(patient_id);
CREATE INDEX idx_reminders_active ON medication_reminders(is_active);

-- Subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier subscription_tier NOT NULL DEFAULT 'free',
    price_cents INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    payment_provider VARCHAR(50),         -- Phase 3: stripe/razorpay
    payment_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);

-- Usage Tracking — for tier limit enforcement
CREATE TABLE usage_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,   -- documents_per_month, summaries_per_month
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    usage_count INTEGER DEFAULT 0,
    UNIQUE(user_id, resource_type, period_start)
);

CREATE INDEX idx_usage_user_resource ON usage_tracking(user_id, resource_type);

-- Caregiver Links
CREATE TABLE caregiver_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    caregiver_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship caregiver_relationship NOT NULL,
    permission_level permission_level NOT NULL DEFAULT 'view',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    UNIQUE(patient_id, caregiver_id)
);

CREATE INDEX idx_caregiver_patient ON caregiver_links(patient_id);
CREATE INDEX idx_caregiver_caregiver ON caregiver_links(caregiver_id);

-- Adherence Tracking
CREATE TABLE adherence_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reminder_id UUID NOT NULL REFERENCES medication_reminders(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMPTZ NOT NULL,
    taken_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, taken, missed, skipped
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_adherence_patient ON adherence_records(patient_id);
CREATE INDEX idx_adherence_reminder ON adherence_records(reminder_id);

-- Chat History
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,            -- user, assistant
    message TEXT NOT NULL,
    language VARCHAR(5) DEFAULT 'en',
    agents_used TEXT[],
    alerts JSONB,
    care_gaps JSONB,
    confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_patient ON chat_messages(patient_id);
CREATE INDEX idx_chat_created ON chat_messages(created_at);
