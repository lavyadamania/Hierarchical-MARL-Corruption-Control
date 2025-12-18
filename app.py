from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading
import time
import os
from simulation_engine import SimulationEngine
import config # For dynamic settings updates
from config import SEASON_LENGTH

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')

# Initialize Engine
engine = SimulationEngine()
thread = None
thread_lock = threading.Lock()
is_running = False
is_resetting = False

def background_thread():
    """Runs the simulation loop."""
    global is_running
    print("Background thread started")
    
    # UNLIMITED MODE: Runs until user presses Stop
    while is_running:
        step_data = engine.step()
        
        if step_data:  # Only emit if there's data (may be None in turbo mode)
            socketio.emit('update_data', step_data)
        
        # Dynamic delay based on turbo mode
        if engine.turbo_mode:
            time.sleep(0.001)  # 1ms - nearly instant for max speed
        else:
            time.sleep(0.1)    # 100ms - smooth visualization
        
        if not step_data and not engine.turbo_mode:
            # Only stop on None if not in turbo mode
            is_running = False
            break
            
    # Stop reached
    # CRITICAL FIX: Do NOT save state if we are resetting (resetting wipes files)
    if not is_resetting:
        engine.save_state()
        socketio.emit('status_update', {'status': 'Stopped'})
    else:
        print("Reset triggered: Skipping save_state cleanup.")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def test_connect():
    # Send recent history to populate graphs on refresh
    try:
        rows = engine.db.fetch_all("SELECT episode, corruption_level, avg_wealth, chief_wealth FROM episode_stats ORDER BY episode DESC LIMIT 200")
        if rows:
            # Reverse to chronological order
            rows.reverse()
            history = [{'episode': r[0], 'corruption': r[1], 'avg_wealth': r[2], 'chief_wealth': r[3]} for r in rows]
            emit('init_history', history)
    except Exception as e:
        print(f"History fetch error: {e}")
        
    emit('status_update', {'status': 'Connected', 'episode': engine.global_episodes})

@socketio.on('start_simulation')
def start_simulation():
    global is_running, is_resetting, thread
    if not is_running:
        is_running = True
        is_resetting = False # Reset flag clear
        emit('status_update', {'status': 'Running'})
        with thread_lock:
            if thread is None:
                thread = socketio.start_background_task(background_thread)
            else:
                thread = socketio.start_background_task(background_thread)

@socketio.on('stop_simulation')
def stop_simulation():
    global is_running
    is_running = False
    emit('status_update', {'status': 'Stopping...'})

@socketio.on('reset_simulation')
def reset_simulation():
    global is_running, is_resetting
    is_running = False
    is_resetting = True # Prevent background thread from saving
    
    # Wait for thread to stop (Poll for 2 seconds max)
    for _ in range(20):
        if not is_running: 
            # Ideally we check thread.is_alive() but socketio manages it differently
            break
        time.sleep(0.1)
    
    time.sleep(1.0) # Extra safety buffer for DB locks

    # Wipe files (Best Effort)
    print("🧹 WIPING MEMORY...")
    try:
        # Delete database
        if os.path.exists(config.DB_PATH): 
            try: 
                os.remove(config.DB_PATH)
                print(f"✓ Deleted database: {config.DB_PATH}")
            except Exception as e: 
                print(f"✗ Failed to delete DB: {e}")
        
        # Delete training state
        state_file = os.path.join(config.PROJECT_ROOT, 'training_state.json')
        if os.path.exists(state_file): 
            os.remove(state_file)
            print(f"✓ Deleted training state")
        
        # Delete ALL brain files using absolute path
        import glob
        brain_pattern = os.path.join(config.BRAIN_DIR, '*.pth')
        brain_files = glob.glob(brain_pattern)
        deleted_count = 0
        
        for f in brain_files:
            try: 
                os.remove(f)
                deleted_count += 1
            except Exception as e:
                print(f"✗ Failed to delete {os.path.basename(f)}: {e}")
        
        print(f"✓ Deleted {deleted_count} brain files from {config.BRAIN_DIR}")
        
    except Exception as e:
        print(f"Error resetting files: {e}")

    # Engine Reset (The Authority)
    engine.reset()
    is_resetting = False
    is_running = False
    emit('status_update', {'status': f'Reset Complete - Wiped {deleted_count} brain files', 'episode': 0})
    emit('clear_charts')

@socketio.on('execute_agent')
def on_execute_agent(data):
    agent_id = int(data.get('id', -1))
    success, msg = engine.execute_agent(agent_id)
    if success:
        emit('status_update', {'status': f"Executed Officer {agent_id}"})
    else:
        emit('status_update', {'status': f"Failed: {msg}"})

@socketio.on('update_settings')
def on_update_settings(data):
    """
    Supervisor Override: Modify Simulation Physics at Runtime.
    Data format: {'setting': 'WITNESS_RISK_FACTOR', 'value': 0.5}
    """
    key = data.get('setting')
    value = data.get('value')
    
    if hasattr(config, key):
        # Type Check & Conversion
        try:
            old_type = type(getattr(config, key))
            if old_type == int:
                new_value = int(value)
            elif old_type == float:
                new_value = float(value)
            else:
                new_value = value
            
            setattr(config, key, new_value)
            print(f"🔧 CONFIG UPDATED: {key} -> {new_value}")
            emit('status_update', {'status': f"Set {key} to {new_value}"})
        except Exception as e:
            emit('status_update', {'status': f"Error setting {key}: {e}"})
    else:
        emit('status_update', {'status': f"Unknown Setting: {key}"})

@socketio.on('toggle_turbo')
def on_toggle_turbo(data):
    """
    Toggle turbo mode for maximum speed training.
    Data format: {'enabled': true/false}
    """
    enabled = data.get('enabled', False)
    engine.set_turbo_mode(enabled)
    mode_text = "TURBO (Max Speed)" if enabled else "NORMAL (Visualization)"
    print(f"🚀 MODE CHANGE: {mode_text}")
    emit('status_update', {'status': f"Mode: {mode_text}", 'turbo': enabled})
if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
