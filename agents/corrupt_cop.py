import random
import math
import numpy as np
import os
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque, namedtuple
from agents.dqn_model import DQN
import config

# Define Transition tuple for Replay Memory
Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward'))

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
        self.last_caught_episode = -100 # Long time ago initially
        
        # DQN Setup
        self.input_dim = 14 # 14-Dim State (RPG + Memory)
        self.output_dim = config.ACTION_DIM # 15 Actions
        
        # Device Check
        self.device = torch.device("cpu")
        
        self.policy_net = DQN(self.input_dim, self.output_dim, config.HIDDEN_DIM).to(self.device)
        self.target_net = DQN(self.input_dim, self.output_dim, config.HIDDEN_DIM).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=config.ALPHA)
        self.memory = deque(maxlen=config.MEMORY_SIZE)
        
        self.epsilon = config.EPSILON_START
        self.steps_done = 0
        
        self.last_state = None
        self.last_action = None

        # Try to load existing brain
        self.load_brain()

    def get_state_vector(self, state, current_episode):
        """
        Converts state dictionary to Normalized Tensor (14-Dim).
        Original 10 + 4 Memory Features:
        [Wit, IA, Off, Sev, Alert, Evid, War, Gang, Seized, Aggr] + 
        [Hist_Caught, Hist_Wealth, Recency_Caught, Suspicion]
        """
        # --- Original RPG Features (10) ---
        w_norm = min(state['witnesses'] / 5.0, 1.0)
        ia_val = 1.0 if state['ia_nearby'] else 0.0
        # 3. Offer (Logarithmic Norm) - Fix for 'Blind Billionaire'
        # Previously clipped at 500k. Now handles up to 100M+
        # log10(1) = 0. log10(50,000,000) ~ 7.7. Division by 8 scales it nicely to 0-1 range.
        offer_val = max(1.0, state['offer'])
        offer_norm = min(math.log10(offer_val) / 8.0, 1.0) 

        # 4. Severity (Norm)
        sev_norm = state['severity'] / 10.0
        # 5. Alert (Norm)
        alert_val = state.get('alert_level', 0.0)
        # 6. Evidence (Norm)
        ev_norm = state.get('evidence_strength', 0.5)
        # 7. Warrant (Bool)
        war_val = 1.0 if state.get('has_warrant') else 0.0
        # 8. Gang (Bool)
        gang_val = 1.0 if state.get('gang_affiliated') else 0.0
        
        # 9. Seized Value (Log Norm)
        seized_val = max(1.0, state.get('seized_value', 0))
        seized_norm = min(math.log10(seized_val) / 8.0, 1.0)
        
        # 10. Aggression (Norm)
        aggr_norm = state.get('suspect_aggression', 0.1)
        
        # --- New Memory Features (4) ---
        # 11. History Caught (Normalized): "Do I have a record?"
        caught_norm = min(self.times_caught / 5.0, 1.0)
        
        # 12. History Wealth (Log Norm) - Fix for 'Blind Billionaire'
        wealth_val = max(1.0, self.total_money_earned)
        wealth_norm = min(math.log10(wealth_val) / 8.0, 1.0)
        
        # 13. Recency Bias: "Was I caught recently?" (1.0 = Just caught, 0.0 = Long time ago)
        # Decay over 500 episodes
        episodes_since_caught = current_episode - self.last_caught_episode
        recency_val = max(0.0, 1.0 - (episodes_since_caught / 500.0))
        
        # 14. Suspicion Level (Approximate internal feeling)
        # Based on corruption score + paranoia
        suspicion_val = min((self.corruption_score + (self.paranoia_level * 100)) / 200.0, 1.0)

        return torch.tensor([
            w_norm, ia_val, offer_norm, sev_norm, alert_val,
            ev_norm, war_val, gang_val, seized_norm, aggr_norm,
            caught_norm, wealth_norm, recency_val, suspicion_val
        ], dtype=torch.float32).to(self.device)

    def decide_bribe(self, state, current_episode=0):
        state_tensor = self.get_state_vector(state, current_episode)
        self.last_state = state_tensor
        
        if random.random() < self.epsilon:
            action_idx = random.randint(0, self.output_dim - 1)
        else:
            with torch.no_grad():
                # Policy Net -> Q-Values -> Argmax
                q_values = self.policy_net(state_tensor.unsqueeze(0))
                action_idx = q_values.argmax().item()
        
        self.last_action = action_idx
        return config.ACTIONS[action_idx]

    def learn(self, reward, current_episode=0, next_state_raw=None):
        if self.last_state is None or self.last_action is None:
            return

        # Store Transition in Memory
        action_tensor = torch.tensor([[self.last_action]], device=self.device)
        reward_tensor = torch.tensor([reward], device=self.device)
        
        if next_state_raw:
            next_state_tensor = self.get_state_vector(next_state_raw, current_episode)
        else:
            next_state_tensor = None

        self.memory.append(Transition(self.last_state, action_tensor, next_state_tensor, reward_tensor))
        
        # Optimize Model
        self.optimize_model()
        
        # Epsilon Decay
        if self.epsilon > config.EPSILON_MIN:
            self.epsilon *= config.EPSILON_DECAY

    def optimize_model(self):
        if len(self.memory) < config.BATCH_SIZE:
            return
            
        transitions = random.sample(self.memory, config.BATCH_SIZE)
        batch = Transition(*zip(*transitions))

        # Compute a mask of non-final states
        non_final_mask = torch.tensor(tuple(map(lambda s: s is not None, batch.next_state)), device=self.device, dtype=torch.bool)
        
        valid_next_states = [s for s in batch.next_state if s is not None]
        non_final_next_states = torch.stack(valid_next_states) if len(valid_next_states) > 0 else None
        
        state_batch = torch.stack(batch.state)
        action_batch = torch.cat(batch.action)
        reward_batch = torch.cat(batch.reward)

        # Compute Q(s, a)
        state_action_values = self.policy_net(state_batch).gather(1, action_batch)

        # Compute V(s_{t+1}) for all next states.
        next_state_values = torch.zeros(config.BATCH_SIZE, device=self.device)
        
        if non_final_next_states is not None:
            next_state_values[non_final_mask] = self.target_net(non_final_next_states).max(1)[0].detach()
            
        # Compute the expected Q values
        expected_state_action_values = (next_state_values * config.GAMMA) + reward_batch

        # Compute Huber Loss
        criterion = nn.SmoothL1Loss()
        loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        for param in self.policy_net.parameters():
            param.grad.data.clamp_(-1, 1) # Gradient Clipping
        self.optimizer.step()
        
        # Update Target Network periodically
        self.steps_done += 1
        if self.steps_done % config.TARGET_UPDATE_FREQ == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

    def update_stats(self, outcome, offer, current_episode=0):
        """Updates internal stats and corruption score."""
        # Simple Logic: Any 'success' means they did something (lawful or unlawful)
        # But here we track corruption.
        
        if 'success' in outcome:
            # Check if action was corrupt (Indices 7-14 in ACTIONS list)
            # We don't have index here easily, but we know names.
            is_corrupt_act = outcome not in ['arrest_success', 'investigate_success', 'de_escalate_success', 'ticket_success', 'report_success', 'warrant_success', 'whistleblow_success']
            
            if is_corrupt_act:
                self.corruption_score = min(100, self.corruption_score + config.CORRUPTION_GAIN_SUCCESS)
                self.times_bribed += 1 # "Bribed" now means "Corrupt Act"
                
                # Money Logic
                bribe_amount = offer if offer > 0 else 1000 # Default if abstract
                self.total_money_earned += bribe_amount
            
        elif outcome == 'caught':
            self.corruption_score = max(0, self.corruption_score + config.CORRUPTION_LOSS_CAUGHT)
            self.paranoia_level = min(1.0, self.paranoia_level + config.PARANOIA_GAIN_CAUGHT)
            self.loyalty_score = max(0, self.loyalty_score + config.LOYALTY_LOSS_CAUGHT)
            self.times_caught += 1
            self.last_caught_episode = current_episode

    def save_brain(self):
        """Saves Neural Network Weights to disk."""
        if not os.path.exists(config.BRAIN_DIR):
            os.makedirs(config.BRAIN_DIR)
            
        filename = os.path.join(config.BRAIN_DIR, f"cop_{self.agent_id}.pth")
        torch.save({
            'model_state_dict': self.policy_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, filename)

    def load_brain(self):
        """Loads Neural Network from disk if it exists."""
        filename = os.path.join(config.BRAIN_DIR, f"cop_{self.agent_id}.pth")
        if os.path.exists(filename):
            try:
                checkpoint = torch.load(filename)
                # Architecture check handled by try/except usually
                self.policy_net.load_state_dict(checkpoint['model_state_dict'])
                self.target_net.load_state_dict(self.policy_net.state_dict())
                self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                self.epsilon = checkpoint.get('epsilon', config.EPSILON_START)
                self.policy_net.eval()
            except Exception as e:
                # print(f"Error loading brain for {self.name}: {e}")
                pass 

    def inherit_brain(self, source_file_path):
        if os.path.exists(source_file_path):
            try:
                checkpoint = torch.load(source_file_path)
                self.policy_net.load_state_dict(checkpoint['model_state_dict'])
                self.target_net.load_state_dict(self.policy_net.state_dict())
                self.epsilon = max(checkpoint.get('epsilon', 1.0), 0.1) 
                print(f"🧠 {self.name} inherited Neural Pathways from {os.path.basename(source_file_path)}")
            except Exception as e:
                print(f"⚠️ Brain Compatible Error: {e}")
                print("✨ Starting with fresh brain...")
        else:
            print(f"⚠️ Failed to inherit brain: {source_file_path} not found")

    def __repr__(self):
        return f"CorruptCop(#{self.agent_id}, {self.personality}, C:{self.corruption_score:.1f}, ε:{self.epsilon:.2f}, RPG)"
