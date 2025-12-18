# Technical Specification
## CorruptionMARL: Architectural Design and Implementation Details

**Document Version:** 1.0  
**Last Updated:** December 2024  
**Classification:** Technical Reference

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Agent Design](#2-agent-design)
3. [Learning Algorithms](#3-learning-algorithms)
4. [Environment Specification](#4-environment-specification)
5. [Data Models](#5-data-models)
6. [API Reference](#6-api-reference)
7. [Performance Optimization](#7-performance-optimization)

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Web Interface Layer                     │
│  (Flask + Socket.IO + Chart.js + WebSocket Streaming)    │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│              Simulation Engine Layer                      │
│  - Episode Management    - Agent Coordination             │
│  - Hierarchy Enforcement - Event Logging                  │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│               Multi-Agent RL Layer                        │
│  ┌─────────────┬──────────────┬─────────────┐           │
│  │ Police      │  IA          │ Police      │           │
│  │ Officers    │  Detective   │ Chief       │           │
│  │ (5 x DQN)   │  (1 x DQN)   │ (1 x DQN)   │           │
│  └─────────────┴──────────────┴─────────────┘           │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│            Environment & Physics Layer                    │
│  - Scenario Generation   - Outcome Resolution            │
│  - Risk Calculation      - Reward Computation             │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│              Persistence Layer                            │
│  - SQLite Database  - Neural Network Weights             │
│  - Episode History  - Performance Metrics                 │
└──────────────────────────────────────────────────────────┘
```

### 1.2 Component Interaction Diagram

```
[Web Client] ←→ [Flask Server] ←→ [Simulation Engine]
                                         ↓
                            [Chief AI] ← [IA Detective]
                               ↓              ↓
                            [Police Officers (5x)]
                                     ↓
                            [Environment Physics]
                                     ↓
                            [Database Manager]
```

### 1.3 Design Patterns

- **Model-View-Controller (MVC):** Separation of agent logic, UI, and coordination
- **Observer Pattern:** Real-time WebSocket updates for UI synchronization  
- **Strategy Pattern:** Polymorphic agent decision-making
- **Factory Pattern:** Dynamic agent creation and replacement
- **Repository Pattern:** Database abstraction layer

---

## 2. Agent Design

### 2.1 Police Officer Agent

**Purpose:** Operational-level decision-making for individual criminal interactions.

**State Space (14 dimensions):**

| Dimension | Range | Description |
|-----------|-------|-------------|
| `bribe_amount` | [0, 1] | Normalized bribe offer value |
| `witness_risk` | [0, 1] | Probability of witness detection |
| `suspect_threat` | [0, 1] | Danger level from suspect |
| `illegal_severity` | [0, 1] | Crime severity (normalized) |
| `officer_need` | [0, 1] | Financial need level |
| `location_exposure` | [0, 1] | Public visibility of location |
| `time_of_day` | [0, 1] | Time-based risk factor |
| `backup_nearby` | {0, 1} | Presence of backup |
| `evidence_present` | [0, 1] | Evidence strength |
| `civilian_witnesses` | [0, 1] | Number of civilians (normalized) |
| `corruption_score` | [0, 1] | Agent's current corruption level |
| `times_caught` | [0, 1] | Historical catch count (normalized) |
| `total_money` | [0, 1] | Accumulated wealth (normalized) |
| `last_reward` | [-1, 1] | Previous episode reward (normalized) |

**Action Space:**
- `HONEST`: Perform duty according to protocol
- `ACCEPT_BRIBE`: Take bribe and release suspect
- `IGNORE`: Take no action

**Reward Function:**
```python
R(s, a) = {
    bribe * multiplier     if a = ACCEPT_BRIBE and ¬caught
    jail_penalty           if a = ACCEPT_BRIBE and caught
    base_salary            if a = HONEST
}
```

### 2.2 IA Detective Agent

**Purpose:** Mid-level supervision and corruption detection.

**State Space (5 dimensions):**

| Dimension | Range | Description |
|-----------|-------|-------------|
| `corruption_estimate` | [0, 1] | Noisy observation of officer corruption |
| `wealth_visible` | [0, 1] | Observable wealth accumulation |
| `times_caught` | [0, 1] | Historical violations |
| `loyalty_score` | [0, 1] | Department tenure and reliability |
| `global_alert` | [0, 1] | System-wide corruption indicator |

**Action Space:**
- `IGNORE`: Take no action on this officer
- `SEND_TO_CHIEF`: Refer case to strategic decision-maker

**Reward Function:**
```python
R(s, a) = {
    +100    if a = SEND_TO_CHIEF and officer.corruption > 50%
    -50     if a = SEND_TO_CHIEF and officer.corruption ≤ 50%
    +5      if a = IGNORE and officer.corruption ≤ 60%
    -20     if a = IGNORE and officer.corruption > 60%
}
```

### 2.3 Police Chief Agent

**Purpose:** Strategic-level institutional corruption control.

**State Space (6 dimensions):**

| Dimension | Range | Description |
|-----------|-------|-------------|
| `evidence_strength` | [0, 1] | Case evidence quality |
| `times_caught` | [0, 1] | Officer violation history |
| `loyalty` | [0, 1] | Officer loyalty score |
| `individual_corruption` | [0, 1] | Target officer corruption |
| **`global_corruption`** | [0, 1] | **System-wide corruption level** |
| **`target_error`** | [-1, 1] | **Deviation from target corruption** |

**Action Space:**
- `EXECUTE`: Remove officer and replace with new agent
- `FIRE`: Demote officer (reduces corruption)
- `WARNING`: Issue warning (minimal effect)

**Reward Function (Control Theory):**

```python
def calculate_reward(decision, global_corruption, target):
    error = global_corruption - target
    tolerance = 5.0
    
    if error > tolerance:  # Too corrupt
        if decision == EXECUTE: return 500 + (error * 10)
        if decision == FIRE: return 200 + (error * 5)
        if decision == WARNING: return -500
    
    elif error < -tolerance:  # Too honest
        if decision == EXECUTE: return -500 * abs(error/10)
        if decision == WARNING: return 300 + (abs(error) * 20)
        if decision == FIRE: return 100
    
    else:  # On target
        return 100
```

---

## 3. Learning Algorithms

### 3.1 Deep Q-Network Architecture

**Neural Network Specification:**

```python
class DQN(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim=64):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
    
    def forward(self, x):
        return self.network(x)
```

**Layer Dimensions:**
- Input Layer: Variable (5D, 6D, or 14D based on agent)
- Hidden Layer: 64 neurons with ReLU activation
- Output Layer: 2-3 neurons (Q-values for each action)

**Justification for Architecture:**
- Single hidden layer provides sufficient capacity for this domain
- 64 neurons balances expressiveness and computational efficiency
- ReLU activation prevents vanishing gradients
- No dropout required due to limited training data size

### 3.2 Training Algorithm

**Experience Replay:**

```python
Memory = Deque(maxlen=10,000)
Batch_Size = 32

For each episode:
    Observe state s
    Select action a using ε-greedy policy
    Execute action, receive reward r
    Store transition (s, a, r, s') in Memory
    
    If len(Memory) >= Batch_Size:
        Sample random batch B from Memory
        Compute Q-targets using target network
        Update policy network via gradient descent
```

**Target Network Update:**

```python
Every TARGET_UPDATE_FREQ episodes:
    target_net.load_state_dict(policy_net.state_dict())
```

**Exploration Strategy:**

```python
ε(t) = max(EPSILON_MIN, EPSILON_START * EPSILON_DECAY^t)

where:
    EPSILON_START = 1.0   # Initial exploration
    EPSILON_MIN = 0.01    # Minimum exploration  
    EPSILON_DECAY = 0.999 # Decay rate per episode
```

### 3.3 Convergence Criteria

System is considered converged when:

1. **Rolling Average Stability:**  
   `|avg(corruption[t-1000:t]) - target| < 5%` for 5,000 consecutive episodes

2. **Variance Constraint:**  
   `std(corruption[t-1000:t]) < 8%` over 5,000 episodes

3. **Policy Stability:**  
   `ε < 0.1` (exploration has sufficiently decayed)

---

## 4. Environment Specification

### 4.1 Scenario Generation

Scenarios are procedurally generated each episode:

```python
class Scenario:
    crime_type: str          # Randomly selected from CRIME_TYPES
    severity: int            # 1-10 scale
    bribe_offer: float       # Based on severity and suspect wealth
    witnesses: int           # 0-4 witnesses present
    ia_nearby: bool          # IA proximity flag
    evidence_strength: float # 0.0-1.0
    has_warrant: bool        # Arrest warrant exists
    gang_affiliated: bool    # Suspect gang membership
    seized_value: float      # Potential asset seizure
    suspect_aggression: float # 0.0-1.0
    location_risk: float     # 0.0-1.0
```

### 4.2 Physics Parameters

**Configurable Environmental Variables:**

| Parameter | Range | Default | Effect |
|-----------|-------|---------|--------|
| `WITNESS_RISK_FACTOR` | [0.001, 0.10] | 0.01 | Base detection probability per witness |
| `BRIBE_MULTIPLIER` | [1, 10] | 8 | Reward scaling for successful bribes |
| `JAIL_PENALTY` | [-2000, -20] | -100 | Punishment for being caught |
| `SPAWN_CORRUPTION` | [1, 100] | 80 | Initial corruption for new officers |
| `TARGET_CORRUPTION` | [0, 100] | 50 | Desired system-wide corruption level |
| `INSPECTION_FREQUENCY` | [1, 20] | 10 | Episodes between IA checks |

### 4.3 Risk Calculation

Total detection risk is computed as:

```python
risk = (
    witness_count * WITNESS_RISK_FACTOR +
    (0.5 if ia_nearby else 0) +
    location_risk * LOCATION_RISK_WEIGHT +
    global_alert * ALERT_MULTIPLIER
)

caught = random() < risk
```

---

## 5. Data Models

### 5.1 Database Schema

**Episodes Table:**
```sql
CREATE TABLE episodes (
    id INTEGER PRIMARY KEY,
    season_id INTEGER,
    corruption_level REAL,
    avg_reward REAL,
    chief_actions TEXT,
    ia_actions TEXT,
    timestamp DATETIME
);
```

**Agents Table:**
```sql
CREATE TABLE agents (
    agent_id INTEGER PRIMARY KEY,
    agent_type TEXT,
    corruption_score REAL,
    total_money REAL,
    times_caught INTEGER,
    created_episode INTEGER,
    executed_episode INTEGER
);
```

**Investigations Table:**
```sql
CREATE TABLE investigations (
    id INTEGER PRIMARY KEY,
    episode INTEGER,
    target_cop_id INTEGER,
    ia_action TEXT,
    chief_action TEXT,
    outcome TEXT,
    FOREIGN KEY(target_cop_id) REFERENCES agents(agent_id)
);
```

### 5.2 Neural Network Persistence

**Brain File Format:**
```
brains/
├── cop_1.pth       # PyTorch state dict for officer 1
├── cop_2.pth        
├── cop_3.pth
├── cop_4.pth
├── cop_5.pth
├── ia_brain.pth    # IA detective weights
└── chief_brain.pth # Police chief weights
```

**Weight Transfer Protocol:**
```python
def transfer_brain(source_id, target_id):
    weights = torch.load(f"brains/cop_{source_id}.pth")
    target_agent.policy_net.load_state_dict(weights)
    target_agent.target_net.load_state_dict(weights)
```

---

## 6. API Reference

### 6.1 REST Endpoints

**Training Control:**

```http
POST /start_simulation
Body: { "episodes": 50000, "turbo": true }
Response: { "status": "started", "season_id": 1}
```

```http
POST /stop_simulation
Response: { "status": "stopped", "episodes_completed": 12543 }
```

```http
POST /reset_simulation
Response: { "status": "reset", "brains_deleted": 7, "db_cleared": true }
```

**Configuration:**

```http
POST /update_setting
Body: { 
    "key": "WITNESS_RISK_FACTOR", 
    "value": 0.01 
}
Response: { "success": true }
```

**Data Retrieval:**

```http
GET /results?metric=corruption&window=1000
Response: {
    "data": [45.2, 48.1, 49.3, ...],
    "avg": 47.5,
    "std": 3.2
}
```

### 6.2 WebSocket Events

**Client → Server:**

```javascript
socket.emit('start_simulation', {});
socket.emit('stop_simulation', {});
socket.emit('reset_simulation', {});
socket.emit('execute_agent', { id: 3 });
socket.emit('toggle_turbo', { enabled: true });
socket.emit('update_settings', { 
    setting: 'TARGET_CORRUPTION_LEVEL', 
    value: 65 
});
```

**Server → Client:**

```javascript
socket.on('update_data', (data) => {
    // data: { corruption, episode, agents, events }
});

socket.on('season_complete', (data) => {
    // data: { episodes, final_corruption, convergence }
});

socket.on('system_message', (msg) => {
    // msg: "Training started", "Memory wiped", etc.
});
```

---

## 7. Performance Optimization

### 7.1 Turbo Mode

**Mechanism:**
- Disables real-time visualization updates
- Batch database writes (every 100 episodes)
- Reduces Socket.IO emission frequency
- Achieves 200-500 episodes/second (vs 10-20 normal)

**Implementation:**
```python
if turbo_mode:
    emit_frequency = 100  # Update UI every 100 episodes
    db_batch_size = 100   # Batch insert episodes
else:
    emit_frequency = 1
    db_batch_size = 1
```

### 7.2 Memory Management

**Brain Saving Strategy:**
```python
# Save every TARGET_UPDATE_FREQ episodes
if episode % 200 == 0:
    for agent in all_agents:
        agent.save_brain()
```

**Database Indexing:**
```sql
CREATE INDEX idx_episodes_season ON episodes(season_id);
CREATE INDEX idx_agents_type ON agents(agent_type);
CREATE INDEX idx_investigations_episode ON investigations(episode);
```

### 7.3 Computational Complexity

**Per Episode:**
- Officer decisions: O(5 × forward_pass) = O(5 × 64) = O(320)
- IA decision: O(1 × forward_pass) = O(64)
- Chief decision: O(1 × forward_pass) if IA sends case = O(64)
- Learning updates: O(batch_size × backprop) = O(32 × 128) = O(4096)

**Total:** O(5000) per episode (highly efficient)

---

## 8. Deployment Considerations

### 8.1 System Requirements

**Minimum:**
- Python 3.8+
- 4GB RAM
- 1GB disk space
- Modern web browser

**Recommended:**
- Python 3.10+
- 8GB RAM
- CUDA-capable GPU (optional, 10x speedup)
- Chrome/Firefox (latest)

### 8.2 Scalability

**Horizontal Scaling Options:**
1. Distributed training across multiple machines
2. Parallel season execution
3. Cloud deployment (AWS, GCP, Azure)

**Vertical Scaling:**
1. GPU acceleration (PyTorch CUDA support)
2. Larger batch sizes with more RAM
3. Increased hidden layer dimensions

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **DQN** | Deep Q-Network, a value-based RL algorithm |
| **MARL** | Multi-Agent Reinforcement Learning |
| **Experience Replay** | Technique to break correlation in training data |
| **Target Network** | Stabilization mechanism using delayed weight updates |
| **ε-greedy** | Exploration strategy balancing random and optimal actions |
| **Corruption Score** | Agent-level metric (0-100) of corrupt behavior |
| **Global Corruption** | System-wide average corruption across all officers |

---

**Document Maintained By:** Technical Architecture Team  
**Review Cycle:** Quarterly  
**Classification:** Internal Technical Reference
