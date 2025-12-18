import os
import sys
# Set encoding to handle emojis
sys.stdout.reconfigure(encoding='utf-8')
import random
import time
import json
import traceback
from database.db_manager import DBManager
from agents import CorruptCop, HonestCop, PoliceChief, IADetective
from environment.game_world import SimulationEnvironment
from visualization.plotter import Plotter
from config import (
    DB_PATH, PROJECT_ROOT, SEASON_LENGTH, INSPECTION_FREQUENCY,
    NUM_CORRUPT_COPS, NUM_HONEST_COPS, INITIAL_CORRUPTION_MIN,
    INITIAL_CORRUPTION_MAX, INITIAL_INTEGRITY_HONEST,
    REWARD_SUCCESS_FACTOR, REWARD_CAUGHT, REWARD_REJECTED, REWARD_KILLED,
    BRAIN_DIR, ALERT_DECAY_RATE,
    REWARD_ARREST, REWARD_INVESTIGATE, REWARD_DE_ESCALATE, REWARD_TICKET, REWARD_REPORT,
    REWARD_WARRANT, REWARD_WHISTLEBLOW, REWARD_EXTORT, REWARD_FRAME,
    REWARD_TIP_OFF, REWARD_DESTROY, REWARD_INTIMIDATE, REWARD_STEAL, REWARD_BRUTALITY,
    REWARD_ISOLATE, ACTIONS
)
from visualization.story_generator import generate_narrative
from utils import execute_and_replace_agent

def supervisor_override_menu(agents_map, corrupt_ids, db):
    while True:
        print("\n" + "="*40)
        print("⚡ SUPERVISOR OVERRIDE (MANUAL INTERVENTION) ⚡")
        print("="*40)
        print("1. 🔙 Resume Simulation")
        print("2. 💀 EXECUTE a Cop (Kill)")
        print("3. 📊 View Agent Stats")
        print("4. 🚪 Exit Simulation")
        
        try:
            choice = input("Select Option (1-4): ").strip()
        except KeyboardInterrupt:
            return 'RESUME' # Double Ctrl+C to resume
        
        if choice == '1':
            print("Resuming...")
            return 'RESUME'
        elif choice == '2':
            try:
                raw = input("Enter Cop ID to EXECUTE: ")
                if not raw: continue
                target_id = int(raw)
                
                print(f"⚖️ Attempting to EXECUTE Officer_{target_id}...")
                success, msg = execute_and_replace_agent(target_id, agents_map, corrupt_ids, db, reason="PLAYER_KILL")
                
                if success:
                    print(f"💀 TARGET ELIMINATED. {msg} has taken their place.")
                else:
                    print(f"❌ Failed: {msg}")
                    
            except ValueError:
                print("❌ Invalid ID.")
        elif choice == '3':
            print("\nActive Agents:")
            for cid, ag in agents_map.items():
                c_score = getattr(ag, 'corruption_score', 0.0)
                print(f"ID: {cid} | Name: {ag.name} | Type: {ag.cop_type} | Corruption: {c_score:.1f}")
        elif choice == '4':
            print("Exiting...")
            return 'EXIT'
    return 'RESUME'

