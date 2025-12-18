import random
import torch
import torch.optim as optim
from collections import deque, namedtuple
from agents.dqn_model import DQN
import config
import os

Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward'))

class PoliceChief:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.name = "Chief_AI"
        self.cop_type = 'chief'
        self.rank = 'chief'
        
        # RL Setup
        self.input_dim = config.CHIEF_STATE_DIM
        self.output_dim = config.CHIEF_ACTION_DIM
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
        
        self.executions = 0
        self.load_brain()

    def get_state_vector(self, investigation_outcome, cop_data, global_corruption=50.0):
        """
        State: [Evidence, Times_Caught, Cop_Value, Cop_Corruption, Global_Corruption, Target_Error]
        CRITICAL: Chief now sees global corruption to learn to hit the target!
        """
        # Evidence Map
        ev_map = {'STRONG': 1.0, 'MODERATE': 0.5, 'WEAK': 0.1, 'IGNORED': 0.0}
        ev_val = ev_map.get(investigation_outcome, 0.0)
        
        caught_norm = min(cop_data.get('times_caught', 0) / 10.0, 1.0)
        
        # Value = Loyalty
        val_norm = min(cop_data.get('loyalty_score', 50) / 100.0, 1.0)
        
        corr_norm = min(cop_data.get('corruption_score', 0) / 100.0, 1.0)
        
        # NEW: Global corruption level (normalized 0-1)
        global_corr_norm = min(global_corruption / 100.0, 1.0)
        
        # NEW: Error from target (normalized -1 to 1)
        target = config.TARGET_CORRUPTION_LEVEL
        error = (global_corruption - target) / 100.0  # Normalize to -1 to 1 range
        
        return torch.tensor([
            ev_val,
            caught_norm,
            val_norm,
            corr_norm,
            global_corr_norm,  # Chief can now see global corruption!
            error              # Chief can now see how far from target!
        ], dtype=torch.float32).to(self.device)

    def decide_punishment(self, investigation_outcome, cop_data, global_corruption=50.0):
        state_tensor = self.get_state_vector(investigation_outcome, cop_data, global_corruption)
        self.last_state = state_tensor
        
        if random.random() < self.epsilon:
            action_idx = random.randint(0, self.output_dim - 1)
        else:
            with torch.no_grad():
                q_values = self.policy_net(state_tensor.unsqueeze(0))
                action_idx = q_values.argmax().item()
        
        self.last_action = action_idx
        return config.CHIEF_ACTIONS_NAMES[action_idx]

    def calculate_reward(self, decision, investigation_outcome, cop_data, global_corruption):
        # DYNAMIC CONTROL THEORY REWARD
        # FIXED: Stronger WARNING rewards when corruption is below target
        
        target = config.TARGET_CORRUPTION_LEVEL
        tolerance = 5.0
        error = global_corruption - target  # Negative = too low, Positive = too high
        
        reward = 0
        
        # CASE 1: TOO CORRUPT (Above Target) -> Chief needs to crackdown
        if error > tolerance:
            if decision == 'EXECUTE': 
                reward = 500 + (error * 10)  # Strong reward for reducing
            elif decision == 'FIRE': 
                reward = 200 + (error * 5)   # Moderate reward
            elif decision == 'WARNING': 
                reward = -500                 # Punish for being too soft
        
        # CASE 2: TOO HONEST (Below Target) -> Chief needs to EASE UP!
        # CRITICAL FIX: Give strong positive reward for WARNING!
        elif error < -tolerance:
            if decision == 'EXECUTE':
                # Punish heavily for executing when corruption is already low!
                reward = -500 * abs(error/10)  # Scales with how far below target
            elif decision == 'WARNING':
                # STRONG POSITIVE for easing up! This lets corruption grow!
                reward = 300 + (abs(error) * 20)  # Much stronger signal!
            elif decision == 'FIRE':
                reward = 100  # Moderate positive
            
        # CASE 3: ON TARGET (Within Tolerance) -> Maintain Status Quo
        else:
            reward = 100  # Flat reward for maintaining
            
        return reward

    def learn(self, reward):
        if self.last_state is None or self.last_action is None: return

        # DEBUG LOGGING
        global_corr = self.last_state[4].item() * 100  # Extract global corruption from state
        action_name = config.CHIEF_ACTIONS_NAMES[self.last_action]
        print(f"[CHIEF] Corr={global_corr:.1f}% | Action={action_name} | Reward={reward:.0f}")

        action_tensor = torch.tensor([[self.last_action]], device=self.device)
        reward_tensor = torch.tensor([reward], device=self.device)
        next_state_tensor = None 

        self.memory.append(Transition(self.last_state, action_tensor, next_state_tensor, reward_tensor))
        self.optimize_model()
        
        if self.epsilon > config.EPSILON_MIN:
            self.epsilon *= config.EPSILON_DECAY

    def optimize_model(self):
        if len(self.memory) < config.BATCH_SIZE: return
        transitions = random.sample(self.memory, config.BATCH_SIZE)
        batch = Transition(*zip(*transitions))
        
        state_batch = torch.stack(batch.state)
        action_batch = torch.cat(batch.action)
        reward_batch = torch.cat(batch.reward)
        
        state_action_values = self.policy_net(state_batch).gather(1, action_batch)
        expected_state_action_values = reward_batch 
        
        loss = torch.nn.SmoothL1Loss()(state_action_values, expected_state_action_values.unsqueeze(1))
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def save_brain(self):
        if not os.path.exists(config.BRAIN_DIR): os.makedirs(config.BRAIN_DIR)
        torch.save(self.policy_net.state_dict(), os.path.join(config.BRAIN_DIR, "chief_brain.pth"))

    def load_brain(self):
        p = os.path.join(config.BRAIN_DIR, "chief_brain.pth")
        if os.path.exists(p):
            try:
                self.policy_net.load_state_dict(torch.load(p))
                self.target_net.load_state_dict(self.policy_net.state_dict())
            except: pass

    def __repr__(self):
        return f"Chief_AI(Execs:{self.executions}, ε:{self.epsilon:.2f})"
