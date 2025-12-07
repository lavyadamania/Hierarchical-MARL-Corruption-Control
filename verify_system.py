import os
import sys
import sqlite3

def check_file(path, description):
    if os.path.exists(path):
        print(f"✅ FOUND: {description} ({os.path.basename(path)})")
        return True
    else:
        print(f"❌ MISSING: {description} ({path})")
        return False

def main():
    print("--- 🕵️ CORRUPTION MARL SYSTEM VERIFICATION ---")
    
    root = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Check Directory Structure
    files_to_check = [
        ("main.py", "Main executable"),
        ("config.py", "Configuration file"),
        (os.path.join("database", "schema.sql"), "Database Schema"),
        (os.path.join("agents", "corrupt_cop.py"), "Agent Logic"),
        (os.path.join("visualization", "plotter.py"), "Plotter Logic")
    ]
    
    all_files_exist = True
    for rel_path, desc in files_to_check:
        if not check_file(os.path.join(root, rel_path), desc):
            all_files_exist = False
            
    if not all_files_exist:
        print("\n❌ CRITICAL: Some core files are missing. Please restore the project.")
        return

    # 2. Check Database
    db_path = os.path.join(root, "corruption.db")
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cops")
            count = cursor.fetchone()[0]
            print(f"✅ DATABASE: Connection successful. Found {count} agents in history.")
            conn.close()
        except Exception as e:
            print(f"❌ DATABASE ERROR: {e}")
    else:
        print("⚠️ DATABASE: Not found. Run 'main.py' to generate it.")

    # 3. Check Results
    results_dir = os.path.join(root, "results")
    expected_images = [
        "corruption_hierarchy.png",
        "success_rate.png",
        "cop_performance.png",
        "investigations.png",
        "witness_impact.png"
    ]
    
    missing_images = []
    if os.path.exists(results_dir):
        for img in expected_images:
            if not os.path.exists(os.path.join(results_dir, img)):
                missing_images.append(img)
        
        if not missing_images:
            print("✅ RESULTS: All 5 visualization graphs are present.")
        else:
            print(f"⚠️ RESULTS: Missing {len(missing_images)} graphs. Run simulation to generate them.")
    else:
        print("⚠️ RESULTS: 'results' folder not found.")

    print("\n--- INSTRUCTIONS ---")
    print("To run the FULL simulation, type:")
    print("   python main.py")
    print("--------------------")

if __name__ == "__main__":
    main()
