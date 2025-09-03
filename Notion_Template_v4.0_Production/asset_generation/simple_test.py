#!/usr/bin/env python3
"""
Simple test for import issues
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

print("Testing imports...")

try:
    from generation_manager import GenerationManager
    print("✅ GenerationManager imported successfully")
except Exception as e:
    print(f"❌ GenerationManager import failed: {e}")
    sys.exit(1)

try:
    from utils.session_manager import SessionManager
    print("✅ SessionManager imported successfully")
except Exception as e:
    print(f"❌ SessionManager import failed: {e}")

try:
    from services.prompt_competition_service import PromptCompetitionService
    print("✅ PromptCompetitionService imported successfully")
except Exception as e:
    print(f"❌ PromptCompetitionService import failed: {e}")

try:
    from utils.sync_database_manager import SyncAssetDatabase
    print("✅ SyncAssetDatabase imported successfully")
except Exception as e:
    print(f"❌ SyncAssetDatabase import failed: {e}")

try:
    from quality_scorer import QualityScorer
    print("✅ QualityScorer imported successfully")
except Exception as e:
    print(f"❌ QualityScorer import failed: {e}")

print("✅ All individual imports work!")

try:
    from review_dashboard import ReviewDashboard
    print("✅ ReviewDashboard imported successfully")
except Exception as e:
    print(f"❌ ReviewDashboard import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("🎉 All imports successful!")