import os
import random
import config # CHANGED
from agents.corrupt_cop import CorruptCop

def execute_and_replace_agent(target_id, agents_map, corrupt_ids, db, reason="EXECUTE"):
    """
    Handles the logic of killing an agent and spawning a successor.
    Shared by God Mode (manual) and Chief Logic (automatic).
    """
    if target_id not in agents_map:
        return False, "Agent Not Found"
        
    cop = agents_map[target_id]
    
    # Only CorruptCops have brains to save/inherit
    if cop.cop_type == 'corrupt':
        cop.save_brain()
        dead_brain_path = os.path.join(config.BRAIN_DIR, f"cop_{target_id}.pth")
        
        # Calculate next ID
        next_cop_id = max(agents_map.keys()) + 1
        
        # Spawn Replacement
        # Helper: get personalities randomly if not passed, but for now hardcoded list is fine or passed in
        personalities = ['greedy', 'cautious', 'paranoid'] 
        new_agent = CorruptCop(next_cop_id, f"Officer_{next_cop_id}", random.choice(personalities), random.uniform(30,60))
        
        # Cleanup Old
        if target_id in corrupt_ids: corrupt_ids.remove(target_id)
        del agents_map[target_id]
        
        # Register New
        agents_map[next_cop_id] = new_agent
        corrupt_ids.append(next_cop_id)
        
        # Brain Inheritance
        new_agent.inherit_brain(dead_brain_path)
        
        # Database Updates
        status_update = 'executed_by_player' if reason == 'PLAYER_KILL' else 'executed'
        db.update_cop_status(target_id, status_update)
        db.execute_query("INSERT INTO cops (cop_id, name, cop_type, rank, personality, corruption_score) VALUES (?, ?, ?, ?, ?, ?)", 
                         (next_cop_id, new_agent.name, new_agent.cop_type, new_agent.rank, new_agent.personality, new_agent.corruption_score))
        
        return True, new_agent.name
    else:
        # Handling for honest cops or special roles if needed in future (currently simplified to only replace corrupt)
        # For this specific project requirement, we mostly focus on replacing corrupt cops as they have the neural nets.
        # But to be safe, we should handle removal of others too if requested. 
        # Refusing to execute Chief/IA for stability.
        if cop.cop_type in ['chief', 'detective']:
             return False, "Cannot Execute Special Agents"
        
        # Honest Cop replacement (Simpler, no brain)
        # This part was not in original main.py, so we stick to original behavior: 
        # Original main only allowed executing agents in 'corrupt_ids' or looked up in map but logic assumed corrupt cop for brain.
        return False, "Only Corrupt Cops can be executed in this version."
