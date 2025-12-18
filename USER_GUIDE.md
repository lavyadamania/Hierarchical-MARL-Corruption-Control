# User Guide
## CorruptionMARL: Complete User Manual

**Version:** 1.0.0  
**Target Audience:** Researchers, Data Scientists, Students  
**Difficulty Level:** Intermediate to Advanced

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Interface Overview](#2-interface-overview)
3. [Training Workflow](#3-training-workflow)
4. [Physics Configuration](#4-physics-configuration)
5. [Data Analysis](#5-data-analysis)
6. [Troubleshooting](#6-troubleshooting)
7. [Best Practices](#7-best-practices)
8. [Advanced Usage](#8-advanced-usage)

---

## 1. Quick Start

### 1.1 First-Time Setup

```bash
# Navigate to project directory
cd CorruptionMARL_Complete

# Launch application
python app.py
```

**Expected Output:**
```
* Running on http://127.0.0.1:5000
* Debugger is active
```

### 1.2 Accessing the Dashboard

1. Open web browser
2. Navigate to `http://localhost:5000`
3. You should see the main dashboard with live corruption chart

### 1.3 Your First Training Run

**Step-by-Step:**

1. **Click ⚙ Physics** button (top-right)
2. **Select Quick Preset:** "50% - Balanced (Current)"
3. **Click X** to close physics panel
4. **Click ↻ Wipe Memory** (confirms fresh start)
5. **Click ▶ Start Season**
6. **Click 🚀 Turbo** for faster training
7. **Wait 30,000-50,000 episodes** for convergence
8. **Observe graph** trending toward ~50%

**Expected Result:** Corruption level stabilizes around 45-55% after convergence.

---

## 2. Interface Overview

### 2.1 Main Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│  [Logo] Corruption MARL System         [⚙][↻][▶][🚀]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │     CORRUPTION TREND OVER TIME (Live Chart)      │  │
│  │  60%┤                    ╱╲                       │  │
│  │  50%┤─────────────────╱──╯╲───────────────────  │  │
│  │  40%┤              ╱         ╲                    │  │
│  │  30%┤           ╱               ╲                 │  │
│  │  20%┤        ╱                     ╲              │  │
│  │  10%┤     ╱                           ╲           │  │
│  │   0%┴────────────────────────────────────────────│  │
│  │      0    10k   20k   30k   40k   50k Episodes   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─────────────┬─────────────┬─────────────┬─────────┐ │
│  │  Officer_1  │  Officer_2  │  Officer_3  │  IA     │ │
│  │  Corrupt    │  Corrupt    │  Corrupt    │  Active │ │
│  │  C: 78%     │  C: 45%     │  C: 92%     │  Cases: │ │
│  │  $45k       │  $23k       │  $67k       │  124    │ │
│  └─────────────┴─────────────┴─────────────┴─────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Control Buttons

| Button | Function | Hotkey |
|--------|----------|--------|
| ⚙ Physics | Configure environment parameters | `Ctrl+P` |
| ↻ Wipe Memory | Reset all learned strategies | `Ctrl+R` |
| ▶ Start Season | Begin training (5,000 episodes) | `Ctrl+S` |
| ⏸ Pause | Pause current training | `Ctrl+Space` |
| 🚀 Turbo | Toggle fast training (200-500 eps/sec) | `Ctrl+T` |
| 📊 Results | View historical data and analytics | `Ctrl+D` |

### 2.3 Status Indicators

**Live Metrics Bar:**
- **Episode:** Current training iteration
- **Corruption:** Real-time system-wide corruption percentage
- **IA Activity:** Number of investigations this session
- **Chief Actions:** Executions/Firings/Warnings count

---

## 3. Training Workflow

### 3.1 Standard Training Protocol

**Recommended Workflow for Reproducible Results:**

```
1. Configure Physics (Select target preset)
   ↓
2. Wipe Memory (Clean slate)
   ↓
3. Start Season (Begin training)
   ↓
4. Enable Turbo (Accelerate learning)
   ↓
5. Monitor Convergence (30k-50k episodes)
   ↓
6. Analyze Results (Review graph in Results panel)
   ↓
7. Export Data (Save for research/publication)
```

### 3.2 Training Phases

**Phase 1: Exploration (0-10,000 episodes)**
- **Behavior:** High variance, random strategies
- **Corruption:** Chaotic oscillation (0-100%)
- **ε (Exploration Rate):** 1.0 → 0.3
- **What's Happening:** Agents discovering action space

**Phase 2: Learning (10,000-25,000 episodes)**
- **Behavior:** Patterns emerge, overcorrection common
- **Corruption:** Large swings, trending toward target
- **ε:** 0.3 → 0.1
- **What's Happening:** Agents refining strategies

**Phase 3: Convergence (25,000+ episodes)**
- **Behavior:** Stable oscillation around target
- **Corruption:** Target ± 5-10%
- **ε:** 0.1 → 0.01
- **What's Happening:** Near-optimal policies learned

### 3.3 Convergence Indicators

**Signs of Successful Convergence:**

✅ Corruption graph shows stable horizontal trend  
✅ Oscillations reduce in amplitude over time  
✅ Average (rolling 1,000 eps) within target ± 10%  
✅ No crashes to 0% or spikes to 100%  
✅ IA detection rate stabilizes around 30-50%  

**Warning Signs (Non-Convergence):**

⚠️ Wild swings continuing beyond 30,000 episodes  
⚠️ Crashes to 0% in late training  
⚠️ Stagnation at wrong equilibrium (e.g., targeting 50%, stuck at 20%)  
⚠️ Increasing variance in late training  

---

## 4. Physics Configuration

### 4.1 Quick Preset System

**Purpose:** One-click configuration for different corruption equilibriums.

**Available Presets:**

| Preset | Target | Physics Profile | Use Case |
|--------|--------|----------------|----------|
| 🟢 20% | Very Low | Harsh enforcement (10% witness, -1000 penalty) | Studying strict institutional control |
| 🟡 35% | Low | Moderate enforcement (5% witness, -500 penalty) | Balanced corruption-efficiency trade-off |
| 🟠 50% | Balanced | Lenient enforcement (1% witness, -100 penalty) | Default demonstration scenario |
| 🟠 65% | High | Minimal enforcement (0.5% witness, -50 penalty) | Studying organizational decay |
| 🔴 80% | Very High | Almost no enforcement (0.1% witness, -20 penalty) | Extreme corruption scenarios |

**How to Use:**
1. Open Physics panel (⚙ button)
2. Select desired preset from dropdown
3. Confirm auto-configuration
4. **CRITICAL:** Wipe memory for clean results
5. Start new training run

### 4.2 Manual Parameter Tuning

**For Advanced Users:**

**🎯 Target Corruption (0-100%)**
- Sets Chief AI's control objective
- Does NOT guarantee this will be achieved
- Physics must support natural equilibrium near target

**💰 Bribe Multiplier (1-10x)**
- Scales officer reward for successful bribes
- Higher = more incentive to be corrupt
- Recommended: 5-8x for stable systems

**👀 Witness Risk (1-100%)**
- Base probability of detection per witness
- Lower = safer for officers → higher corruption
- Recommended: 1-5% for convergence

**⚖ Jail Penalty (-2000 to -100)**
- Punishment when officer caught
- More negative = stronger deterrent
- Recommended: -100 to -500

**😈 Spawn Corruption (1-100%)**
- Initial corruption for new officers
- Higher = starts corrupt → easier to maintain
- Recommended: 60-90%

### 4.3 Physics-Equilibrium Relationship

**Key Insight:** Target corruption is achievable only if natural equilibrium is higher.

**Formula:**
```
achievable_target = natural_equilibrium - Chief_suppression

Where:
    natural_equilibrium ≈ f(witness_risk, jail_penalty, bribe_mult)
    Chief_suppression ≈ 10-20% (learned through training)
```

**Example:**
```
Target: 50%
Required natural equilibrium: 60-70%
Physics needed:
    - Witness Risk: 1% (very safe)
    - Bribe Mult: 8x (very profitable)  
    - Jail Penalty: -100 (light)
    - Spawn: 80% (high)
```

---

## 5. Data Analysis

### 5.1 Results Dashboard

**Accessing Historical Data:**

1. Click **📊 Results** button
2. Select metric to visualize:
   - **Corruption:** System-wide corruption over time
   - **IA Activity:** Investigation frequency
   - **Chief Actions:** Execution/Fire/Warning distribution
   - **Officer Wealth:** Average accumulated bribes

3. View statistics:
   - Mean
   - Standard Deviation
   - Min/Max
   - Convergence Episode (when variance dropped below threshold)

### 5.2 Exporting Data

**For Research Publications:**

Data is automatically saved in SQLite database: `corruption.db`

**Query Examples:**

```sql
-- Get corruption trend
SELECT episode, corruption_level 
FROM episodes 
WHERE season_id = 1 
ORDER BY episode;

-- Get agent statistics
SELECT agent_type, AVG(corruption_score), AVG(total_money)
FROM agents
GROUP BY agent_type;

-- Get Chief's decision distribution
SELECT chief_action, COUNT(*)
FROM investigations
GROUP BY chief_action;
```

**Python Export:**

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('corruption.db')
df = pd.read_sql_query("SELECT * FROM episodes", conn)
df.to_csv('results.csv', index=False)
```

### 5.3 Interpreting Results

**Successful Run Characteristics:**

- **Convergence Time:** 25,000-40,000 episodes
- **Final Variance:** < 8% standard deviation
- **Hit Rate:** Within ±10% of target
- **Stability:** Horizontal trend in final 10,000 episodes

**Publication-Quality Metrics:**

- Report mean ± std over final 10,000 episodes
- Include convergence plot (episodes vs corruption)
- Document physics parameters used
- State random seed for reproducibility

---

## 6. Troubleshooting

### 6.1 Common Issues

**Problem: Corruption Crashes to 0%**

**Diagnosis:** Chief over-executing due to wrong reward signals or physics too harsh.

**Solution:**
1. Check physics: Witness risk should be 1-5%, not 10%+
2. Verify Chief's reward function (should NOT punish WARNING when low)
3. Wipe memory and retrain

---

**Problem: Stuck at Wrong Equilibrium**

**Diagnosis:** Natural equilibrium doesn't support target.

**Example:** Targeting 50%, stuck at 25%.

**Solution:**
1. Use Quick Preset instead of manual configuration
2. Lower witness risk (make corruption safer)
3. Increase bribe multiplier (make corruption more profitable)
4. Reduce jail penalty (make getting caught less painful)

---

**Problem: Wild Oscillations Never Stabilize**

**Diagnosis:** Exploration rate decaying too slowly or batch size too small.

**Solution:**
1. Check `EPSILON_DECAY` in `config.py` (should be 0.999)
2. Ensure training for 40,000+ episodes
3. Restart training with memory wipe

---

**Problem: Flask Server Crashes**

**Diagnosis:** Database lock or memory overflow.

**Solution:**
```bash
# Stop server (Ctrl+C)
# Delete database
rm corruption.db

# Restart
python app.py
```

---

### 6.2 Validation Checklist

Before reporting issues, verify:

- [ ] Memory was wiped before training
- [ ] Training ran for 30,000+ episodes
- [ ] Physics parameters are within recommended ranges
- [ ] Browser is up-to-date (Chrome/Firefox latest)
- [ ] No console errors in browser DevTools
- [ ] Python dependencies installed correctly

---

## 7. Best Practices

### 7.1 Research Experiment Design

**For Academic Research:**

1. **Define Hypothesis First**  
   Example: "Corruption level is inversely proportional to witness risk."

2. **Use Systematic Parameter Sweep**  
   ```python
   for witness_risk in [0.01, 0.03, 0.05, 0.10]:
       for bribe_mult in [3, 5, 8, 10]:
           run_experiment(witness_risk, bribe_mult, episodes=50000)
   ```

3. **Repeat Trials (N=3 minimum)**  
   Wipe memory and retrain 3 times per configuration for statistical significance.

4. **Document Everything**  
   - Random seed
   - Hyperparameters
   - Convergence criteria
   - Environmental conditions

### 7.2 Reproducibility Guidelines

**Minimum Requirements:**

- **Code Version:** Git commit hash
- **Python Version:** `python --version`
- **Dependencies:** `pip freeze > requirements.txt`
- **Random Seed:** Set in `config.py`
- **Physics Params:** Full configuration snapshot
- **Training Duration:** Exact episode count

**Recommended Practice:**

```python
# Add to top of app.py
import random, numpy as np, torch

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
```

### 7.3 Performance Optimization Tips

1. **Use Turbo Mode** for initial exploration (200-500 eps/sec)
2. **Disable Turbo** nearing convergence for detailed observation
3. **Batch database writes** in `config.py` (every 100 episodes)
4. **Enable GPU acceleration** if available (10x speedup)
5. **Close unused browser tabs** (WebSocket overhead)

---

## 8. Advanced Usage

### 8.1 Customizing Agent Behavior

**Modifying Reward Functions:**

Located in `agents/police_chief.py`:

```python
def calculate_reward(self, decision, ..., global_corruption):
    # Your custom reward logic here
    if some_condition:
        return custom_reward
```

**Example:** Add bonus for low variance:

```python
variance = np.std(recent_corruption_history)
bonus = -100 * variance  # Reward stability
return base_reward + bonus
```

### 8.2 Adding Custom Metrics

**Track New Metrics:**

1. Add to `simulation_engine.py`:
```python
self.custom_metric = []

# During training:
self.custom_metric.append(calculated_value)
```

2. Emit to frontend:
```python
socketio.emit('update_data', {
    'custom_metric': self.custom_metric[-1]
})
```

3. Update `index.html` to display

### 8.3 Batch Experimentation

**Automated Testing Script:**

```python
import subprocess
import time

configurations = [
    {'target': 20, 'witness': 0.10},
    {'target': 35, 'witness': 0.05},
    {'target': 50, 'witness': 0.01},
    # ... more configs
]

for config in configurations:
    # Update config.py
    update_config(config)
    
    # Run training
    subprocess.run(['python', 'main.py', '--episodes', '50000'])
    
    # Extract results
    results = analyze_database()
    save_results(config, results)
    
    # Wipe for next run
    subprocess.run(['rm', 'corruption.db'])
```

---

## Appendix: Quick Reference

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+P` | Open Physics |
| `Ctrl+R` | Wipe Memory |
| `Ctrl+S` | Start Season |
| `Ctrl+T` | Toggle Turbo |
| `Ctrl+D` | Results Dashboard |
| `Ctrl+Space` | Pause/Resume |

### Default File Locations

| File | Purpose |
|------|---------|
| `corruption.db` | Training data |
| `brains/` | Neural network weights |
| `results/` | Exported visualizations |
| `config.py` | Hyperparameters |

### Recommended Training Durations

| Objective | Episodes | Time (Turbo) |
|-----------|----------|--------------|
| Quick Demo | 5,000 | ~30 seconds |
| Initial Exploration | 10,000 | ~1 minute |
| Research Quality | 50,000 | ~4-5 minutes |
| Publication Quality | 100,000 | ~8-10 minutes |

---

**Document Version:** 1.0.0  
**Last Updated:** December 2024  
**Feedback:** GitHub [@lavyadamania](https://github.com/lavyadamania)
