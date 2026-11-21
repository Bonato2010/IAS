-- ====================================================================
-- SCHEMA COMPLETO v2.5: CENTRAL SHORTS - MULTI-SKILL AI CONTENT COMPANY
-- Suporte a 50.000+ referências, 10 Agentes Especializados, Podcasts,
-- Perfis Editoriais, Experimentos, Google Drive 5 TB e 20 Canais.
-- ====================================================================

-- 1. Categorias e Nichos (15 Categorias Obrigatórias + Dinâmicas)
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Biblioteca de Referências em Escala (Até 50.000+ Vídeos)
CREATE TABLE IF NOT EXISTS video_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER REFERENCES categories(id),
    youtube_id TEXT UNIQUE,
    url TEXT NOT NULL,
    title TEXT,
    author TEXT,
    views_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    duration_seconds REAL,
    hook_transcript TEXT,
    full_transcript TEXT,
    niche TEXT,
    content_type TEXT,
    pacing_bpm REAL,
    retention_score REAL,
    audio_features TEXT,
    visual_features TEXT,
    tags TEXT,
    gdrive_backup_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Padrões de Sucesso e Conhecimento Central
CREATE TABLE IF NOT EXISTS content_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER REFERENCES categories(id),
    pattern_type TEXT NOT NULL,
    title TEXT NOT NULL,
    structure_template TEXT NOT NULL,
    hook_formula TEXT,
    ideal_duration_seconds REAL,
    typical_retention_rate REAL,
    source_reference_id INTEGER REFERENCES video_references(id),
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Os 20 Canais YouTube Shorts Independentes
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_number INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    niche TEXT NOT NULL,
    subniche TEXT,
    target_audience TEXT,
    language TEXT DEFAULT 'pt-BR',
    visual_identity TEXT,
    editing_style TEXT,
    communication_tone TEXT,
    posting_frequency TEXT DEFAULT '2_por_dia',
    goals TEXT,
    editorial_strategy TEXT,
    youtube_channel_id TEXT,
    gdrive_channel_folder_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Roteiros Originais e Variantes Anti-Duplicação
CREATE TABLE IF NOT EXISTS scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER REFERENCES channels(id),
    category_id INTEGER REFERENCES categories(id),
    editorial_profile_id INTEGER REFERENCES editorial_profiles(id),
    title TEXT NOT NULL,
    hook TEXT NOT NULL,
    core_narrative TEXT NOT NULL,
    cta TEXT NOT NULL,
    full_script_json TEXT NOT NULL,
    target_duration REAL,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Pipeline de Produção (Integração Google Drive 5 TB)
CREATE TABLE IF NOT EXISTS production_pipeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER REFERENCES scripts(id),
    channel_id INTEGER REFERENCES channels(id),
    current_stage TEXT DEFAULT 'queue',
    progress_percent INTEGER DEFAULT 0,
    local_temp_file TEXT,
    gdrive_file_id TEXT,
    gdrive_web_link TEXT,
    rendered_at TIMESTAMP,
    final_duration REAL,
    error_log TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Publicações no YouTube e Histórico
CREATE TABLE IF NOT EXISTS publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    production_id INTEGER REFERENCES production_pipeline(id),
    channel_id INTEGER REFERENCES channels(id),
    youtube_video_id TEXT,
    published_url TEXT,
    scheduled_for TIMESTAMP,
    published_at TIMESTAMP,
    title TEXT NOT NULL,
    description TEXT,
    tags TEXT,
    status TEXT DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Métricas e Inteligência de Desempenho
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    publication_id INTEGER REFERENCES publications(id),
    channel_id INTEGER REFERENCES channels(id),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    estimated_retention_rate REAL,
    insights TEXT
);

-- 9. Logs e Auditoria Operacional (Google Drive, YouTube, Sistema)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Decisões e Deliberações dos 10 Agentes Especializados
CREATE TABLE IF NOT EXISTS agent_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id INTEGER,
    input_data TEXT,
    analysis TEXT,
    score INTEGER DEFAULT 0,
    confidence REAL DEFAULT 0.0,
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Episódios de Podcasts Longos Ingeridos
CREATE TABLE IF NOT EXISTS podcast_episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    source_url TEXT,
    channel_name TEXT,
    duration_seconds REAL,
    audio_path TEXT,
    transcript_path TEXT,
    status TEXT DEFAULT 'ingested',
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. Cortes Candidatos de Podcasts (Avaliados pelos 10 Agentes)
CREATE TABLE IF NOT EXISTS podcast_candidate_cuts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER REFERENCES podcast_episodes(id),
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    duration REAL NOT NULL,
    transcript TEXT NOT NULL,
    theme TEXT,
    target_audience TEXT,
    content_type TEXT,
    hook_suggested TEXT,
    justification TEXT,
    narrative_potential REAL,
    editing_strategy TEXT,
    title_suggestion TEXT,
    caption_suggestion TEXT,
    quality_score INTEGER DEFAULT 0,
    confidence_score REAL DEFAULT 0.0,
    agent_evaluations TEXT,
    director_decision TEXT DEFAULT 'pending_review',
    production_id INTEGER REFERENCES production_pipeline(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. Perfis e Personalidades Editoriais
CREATE TABLE IF NOT EXISTS editorial_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    archetype TEXT NOT NULL,
    tone TEXT NOT NULL,
    target_niches TEXT,
    hook_style TEXT,
    pacing_style TEXT,
    visual_style TEXT,
    catchphrases TEXT,
    prompt_modifiers TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. Laboratório de Experimentos A/B
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    variable_type TEXT NOT NULL,
    control_variant TEXT,
    test_variant TEXT,
    channel_id INTEGER REFERENCES channels(id),
    script_ids TEXT,
    metrics_control TEXT,
    metrics_test TEXT,
    status TEXT DEFAULT 'draft',
    winner TEXT,
    insights_learned TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    concluded_at TIMESTAMP
);

-- 15. Nós do Grafo de Conhecimento Central
CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_slug TEXT,
    node_type TEXT NOT NULL,
    title TEXT NOT NULL,
    pattern_data TEXT NOT NULL,
    sample_count INTEGER DEFAULT 1,
    effectiveness_score REAL DEFAULT 50.0,
    derived_from_references TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
