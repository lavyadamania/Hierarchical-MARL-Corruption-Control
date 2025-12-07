import random
import numpy as np
import pickle
import os
from collections import defaultdict
from config import (
    WITNESS_RISK_FACTOR, IA_RISK_MULTIPLIER, LOCATION_RISK_WEIGHT,
    CORRUPTION_GAIN_SUCCESS, CORRUPTION_LOSS_CAUGHT,
    PARANOIA_GAIN_CAUGHT, PARANOIA_LOSS_SUCCESS, LOYALTY_LOSS_CAUGHT,
    ALPHA, GAMMA, EPSILON_START, EPSILON_MIN, EPSILON_DECAY,
    BRAIN_DIR
)

class CorruptCop:
    def __init__(self, agent_id, name, personality, corruption_score):
        self.agent_id = agent_id
        self.name = name
        self.cop_type = 'corrupt'
        self.rank = 'constable'
        self.personality = personality
        self.corruption_score = corruption_score
        self.paranoia_level = 0.0
        self.loyalty_score = 100.0
        
        # Stats
        self.times_bribed = 0
        self.times_caught = 0
        self.total_money_earned = 0.0
        
        # Q-Learning State
        self.q_table = defaultdict(float) 
        self.epsilon = EPSILON_START
        self.last_state = None
        self.last_action = None
        
        # Load existing brain if available
        self.load_brain()

    def get_state_key(self, state):
        """
        Discretizes state for Q-Learning.
        Tuple: (Witness_Level, IA_Present, Offer_Level, Severity_Level, Alert_Level)
        """
        w_state = 0 if state['witnesses'] == 0 else 1
        ia_state = 1 if state['ia_nearby'] else 0
        offer_state = 0 if state['offer'] < 5000 else 1
        
        # Severity: 0 (Low < 5), 1 (High >= 5)
        sev_state = 0 if state['severity'] < 5 else 1

        # Alert Level: 0 (Safe < 0.3), 1 (Heat >= 0.3)
        alert_state = 0 if state.get('alert_level', 0) < 0.3 else 1
        
        return (w_state, ia_state, offer_state, sev_state, alert_state)

    def decide_bribe(self, state):
        state_key = self.get_state_key(state)
        self.last_state = state_key
        
        actions = ['ACCEPT', 'REJECT', 'CLEAN_AND_ACCEPT']
        
        # Exploration vs Exploitation
        if random.random() < self.epsilon:
            action = random.choice(actions)
        else:
            # Find best action
            vals = [self.q_table[(state_key, a)] for a in actions]
            max_val = max(vals)
            # Handle ties randomly
            best_actions = [a for a, v in zip(actions, vals) if v == max_val]
            action = random.choice(best_actions)
        
        self.last_action = action
        return action

    def learn(self, reward, next_state_raw=None):
        if self.last_state is None or self.last_action is None:
            return

        state = self.last_state
        action = self.last_action
        
        # Max Q for next state (assuming next random scenario is the 'next state')
        if next_state_raw:
            next_s = self.get_state_key(next_state_raw)
            actions = ['ACCEPT', 'REJECT', 'CLEAN_AND_ACCEPT']
            max_next_q = max([self.q_table[(next_s, a)] for a in actions])
        else:
            max_next_q = 0

        current_q = self.q_table[(state, action)]
        new_q = current_q + ALPHA * (reward + GAMMA * max_next_q - current_q)
        self.q_table[(state, action)] = new_q
        
        if self.epsilon > EPSILON_MIN:
            self.epsilon *= EPSILON_DECAY

    def update_stats(self, outcome, offer):
        """Updates internal stats and corruption score."""
        if outcome == 'success':
            self.corruption_score = min(100, self.corruption_score + CORRUPTION_GAIN_SUCCESS)
            self.paranoia_level = max(0.0, self.paranoia_level + PARANOIA_LOSS_SUCCESS)
            self.total_money_earned += offer
            self.times_bribed += 1
            
        elif outcome == 'caught':
            self.corruption_score = max(0, self.corruption_score + CORRUPTION_LOSS_CAUGHT)
            self.paranoia_level = min(1.0, self.paranoia_level + PARANOIA_GAIN_CAUGHT)
            self.loyalty_score = max(0, self.loyalty_score + LOYALTY_LOSS_CAUGHT)
            self.times_caught += 1

    def save_brain(self):
        """Saves Q-table and epsilon to disk."""
        if not os.path.exists(BRAIN_DIR):
            os.makedirs(BRAIN_DIR)
            
        filename = os.path.join(BRAIN_DIR, f"cop_{self.agent_id}.pkl")
        with open(filename, 'wb') as f:
            pickle.dump({
                'q_table': dict(self.q_table),
                'epsilon': self.epsilon
            }, f)

    def load_brain(self):
        """Loads Q-table from disk if it exists."""
        filename = os.path.join(BRAIN_DIR, f"cop_{self.agent_id}.pkl")
        if os.path.exists(filename):
            try:
                with open(filename, 'rb') as f:
                    data = pickle.load(f)
                    self.q_table = defaultdict(float, data.get('q_table', {}))
                    self.epsilon = data.get('epsilon', EPSILON_START)
            except Exception as e:
                print(f"Error loading brain for {self.name}: {e}")

    def inherit_brain(self, source_file_path):
        """
        Loads Q-table from a dead agent's file.
        """
        if os.path.exists(source_file_path):
            with open(source_file_path, 'rb') as f:
                data = pickle.load(f)
                # Handle both old format (direct dict) and new format (wrapper dict) if needed
                # But we know save_brain uses wrapper dict
                if 'q_table' in data:
                    self.q_table = defaultdict(float, data['q_table'])
                else:
                    self.q_table = defaultdict(float, data)
                    
            # Adjust epsilon slightly higher to allow the new recruit to experiment 
            # a bit with the new knowledge, but mostly exploit.
            self.epsilon = max(self.epsilon, EPSILON_MIN + 0.1) 
            print(f"🧠 {self.name} successfully inherited brain from {os.path.basename(source_file_path)}")
        else:
            print(f"⚠️ Failed to inherit brain: {source_file_path} not found")

    def __repr__(self):
        return f"CorruptCop(#{self.agent_id}, {self.personality}, C:{self.corruption_score:.1f}, ε:{self.epsilon:.2f})"
