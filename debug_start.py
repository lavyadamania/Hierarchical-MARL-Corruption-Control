import sys
import os

print("1. Importing config...")
try:
    import config
    print("   Success.")
except Exception as e:
    print(f"   FAILED: {e}")

print("2. Importing agents...")
try:
    from agents import CorruptCop, PoliceChief, IADetective
    print("   Success.")
except Exception as e:
    print(f"   FAILED: {e}")

print("3. Importing engine...")
try:
    from simulation_engine import SimulationEngine
    print("   Success.")
except Exception as e:
    print(f"   FAILED: {e}")

print("4. Importing app (flask)...")
try:
    import app
    print("   Success.")
except Exception as e:
    print(f"   FAILED: {e}")
