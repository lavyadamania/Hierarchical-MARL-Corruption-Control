import os
import random
import json
import traceback
import time
from database.db_manager import DBManager
from agents import CorruptCop, HonestCop, PoliceChief, IADetective
from environment.game_world import SimulationEnvironment
import config # CHANGED
from visualization.story_generator import generate_narrative
from utils import execute_and_replace_agent

class SimulationEngine:
    def __init__(self):
        self.running = False
        self.paused = False
        self.episode_counter = 0
        self.global_episodes = 0
        self.global_alert_level = 0.0
        self.agents_map = {}
        self.corrupt_ids = []
        self.honest_ids = []
        self.chief = None
        self.ia = None
        
        # Performance modes
        self.turbo_mode = False  # When True, minimal UI updates for max speed
        
        # Initialize components
        schema_path = os.path.join(config.PROJECT_ROOT, 'database', 'schema.sql')
        self.db = DBManager(config.DB_PATH, schema_path)
        self.env = SimulationEnvironment()
        self.state_file = os.path.join(config.PROJECT_ROOT, 'training_state.json')
        
        self.initialize_agents()

    def initialize_agents(self):
        start_episode = 0
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    start_episode = data.get('total_episodes', 0)
            except:
                start_episode = 0
        
        self.global_episodes = start_episode
        self.agents_map = {}
        self.corrupt_ids = []
        self.honest_ids = []
        personalities = ['greedy', 'cautious', 'paranoid']

        if self.global_episodes > 0:
            # RESUME logic 
            rows = self.db.fetch_all("SELECT cop_id, name, cop_type, rank, personality, corruption_score, loyalty_score, times_bribed, times_caught, total_money_earned FROM cops WHERE status='active'")
            if not rows: # Fallback if DB is empty
                self.global_episodes = 0 
            else:
                for row in rows:
                    cid, name, c_type, rank, pers, c_score, l_score, t_bribed, t_caught, money = row
                    if c_type == 'chief':
                        self.chief = PoliceChief(cid); self.agents_map[cid] = self.chief
                    elif c_type == 'detective':
                        self.ia = IADetective(cid); self.agents_map[cid] = self.ia
                    elif c_type == 'corrupt':
                        agent = CorruptCop(cid, name, pers, c_score)
                        agent.loyalty_score = l_score; agent.times_bribed = t_bribed; agent.times_caught = t_caught
                        agent.total_money_earned = money
                        self.agents_map[cid] = agent; self.corrupt_ids.append(cid)
                    elif c_type == 'honest':
                        agent = HonestCop(cid, name, l_score)
                        agent.times_bribed = t_bribed; agent.times_caught = t_caught
                        agent.total_money_earned = money
                        self.agents_map[cid] = agent; self.honest_ids.append(cid)

        if self.global_episodes == 0 or not self.agents_map:
            # FRESH START
            self.db.execute_query("DELETE FROM cops"); self.db.execute_query("DELETE FROM bribe_history")
            self.db.execute_query("DELETE FROM investigations"); self.db.execute_query("DELETE FROM orders"); self.db.execute_query("DELETE FROM episode_stats")
            
            self.chief = PoliceChief(0); self.agents_map[0] = self.chief
            self.db.execute_query("INSERT INTO cops (cop_id, name, cop_type, rank, personality) VALUES (?, ?, ?, ?, ?)", (0, self.chief.name, self.chief.cop_type, self.chief.rank, "strict"))
            
            self.ia = IADetective(1); self.agents_map[1] = self.ia
            self.db.execute_query("INSERT INTO cops (cop_id, name, cop_type, rank, personality) VALUES (?, ?, ?, ?, ?)", (1, self.ia.name, self.ia.cop_type, self.ia.rank, "analytical"))

            for i in range(config.NUM_CORRUPT_COPS):
                cid = 2 + i; p = personalities[i % 3]; c = random.uniform(config.INITIAL_CORRUPTION_MIN, config.INITIAL_CORRUPTION_MAX)
                agent = CorruptCop(cid, f"Officer_{cid}", p, c)
                self.agents_map[cid] = agent; self.corrupt_ids.append(cid)
                self.db.execute_query("INSERT INTO cops (cop_id, name, cop_type, rank, personality, corruption_score) VALUES (?, ?, ?, ?, ?, ?)", (cid, agent.name, agent.cop_type, agent.rank, agent.personality, agent.corruption_score))

            for i in range(config.NUM_HONEST_COPS):
                hid = 2 + config.NUM_CORRUPT_COPS + i; i_sc = random.uniform(config.INITIAL_INTEGRITY_HONEST-5, config.INITIAL_INTEGRITY_HONEST+5)
                agent = HonestCop(hid, f"Officer_{hid}", i_sc)
                self.agents_map[hid] = agent; self.honest_ids.append(hid)
                self.db.execute_query("INSERT INTO cops (cop_id, name, cop_type, rank, personality, loyalty_score) VALUES (?, ?, ?, ?, ?, ?)", (hid, agent.name, agent.cop_type, agent.rank, agent.personality, agent.integrity_score))

        # Ensure Chief and IA exist if loading failed to assign them
        if self.chief is None and 0 in self.agents_map: self.chief = self.agents_map[0]
        if self.ia is None and 1 in self.agents_map: self.ia = self.agents_map[1]

    def step(self):
        """Runs a single episode step."""
        if not self.agents_map: return None
        
        self.current_global_ep = self.global_episodes + self.episode_counter + 1
        self.global_alert_level = max(0.0, self.global_alert_level - config.ALERT_DECAY_RATE)
        
        all_constables = self.corrupt_ids + self.honest_ids
        if not all_constables: return None
        
        active_cop_id = random.choice(all_constables)
        cop_agent = self.agents_map[active_cop_id]
        
        # Scenario (Initial)
        scenario = self.env.generate_scenario()
        scenario['alert_level'] = self.global_alert_level
        current_state = scenario

        # MULTI-STEP DECISION LOOP
        step_count = 0
        done = False
        log_entry = ""
        
        final_outcome = ""
        final_action = ""

        while not done and step_count < 3:
            step_count += 1
            
            # Decision
            if cop_agent.cop_type == 'honest':
                    action = cop_agent.decide_bribe(current_state, current_episode=self.current_global_ep)
                    done = True 
            else:
                    action = cop_agent.decide_bribe(current_state, current_episode=self.current_global_ep)

            # Outcome
            outcome = self.env.resolve_outcome(action, current_state)
            
            # Keep track for logging
            final_action = action
            final_outcome = outcome

            # Reward Logic (Simplified for Engine - Logic is same as main.py)
            reward = 0
            # [Copying Reward Logic from main.py]
            if outcome == 'isolate_success': reward = config.REWARD_ISOLATE
            elif outcome == 'isolate_useless': reward = -50
            elif outcome == 'caught': reward = config.REWARD_CAUGHT
            elif outcome == 'arrest_success': reward = config.REWARD_ARREST
            elif outcome == 'arrest_failed': reward = -100
            elif outcome == 'investigate_success': reward = config.REWARD_INVESTIGATE
            elif outcome == 'de_escalate_success': reward = config.REWARD_DE_ESCALATE
            elif outcome == 'de_escalate_failed': reward = -200
            elif outcome == 'severe_injury': reward = config.REWARD_KILLED
            elif outcome == 'ticket_success': reward = config.REWARD_TICKET
            elif outcome == 'ticket_invalid': reward = -50
            elif outcome == 'report_success': reward = config.REWARD_REPORT
            elif outcome == 'warrant_success': reward = config.REWARD_WARRANT
            elif outcome == 'whistleblow_success': reward = config.REWARD_WHISTLEBLOW
            elif outcome == 'success': reward = current_state['offer'] * config.REWARD_SUCCESS_FACTOR
            elif outcome == 'extortion_success': reward = config.REWARD_EXTORT
            elif outcome == 'frame_success': reward = config.REWARD_FRAME
            elif outcome == 'tip_off_success': reward = config.REWARD_TIP_OFF
            elif outcome == 'tip_off_useless': reward = -50
            elif outcome == 'destroy_success': reward = config.REWARD_DESTROY
            elif outcome == 'intimidate_success': reward = config.REWARD_INTIMIDATE
            elif outcome == 'intimidate_useless': reward = -50
            elif outcome == 'steal_success': reward = current_state.get('seized_value',0)
            elif outcome == 'steal_useless': reward = -50
            elif outcome == 'brutality_success': reward = config.REWARD_BRUTALITY
            # 'rejected' outcome removed from game world
            else: reward = 0

            # Update Stats & Kickbacks
            if cop_agent.cop_type == 'corrupt':
                offer = current_state.get('offer', 0)
                outcome_val = offer if outcome in ['success', 'extortion_success'] else 0
                cop_agent.update_stats(outcome, outcome_val, self.current_global_ep)
                
                # KICKBACK TO CHIEF (10%)
                if outcome_val > 0 and self.chief:
                    kickback = outcome_val * 0.10
                    # Ensure Chief has attribute
                    if not hasattr(self.chief, 'total_money_earned'): self.chief.total_money_earned = 0
                    self.chief.total_money_earned += kickback
                    
                    # Deduct from Cop? Optional. Let's say it's a tax.
                    cop_agent.total_money_earned -= kickback

            # Next State
            if outcome in ['isolate_success', 'isolate_useless']:
                next_state = current_state 
                done = False
            else:
                next_state = None
                done = True

            # Learn
            if cop_agent.cop_type == 'corrupt':
                cop_agent.learn(reward, current_episode=self.current_global_ep, next_state_raw=next_state)
            
            if not done:
                current_state = next_state
        
        self.episode_counter += 1
        
        # Narrative
        l1, l2 = generate_narrative(cop_agent.name, current_state, final_action, final_outcome)
        log_entry = f"[Ep {self.current_global_ep}] {l1} -> {l2}"

        # Hierarchy Checks
        Hierarchy_Log = []
        if self.episode_counter % config.INSPECTION_FREQUENCY == 0:
             if self.ia and self.chief:
                targets = random.sample(list(self.agents_map.keys()), min(3, len(self.agents_map)))
                for target_id in targets:
                    target = self.agents_map[target_id]
                    if target.cop_type not in ['corrupt', 'honest']: continue
                    
                    cop_data = {
                        'corruption_score': getattr(target, 'corruption_score', 0),
                        'total_money_earned': getattr(target, 'total_money_earned', 0),
                        'times_caught': getattr(target, 'times_caught', 0),
                        'loyalty_score': getattr(target, 'loyalty_score', 50)
                    }
                    ia_action = self.ia.decide_action(cop_data, self.global_alert_level)
                    outcome, ia_reward = self.ia.execute_logic(ia_action, cop_data)
                    self.ia.learn(ia_reward)

                    # CRITICAL FIX: Chief learns whenever IA sends a cop!
                    if ia_action == 'SEND_TO_CHIEF':  # Changed from !='IGNORE'
                        # Calculate Global Corruption for Chief's Context
                        corrupt_cops = [a for a in self.agents_map.values() if a.cop_type == 'corrupt']
                        avg_corr = sum([c.corruption_score for c in corrupt_cops]) / max(1, len(corrupt_cops))

                        # Chief ALWAYS learns when IA sends someone
                        chief_action = self.chief.decide_punishment(outcome, cop_data, avg_corr)
                        chief_reward = self.chief.calculate_reward(chief_action, outcome, cop_data, avg_corr)
                        self.chief.learn(chief_reward)
                        
                        # Execute the punishment
                        event_msg = ""
                        if chief_action == 'EXECUTE' and target.cop_type == 'corrupt':
                            success, msg = execute_and_replace_agent(target.agent_id, self.agents_map, self.corrupt_ids, self.db, reason="CHIEF_AI")
                            event_msg = f"⚖️ EXECUTION: Officer_{target.agent_id} eliminiated. {msg}"
                        elif chief_action == 'FIRE':
                             event_msg = f"⚖️ FIRED: Officer_{target.agent_id}."
                        
                        if event_msg: Hierarchy_Log.append(event_msg)
                        self.db.execute_query("INSERT INTO investigations (episode, target_cop_id, outcome) VALUES (?, ?, ?)", 
                                             (self.current_global_ep, target.agent_id, f"{ia_action}->{outcome}->{chief_action}"))

        stats = {
            "corruption_level": sum([getattr(a, 'corruption_score', 0) for a in self.agents_map.values() if a.cop_type == 'corrupt']) / len(self.corrupt_ids) if self.corrupt_ids else 0,
            "avg_wealth_corrupt": sum([getattr(a, 'total_money_earned', 0) for a in self.agents_map.values() if a.cop_type == 'corrupt']) / len(self.corrupt_ids) if self.corrupt_ids else 0,
            "chief_wealth": getattr(self.chief, 'total_money_earned', 0) if self.chief else 0,
            "chief_executions": getattr(self.chief, 'executions', 0) if self.chief else 0,
            "active_agents": len(self.agents_map)
        }
        
        # PERSIST STATS TO DB (Fix for Blank Graphs)
        try:
            current_corr = stats["corruption_level"]
            avg_wealth = stats["avg_wealth_corrupt"]
            chief_wealth = stats["chief_wealth"]
            self.db.execute_query(
                "INSERT INTO episode_stats (episode, corruption_level, avg_wealth, chief_wealth) VALUES (?, ?, ?, ?)",
                (self.current_global_ep, current_corr, avg_wealth, chief_wealth)
            )
        except Exception as e:
            # print(f"DB Log Error: {e}")
            pass

        # In turbo mode, only return data every 100 episodes to reduce UI overhead
        if self.turbo_mode and (self.episode_counter % 100 != 0):
            return None  # Skip UI update for speed
        
        return {
            "episode": self.current_global_ep,
            "log": log_entry,
            "hierarchy_logs": Hierarchy_Log,
            "stats": stats,
            "turbo": self.turbo_mode,  # Include turbo status
            "agents": [
                {
                    "id": uid, 
                    "name": ag.name, 
                    "type": ag.cop_type, 
                    "corruption": getattr(ag, 'corruption_score', 0),
                    "action": final_action
                }
                for uid, ag in self.agents_map.items()
            ]
        }

    def execute_agent(self, agent_id):
        """Manually executes an agent via Supervisor Override."""
        if agent_id not in self.agents_map:
            return False, "Agent not found."
        
        success, msg = execute_and_replace_agent(agent_id, self.agents_map, self.corrupt_ids, self.db, reason="SUPERVISOR_KILL")
        return success, msg
    
    def set_turbo_mode(self, enabled):
        """Toggle turbo mode for fast training with minimal UI updates."""
        self.turbo_mode = enabled
        return self.turbo_mode

    def save_state(self):
        with open(self.state_file, 'w') as f: 
            json.dump({'total_episodes': self.global_episodes + self.episode_counter}, f)
        for cid in self.corrupt_ids: self.agents_map[cid].save_brain()
        if self.ia: self.ia.save_brain()
        if self.chief: self.chief.save_brain()
    
    def reset(self):
         self.global_episodes = 0
         self.episode_counter = 0
         
         # 1. Try to delete state file to prevent 'Resume' logic
         if os.path.exists(self.state_file):
            try: os.remove(self.state_file)
            except: pass
            
         # 2. Force Wipe In-Memory
         self.agents_map = {}
         self.corrupt_ids = []
         self.honest_ids = []
         
         # 3. Force Wipe DB (Redundant safety check)
         try:
             self.db.execute_query("DELETE FROM cops")
             self.db.execute_query("DELETE FROM bribe_history")
             self.db.execute_query("DELETE FROM investigations")
             self.db.execute_query("DELETE FROM orders")
             self.db.execute_query("DELETE FROM episode_stats")
         except: pass

         # 4. Re-Initialize (Will now definitely proceed as Fresh Start)
         self.db.initialize_db()
         self.initialize_agents()

