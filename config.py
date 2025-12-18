import os

# System Constants
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, 'corruption.db')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')
BRAIN_DIR = os.path.join(PROJECT_ROOT, 'brains')

# Agent Counts
NUM_CORRUPT_COPS = 5
NUM_HONEST_COPS = 2
TOTAL_AGENTS = 1 + 1 + NUM_CORRUPT_COPS + NUM_HONEST_COPS  # Chief + IA + Corrupt + Honest

# Simulation Parameters
SEASON_LENGTH = 5000 
INSPECTION_FREQUENCY = 10  # IA checks periodically, not every episode (realistic)
ALERT_DECAY_RATE = 0.05

# Risk Factors - CORRUPTION-FRIENDLY DEFAULTS
WITNESS_RISK_FACTOR = 0.01       # 1% chance (was 0.05 = 5%)
IA_RISK_MULTIPLIER = 0.20        
LOCATION_RISK_WEIGHT = 0.10      

# AI Targets
TARGET_CORRUPTION_LEVEL = 50 # The Chief tries to maintain this %
      

# Hyperparameters (RL) - Optimized for Web App Performance
LR = 0.001
ALPHA = LR # Alias
GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_END = 0.01
EPSILON_MIN = EPSILON_END # Alias
EPSILON_DECAY = 0.999  # Faster decay for quicker convergence (was 0.9995)
BATCH_SIZE = 32  # Reduced from 64 for faster training
MEMORY_SIZE = 10000
HIDDEN_DIM = 64  # Reduced from 128 for faster computation
TARGET_UPDATE_FREQ = 200  # Increased from 100 to reduce overhead

# Dimensions
# Corrupt Cop: 14 Dim (10 RPG + 4 Memory)
# Chief: 6 Dim (was 5, now includes global_corruption and target_error)
CHIEF_STATE_DIM = 6
CHIEF_ACTION_DIM = 3 # Execute, Fire, Warning
CHIEF_ACTIONS_NAMES = ['EXECUTE', 'FIRE', 'WARNING']

# IA: 5 Dim - SIMPLIFIED to binary decision
IA_STATE_DIM = 5
IA_ACTION_DIM = 2  # Ignore or Send to Chief (was 3)
IA_ACTIONS_NAMES = ['IGNORE', 'SEND_TO_CHIEF']  # Simplified!
EVIDENCE_THRESHOLD = 50 

# Action Space (Corrupt Cop)
ACTIONS = [
    'ARREST', 'INVESTIGATE', 'DE_ESCALATE', 'ISSUE_TICKET', 'REPORT_BRIBE', 
    'REQUEST_WARRANT', 'WHISTLEBLOW', 
    'ACCEPT_BRIBE', 'EXTORT', 'PLANT_EVIDENCE', 'TIP_OFF', 'DESTROY_EVIDENCE', 
    'INTIMIDATE_WITNESS', 'STEAL_SEIZED', 'EXCESSIVE_FORCE', 'ISOLATE_SUSPECT'
]
ACTION_DIM = len(ACTIONS)

# RPG Crime Types (Severity, BaseValMin, BaseValMax)
CRIME_TYPES = {
    'Speeding': (1, 50, 200),
    'Jaywalking': (1, 10, 50),
    'Shoplifting': (2, 50, 500),
    'Vandalism': (3, 100, 1000),
    'Drunk_Driving': (5, 500, 5000),
    'Assault': (6, 500, 2000),
    'Burglary': (7, 1000, 10000),
    'Drug_Dealing': (8, 2000, 50000),
    'Armed_Robbery': (9, 5000, 100000),
    'Murder': (10, 10000, 1000000)
}

# Rewards (The Incentive Structure) 
REWARD_SUCCESS_FACTOR = 5.0     
REWARD_CAUGHT = -200            
REWARD_KILLED = -2000           

# Action Specific Rewards
REWARD_ARREST = 50
REWARD_INVESTIGATE = 10
REWARD_DE_ESCALATE = 20
REWARD_TICKET = 15
REWARD_REPORT = 30
REWARD_WARRANT = 10
REWARD_WHISTLEBLOW = 100
REWARD_EXTORT = 500 # Plus value
REWARD_FRAME = 200
REWARD_TIP_OFF = 150
REWARD_DESTROY = 100
REWARD_INTIMIDATE = 100
REWARD_STEAL = 0 # Value based
REWARD_BRUTALITY = 50 # Satisfaction?
REWARD_ISOLATE = 20

# Initial Values
INITIAL_INTEGRITY_HONEST = 90
INITIAL_CORRUPTION_MIN = 60      
INITIAL_CORRUPTION_MAX = 90      

# Visualization Settings
DPI = 250
FIG_SIZE_WIDE = (10, 6)
FIG_SIZE_SQUARE = (8, 8)

# Stats for Updating Agent State
CORRUPTION_GAIN_SUCCESS = 2.0
CORRUPTION_LOSS_CAUGHT = -10.0
PARANOIA_GAIN_CAUGHT = 0.2
LOYALTY_LOSS_CAUGHT = -5.0
