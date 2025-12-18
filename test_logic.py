import torch
from agents.corrupt_cop import CorruptCop
import sys

# Set encoding to handle emojis
sys.stdout.reconfigure(encoding='utf-8')

def test_memory_logic():
    print("🔬 TESTING MEMORY LOGIC...")
    
    # 1. Init Agent
    agent = CorruptCop(99, "Test_Cop", "greedy", 50.0)
    
    # Dummy State
    state = {
        'witnesses': 0, 'ia_nearby': False, 'offer': 50000, 'severity': 1,
        'alert_level': 0, 'evidence_strength': 0, 'has_warrant': False,
        'gang_affiliated': False, 'seized_value': 0, 'suspect_aggression': 0
    }
    
    # --- CHECK 1: Initial State ---
    # Should be 0 wealth, 0 caught
    vec_initial = agent.get_state_vector(state, current_episode=100)
    # Indices: 10=Caught, 11=Wealth, 12=Recency, 13=Suspicion
    print(f"Initial Wealth (idx 11): {vec_initial[11]:.4f} (Expected 0.0)")
    assert vec_initial[11] == 0.0
    
    # --- CHECK 2: Wealth accumulation ---
    agent.total_money_earned = 100000 # Half of normalization max (200k)
    vec_wealthy = agent.get_state_vector(state, current_episode=100)
    print(f"Wealthy State (idx 11): {vec_wealthy[11]:.4f} (Expected 0.5)")
    assert 0.49 < vec_wealthy[11] < 0.51
    
    # --- CHECK 3: Getting Caught & Recency ---
    agent.times_caught = 1
    agent.last_caught_episode = 100
    
    # Immediate check (Episode 100, just caught)
    vec_caught_now = agent.get_state_vector(state, current_episode=100)
    print(f"Caught Recency (idx 12) @ Ep 100: {vec_caught_now[12]:.4f} (Expected 1.0)")
    assert vec_caught_now[12] == 1.0
    
    # Delayed check (Episode 350, 250 eps later) -> Should be 0.5 decay
    vec_caught_later = agent.get_state_vector(state, current_episode=350)
    print(f"Caught Recency (idx 12) @ Ep 350: {vec_caught_later[12]:.4f} (Expected 0.5)")
    assert 0.49 < vec_caught_later[12] < 0.51
    
    # Saved verification
    vec_caught_old = agent.get_state_vector(state, current_episode=1000)
    print(f"Caught Recency (idx 12) @ Ep 1000: {vec_caught_old[12]:.4f} (Expected 0.0)")
    assert vec_caught_old[12] == 0.0
    
    print("✅ TEST PASSED: Memory Logic is mathematically correct.")

if __name__ == "__main__":
    try:
        test_memory_logic()
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