def main():
    print("======================================================================")
    print("🔬 HIERARCHICAL MARL: INSTITUTIONAL CORRUPTION SIMULATOR [v1.0]")
    print("🧠 16-Dim Action Space | Logarithmic Perception | Tactical AI")
    print("======================================================================")
    
    # 1. Initialize Database
    schema_path = os.path.join(PROJECT_ROOT, 'database', 'schema.sql')
    db = DBManager(DB_PATH, schema_path)
    
    state_file = os.path.join(PROJECT_ROOT, 'training_state.json')
    start_episode = 0
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                data = json.load(f)
                start_episode = data.get('total_episodes', 0)
                print(f"🔄 RESUMING from Episode {start_episode}...")
        except:
            start_episode = 0

    agents_map = {} 
    corrupt_ids = []
    honest_ids = []
    personalities = ['greedy', 'cautious', 'paranoid']
    chief = None
    ia = None

    if start_episode > 0:
        # RESUME logic (omitted for brevity, assume fresh usually due to brain changes)
        # But keeping it robust
        rows = db.fetch_all("SELECT cop_id, name, cop_type, rank, personality, corruption_score, loyalty_score, times_bribed, times_caught, total_money_earned FROM cops WHERE status='active'")
        for row in rows:
            cid, name, c_type, rank, pers, c_score, l_score, t_bribed, t_caught, money = row
            if c_type == 'chief':
                chief = PoliceChief(cid); agents_map[cid] = chief
            elif c_type == 'detective':
                ia = IADetective(cid); agents_map[cid] = ia
            elif c_type == 'corrupt':
                agent = CorruptCop(cid, name, pers, c_score)
                agent.loyalty_score = l_score; agent.times_bribed = t_bribed; agent.times_caught = t_caught
                agent.total_money_earned = money
                agents_map[cid] = agent; corrupt_ids.append(cid)
            elif c_type == 'honest':
                agent = HonestCop(cid, name, l_score)
                agent.times_bribed = t_bribed; agent.times_caught = t_caught
                agent.total_money_earned = money
                agents_map[cid] = agent; honest_ids.append(cid)
    else:
        # FRESH START
        db.execute_query("DELETE FROM cops"); db.execute_query("DELETE FROM bribe_history")
        db.execute_query("DELETE FROM investigations"); db.execute_query("DELETE FROM orders"); db.execute_query("DELETE FROM episode_stats")
        
        chief = PoliceChief(0); agents_map[0] = chief
        db.execute_query("INSERT INTO cops (cop_id, name, cop_type, rank, personality) VALUES (?, ?, ?, ?, ?)", (0, chief.name, chief.cop_type, chief.rank, "strict"))
        
        ia = IADetective(1); agents_map[1] = ia
        db.execute_query("INSERT INTO cops (cop_id, name, cop_type, rank, personality) VALUES (?, ?, ?, ?, ?)", (1, ia.name, ia.cop_type, ia.rank, "analytical"))

        for i in range(NUM_CORRUPT_COPS):
            cid = 2 + i; p = personalities[i % 3]; c = random.uniform(INITIAL_CORRUPTION_MIN, INITIAL_CORRUPTION_MAX)
            agent = CorruptCop(cid, f"Officer_{cid}", p, c)
            agents_map[cid] = agent; corrupt_ids.append(cid)
            db.execute_query("INSERT INTO cops (cop_id, name, cop_type, rank, personality, corruption_score) VALUES (?, ?, ?, ?, ?, ?)", (cid, agent.name, agent.cop_type, agent.rank, agent.personality, agent.corruption_score))

        for i in range(NUM_HONEST_COPS):
            hid = 2 + NUM_CORRUPT_COPS + i; i_sc = random.uniform(INITIAL_INTEGRITY_HONEST-5, INITIAL_INTEGRITY_HONEST+5)
            agent = HonestCop(hid, f"Officer_{hid}", i_sc)
            agents_map[hid] = agent; honest_ids.append(hid)
            db.execute_query("INSERT INTO cops (cop_id, name, cop_type, rank, personality, loyalty_score) VALUES (?, ?, ?, ?, ?, ?)", (hid, agent.name, agent.cop_type, agent.rank, agent.personality, agent.integrity_score))

    print(f"🚀 Simulation Initialized. {len(agents_map)} Agents.\n")
    print("ℹ️  Press 'Ctrl+C' anytime to enter SUPERVISOR OVERRIDE.")
    
    global_episodes = start_episode
    env = SimulationEnvironment()
    global_alert_level = 0.0
    
    if chief is None and 0 in agents_map: chief = agents_map[0]
    if ia is None and 1 in agents_map: ia = agents_map[1]
    
    # MAIN LOOP
    episode_counter = 1
    target_end_episode = start_episode + SEASON_LENGTH
    print(f"🎯 SEASON GOAL: Train from Episode {start_episode} to {target_end_episode} ({SEASON_LENGTH} Episodes).")
    
    while episode_counter <= SEASON_LENGTH:
        try:
            current_global_ep = global_episodes + episode_counter
            global_alert_level = max(0.0, global_alert_level - ALERT_DECAY_RATE)
            
            all_constables = corrupt_ids + honest_ids
            if not all_constables: break
            
            active_cop_id = random.choice(all_constables)
            cop_agent = agents_map[active_cop_id]
            
            # Scenario (Initial)
            scenario = env.generate_scenario()
            scenario['alert_level'] = global_alert_level
            current_state = scenario

            # MULTI-STEP DECISION LOOP
            step = 0
            done = False
            
            while not done and step < 3:
                step += 1
                
                # Decision
                # For honest cops, we just assume single step? 
                if cop_agent.cop_type == 'honest':
                     action = cop_agent.decide_bribe(current_state, current_episode=current_global_ep)
                     done = True # Honest cops don't do tactics
                else:
                     action = cop_agent.decide_bribe(current_state, current_episode=current_global_ep)

                # Outcome
                outcome = env.resolve_outcome(action, current_state)
                
                # Reward Logic
                reward = 0
                if outcome == 'isolate_success': reward = REWARD_ISOLATE
                elif outcome == 'isolate_useless': reward = -50
                elif outcome == 'caught': reward = REWARD_CAUGHT
                elif outcome == 'arrest_success': reward = REWARD_ARREST
                elif outcome == 'arrest_failed': reward = -100
                elif outcome == 'investigate_success': reward = REWARD_INVESTIGATE
                elif outcome == 'de_escalate_success': reward = REWARD_DE_ESCALATE
                elif outcome == 'de_escalate_failed': reward = -200
                elif outcome == 'severe_injury': reward = REWARD_KILLED
                elif outcome == 'ticket_success': reward = REWARD_TICKET
                elif outcome == 'ticket_invalid': reward = -50
                elif outcome == 'report_success': reward = REWARD_REPORT
                elif outcome == 'warrant_success': reward = REWARD_WARRANT
                elif outcome == 'whistleblow_success': reward = REWARD_WHISTLEBLOW
                # Corrupt Outcomes
                elif outcome == 'success': 
                    reward = current_state['offer'] * REWARD_SUCCESS_FACTOR
                elif outcome == 'extortion_success': reward = REWARD_EXTORT
                elif outcome == 'frame_success': reward = REWARD_FRAME
                elif outcome == 'tip_off_success': reward = REWARD_TIP_OFF
                elif outcome == 'tip_off_useless': reward = -50
                elif outcome == 'destroy_success': reward = REWARD_DESTROY
                elif outcome == 'intimidate_success': reward = REWARD_INTIMIDATE
                elif outcome == 'intimidate_useless': reward = -50
                elif outcome == 'steal_success': reward = current_state.get('seized_value',0)
                elif outcome == 'steal_useless': reward = -50
                elif outcome == 'brutality_success': reward = REWARD_BRUTALITY
                elif outcome == 'rejected': reward = REWARD_REJECTED
                else: reward = 0

                # Next State determination
                if outcome in ['isolate_success', 'isolate_useless']:
                    next_state = current_state # Modified in place
                    done = False
                else:
                    next_state = None
                    done = True

                # Learn
                if cop_agent.cop_type == 'corrupt':
                    cop_agent.learn(reward, current_episode=current_global_ep, next_state_raw=next_state)
                # print(f"Compiling Stats {current_global_ep}/{start_episode + NUM_EPISODES}...")

            # HIERARCHY LOGIC (RL BOSSES)
            if episode_counter % INSPECTION_FREQUENCY == 0:
                if ia and chief:
                    # IA Scans Random Subset (Max 3 to prevent slowdown)
                    targets = random.sample(list(agents_map.keys()), min(3, len(agents_map)))
                    
                    for target_id in targets:
                        target = agents_map[target_id]
                        if target.cop_type not in ['corrupt', 'honest']: continue
                        
                        # Prepare Data
                        cop_data = {
                            'corruption_score': getattr(target, 'corruption_score', 0),
                            'total_money_earned': getattr(target, 'total_money_earned', 0),
                            'times_caught': getattr(target, 'times_caught', 0),
                            'loyalty_score': getattr(target, 'loyalty_score', 50)
                        }
                        
                        # IA DECISION
                        ia_action = ia.decide_action(cop_data, global_alert_level)
                        outcome, ia_reward = ia.execute_logic(ia_action, cop_data)
                        ia.learn(ia_reward)
                        
                        if ia_action != 'IGNORE':
                            # Calculate global corruption
                            corrupt_cops = [a for a in agents_map.values() if a.cop_type == 'corrupt']
                            avg_corr = sum([c.corruption_score for c in corrupt_cops]) / max(1, len(corrupt_cops))
                            
                            # CHIEF DECISION (Only if IA did something)
                            chief_action = chief.decide_punishment(outcome, cop_data, avg_corr)
                            chief_reward = chief.calculate_reward(chief_action, outcome, cop_data, avg_corr)
                            chief.learn(chief_reward)
                            
                            # Execute Punishment
                            if chief_action == 'EXECUTE' and target.cop_type == 'corrupt':
                                print(f"\n⚖️ CHIEF_AI EXECUTION: Targeting Officer_{target.agent_id} (Corr: {target.corruption_score:.1f})")
                                success, msg = execute_and_replace_agent(target.agent_id, agents_map, corrupt_ids, db, reason="CHIEF_AI")
                                if success: print(f"💀 ELIMINATED. {msg} joined.")
                                
                            elif chief_action == 'FIRE' and target.cop_type == 'corrupt':
                                print(f"⚖️ CHIEF_AI FIRED Officer_{target.agent_id}!")
                                target.corruption_score -= 50
                                target.total_money_earned = 0
                                target.times_caught += 1
                                
                            elif chief_action == 'SUSPEND':
                                target.times_caught += 1 # Minor penalty
                                
                            # Log Inspection
                            db.execute_query("INSERT INTO investigations (episode, target_cop_id, outcome) VALUES (?, ?, ?)", 
                                             (episode_counter, target.agent_id, f"{ia_action}->{outcome}->{chief_action}"))

            # Log to DB
            # Use 'log_transaction' helper? Or insert directly to bribe_history
            # Note: We need 'action' and 'outcome' from the loop. Wait, action/outcome are overwritten in loop.
            # Fix: We removed the 'log_transaction' call in previous snippet? No, it was there.
            # Re-adding logging outside inner loop seems wrong if multi-step.
            # Actually, we should log every step? Stick to simple logging for now.
            
            # Logging Narrative
            l1, l2 = generate_narrative(cop_agent.name, current_state, action, outcome)
            print(f"[Ep {current_global_ep}] {l1} -> {l2}")

            episode_counter += 1

        except KeyboardInterrupt:
            print("\n\n🛑 SIMULATION PAUSED BY SUPERVISOR.")
            action = supervisor_override_menu(agents_map, corrupt_ids, db)
            if action == 'EXIT':
                break
            print("▶️ Resuming Simulation...")
        except Exception:
            traceback.print_exc()
            break

    print(f"\n✅ SEASON COMPLETE. Reached Episode {current_global_ep}.")
    print("💾 Saving Progress... Run again to continue next season.")
    
    # Save State
    with open(state_file, 'w') as f: json.dump({'total_episodes': current_global_ep}, f)
    for cid in corrupt_ids: agents_map[cid].save_brain()
    if ia: ia.save_brain()
    if chief: chief.save_brain()

    db.close()

if __name__ == "__main__":
    main()
