#!/usr/bin/env python3
"""Script de test des imports pour diagnostiquer les problèmes"""

import sys
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")
print()

print("Testing imports...")

try:
    from fastapi import FastAPI
    print("✅ FastAPI")
except Exception as e:
    print(f"❌ FastAPI: {e}")

try:
    from supabase_client import SupabaseClient
    print("✅ SupabaseClient")
except Exception as e:
    print(f"❌ SupabaseClient: {e}")

try:
    from legacy.open_wearables_integration import OpenWearablesIntegration
    print("✅ OpenWearablesIntegration")
except Exception as e:
    print(f"❌ OpenWearablesIntegration: {e}")

try:
    from legacy.data_normalizer import DataNormalizer
    print("✅ DataNormalizer")
except Exception as e:
    print(f"❌ DataNormalizer: {e}")

try:
    from legacy.webhook_receiver import WebhookReceiver
    print("✅ WebhookReceiver")
except Exception as e:
    print(f"❌ WebhookReceiver: {e}")

try:
    from correlation_engine import CorrelationEngine
    print("✅ CorrelationEngine")
except Exception as e:
    print(f"❌ CorrelationEngine: {e}")

print("\nTesting numpy/scipy (can be slow)...")
try:
    import numpy as np
    print(f"✅ numpy {np.__version__}")
except Exception as e:
    print(f"❌ numpy: {e}")

try:
    import scipy
    print(f"✅ scipy {scipy.__version__}")
except Exception as e:
    print(f"❌ scipy: {e}")

print("\nTesting baseline_calculator...")
try:
    from baseline_calculator import BaselineCalculator
    print("✅ BaselineCalculator")
except Exception as e:
    print(f"❌ BaselineCalculator: {e}")

print("\n✅ All critical imports successful!")
