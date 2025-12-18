-- Table 1: Cops (Agents)
CREATE TABLE IF NOT EXISTS cops (
    cop_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    cop_type TEXT NOT NULL, -- 'chief', 'detective', 'corrupt', 'honest'
    personality TEXT,       -- 'greedy', 'cautious', 'paranoid', 'none'
    rank TEXT NOT NULL,     -- 'chief', 'detective', 'constable'
    corruption_score REAL DEFAULT 0.0,
    paranoia_level REAL DEFAULT 0.0,
    loyalty_score REAL DEFAULT 100.0,
    times_bribed INTEGER DEFAULT 0,
    times_caught INTEGER DEFAULT 0,
    total_money_earned REAL DEFAULT 0.0,
    reports_filed INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Bribe History (Episodes)
CREATE TABLE IF NOT EXISTS bribe_history (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cop_id INTEGER,
    episode_number INTEGER,
    player_offer REAL,
    witness_count INTEGER,
    ia_nearby BOOLEAN,
    location_risk REAL,
    decision TEXT, -- 'ACCEPT', 'REJECT'
    outcome TEXT,  -- 'success', 'caught', 'rejected'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(cop_id) REFERENCES cops(cop_id)
);

-- Table 3: Trust Network
CREATE TABLE IF NOT EXISTS trust_network (
    relationship_id INTEGER PRIMARY KEY,
    cop_A_id INTEGER,
    cop_B_id INTEGER,
    trust_level REAL DEFAULT 0.5,
    shared_bribes INTEGER DEFAULT 0,
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(cop_A_id) REFERENCES cops(cop_id),
    FOREIGN KEY(cop_B_id) REFERENCES cops(cop_id)
);

-- Table 4: Investigations
CREATE TABLE IF NOT EXISTS investigations (
    investigation_id INTEGER PRIMARY KEY,
    investigator_id INTEGER,
    target_cop_id INTEGER,
    episode INTEGER,
    evidence_score REAL,
    status TEXT, -- 'open', 'active', 'closed'
    outcome TEXT, -- 'CONVICTED-FIRE', 'CONVICTED-SUSPEND', 'WARNING', 'INSUFFICIENT_EVIDENCE'
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    FOREIGN KEY(investigator_id) REFERENCES cops(cop_id),
    FOREIGN KEY(target_cop_id) REFERENCES cops(cop_id)
);

-- Table 5: Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    chief_id INTEGER,
    target_cop_id INTEGER,
    order_type TEXT, -- 'INVESTIGATE', 'SUSPEND', 'WARNING'
    order_details TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'completed'
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(chief_id) REFERENCES cops(cop_id),
    FOREIGN KEY(target_cop_id) REFERENCES cops(cop_id)
);

-- Table 6: Episode Stats (Global Tracking per Episode)
CREATE TABLE IF NOT EXISTS episode_stats (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_number INTEGER,
    total_bribes_accepted INTEGER,
    total_caught INTEGER,
    avg_corruption REAL
);
