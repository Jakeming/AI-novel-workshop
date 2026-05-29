-- Deconstruct Studio — PostgreSQL schema
-- Run: psql -U your_user -d deconstruct_studio -f schema.sql

CREATE DATABASE deconstruct_studio;

\c deconstruct_studio;

-- ===== Users =====
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(100) NOT NULL UNIQUE,
    stage           VARCHAR(20) NOT NULL DEFAULT 'novice',
    cooldown_until  TIMESTAMPTZ,
    consecutive_failures INT NOT NULL DEFAULT 0,
    daily_submit_count INT NOT NULL DEFAULT 0,
    last_submit_date    DATE,
    reputation_score    FLOAT NOT NULL DEFAULT 0.0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===== Deconstruct Sessions =====
CREATE TABLE deconstruct_sessions (
    id                  SERIAL PRIMARY KEY,
    user_id             INT NOT NULL REFERENCES users(id),
    source_title        VARCHAR(500),
    source_url          TEXT,
    source_word_count   INT,
    status              VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    -- Node timestamps
    node1_completed_at  TIMESTAMPTZ,
    node2_completed_at  TIMESTAMPTZ,
    node3_completed_at  TIMESTAMPTZ,
    node4_completed_at  TIMESTAMPTZ,
    node5_completed_at  TIMESTAMPTZ,
    node6_completed_at  TIMESTAMPTZ,
    node7_completed_at  TIMESTAMPTZ,
    -- AI outputs (JSON blobs)
    deep_read_result        JSONB,
    deconstruct_result      JSONB,
    skeleton_result         JSONB,
    -- User inputs
    three_answers           JSONB,   -- {conflict_cause, motivation, value_core}
    archive_notes           JSONB,   -- {core_technique, best_paragraph, reusability_score}
    -- Validation
    last_verdict            VARCHAR(10),  -- green / yellow / red
    validation_log          JSONB,   -- array of {timestamp, verdict, similarities}
    cooldown_triggered      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sessions_user ON deconstruct_sessions(user_id);
CREATE INDEX idx_sessions_status ON deconstruct_sessions(status);

-- ===== Imitation Drafts (版本控制) =====
CREATE TABLE imitation_drafts (
    id              SERIAL PRIMARY KEY,
    session_id      INT NOT NULL REFERENCES deconstruct_sessions(id),
    version         INT NOT NULL DEFAULT 1,
    content         TEXT NOT NULL,
    similarity_result   JSONB,   -- full check_similarity output
    verdict         VARCHAR(10),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_drafts_session ON imitation_drafts(session_id);

-- ===== Skeleton Library =====
CREATE TABLE skeleton_library (
    id                      SERIAL PRIMARY KEY,
    session_id              INT REFERENCES deconstruct_sessions(id),
    contributor_user_id     INT REFERENCES users(id),
    text_skeleton           TEXT NOT NULL,
    mermaid_code            TEXT,
    topology_cluster_id     VARCHAR(50),   -- classification label
    contributor_reputation  FLOAT NOT NULL DEFAULT 0.0,
    is_public               BOOLEAN NOT NULL DEFAULT FALSE,
    reusability_score       INT,           -- 1-5
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_skeleton_topology ON skeleton_library(topology_cluster_id);
CREATE INDEX idx_skeleton_public ON skeleton_library(is_public) WHERE is_public = TRUE;

-- ===== Inspiration Library (Milvus will index this) =====
-- Metadata table; vectors stored in Milvus
CREATE TABLE inspiration_entries (
    id              SERIAL PRIMARY KEY,
    user_id         INT NOT NULL REFERENCES users(id),
    session_id      INT REFERENCES deconstruct_sessions(id),
    original_text   TEXT NOT NULL,          -- the specific passage
    essence_note    TEXT NOT NULL,          -- user's "打动我的本质" note
    technique_abstraction  TEXT,            -- AI's abstract description
    milvus_id       VARCHAR(100),           -- vector ID in Milvus
    embedding_score FLOAT,                  -- similarity at collection time
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_inspiration_user ON inspiration_entries(user_id);

-- ===== Guardian AI Alerts =====
CREATE TABLE guardian_alerts (
    id              SERIAL PRIMARY KEY,
    probe_name      VARCHAR(100) NOT NULL,
    severity        VARCHAR(20) NOT NULL,   -- info / warn / critical
    user_id         INT REFERENCES users(id),
    message         TEXT NOT NULL,
    context_snapshot    JSONB,              -- what the probe saw
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_probe ON guardian_alerts(probe_name);
CREATE INDEX idx_alerts_severity ON guardian_alerts(severity);
CREATE INDEX idx_alerts_unresolved ON guardian_alerts(resolved_at) WHERE resolved_at IS NULL;
