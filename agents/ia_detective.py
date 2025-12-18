import random
import torch
import torch.optim as optim
from collections import deque, namedtuple
from agents.dqn_model import DQN
import config # CHANGED
import os

Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward'))

class IADetective:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.name = "Det_Holmes_AI"
        self.cop_type = 'detective'
        self.rank = 'detective'
        
        # RL Setup
        self.input_dim = config.IA_STATE_DIM
        self.output_dim = config.IA_ACTION_DIM
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
        
        # Stats
        self.cases_solved = 0
        self.cases_failed = 0
        self.money_spent = 0
        
        self.load_brain()

    def get_state_vector(self, cop_data, global_alert):
        """
        State: [Suspicion, Wealth, Caught_Count, Alert, Random]
        """
        # Suspicion Estimate (Noisy)
        real_corruption = cop_data.get('corruption_score', 0)
        noisy_suspicion = min((real_corruption + random.uniform(-10, 10)) / 100.0, 1.0)
        
        # Wealth Visible
        wealth_norm = min(cop_data.get('total_money_earned', 0) / 200000.0, 1.0)
        
        # History
        caught_norm = min(cop_data.get('times_caught', 0) / 10.0, 1.0)
        
        return torch.tensor([
            noisy_suspicion,
            wealth_norm,
            caught_norm,
            global_alert,
            random.random() # Random noise to preventing deterministic loops
        ], dtype=torch.float32).to(self.device)

    def decide_action(self, cop_data, global_alert):
        state_tensor = self.get_state_vector(cop_data, global_alert)
        self.last_state = state_tensor
        
        if random.random() < self.epsilon:
            action_idx = random.randint(0, self.output_dim - 1)
        else:
            with torch.no_grad():
                q_values = self.policy_net(state_tensor.unsqueeze(0))
                action_idx = q_values.argmax().item()
        
        self.last_action = action_idx
        return config.IA_ACTIONS_NAMES[action_idx]

    def execute_logic(self, action_name, cop_data):
        """
        SIMPLIFIED: Just decide if cop is guilty or not
        Returns: (Outcome_String, Reward_For_IA)
        """
        real_corruption = cop_data.get('corruption_score', 0)
        
        if action_name == 'IGNORE':
            # Reward: Good if cop was actually honest, bad if missed corrupt cop
            if real_corruption > 60:
                return 'IGNORED', -20  # Missed a corrupt cop!
            return 'IGNORED', 5  # Correctly ignored honest cop
            
        elif action_name == 'SEND_TO_CHIEF':
            # Sent to Chief - check if was actually corrupt
            if real_corruption > 50:
                self.cases_solved += 1
                return 'GUILTY', 100  # Good call!
            else:
                self.cases_failed += 1  
                return 'NOT_GUILTY', -50  # Wasted Chief's time
        
        return 'NOT_GUILTY', 0

    def learn(self, reward):
        if self.last_state is None or self.last_action is None: return

        action_tensor = torch.tensor([[self.last_action]], device=self.device)
        reward_tensor = torch.tensor([reward], device=self.device)
        # Next state is not really applicable in this turn-based checking, use None or current
        next_state_tensor = None 

        self.memory.append(Transition(self.last_state, action_tensor, next_state_tensor, reward_tensor))
        self.optimize_model()
        
        if self.epsilon > config.EPSILON_MIN:
            self.epsilon *= config.EPSILON_DECAY

    def optimize_model(self):
        if len(self.memory) < config.BATCH_SIZE: return
        transitions = random.sample(self.memory, config.BATCH_SIZE)
        batch = Transition(*zip(*transitions))
        
        # Simplified optimization (since next_state often None/Irrelevant for immediate classification tasks)
        # But we keep standard DQN structure
        state_batch = torch.stack(batch.state)
        action_batch = torch.cat(batch.action)
        reward_batch = torch.cat(batch.reward)
        
        state_action_values = self.policy_net(state_batch).gather(1, action_batch)
        expected_state_action_values = reward_batch # direct reward learning for now as steps are independent
        
        criterion = torch.nn.SmoothL1Loss()
        loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def save_brain(self):
        if not os.path.exists(config.BRAIN_DIR): os.makedirs(config.BRAIN_DIR)
        torch.save(self.policy_net.state_dict(), os.path.join(config.BRAIN_DIR, "ia_brain.pth"))

    def load_brain(self):
        p = os.path.join(config.BRAIN_DIR, "ia_brain.pth")
        if os.path.exists(p):
            try:
                self.policy_net.load_state_dict(torch.load(p))
                self.target_net.load_state_dict(self.policy_net.state_dict())
            except: pass

    def __repr__(self):
        return f"IADetective_AI(Solv:{self.cases_solved}, Fail:{self.cases_failed}, ε:{self.epsilon:.2f})"
