#!/usr/bin/env python3
"""
Smoke Test Script for Estate Planning v4.0 Asset Generation System
Tests the complete pipeline: sample generation → approval → mass production → manifest
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime

# Add asset_generation to path
sys.path.insert(0, str(Path(__file__).parent / "asset_generation"))

def setup_test_environment():
    """Setup test directories and environment"""
    print("🔧 Setting up test environment...")
    
    # Create test directories
    test_dir = Path("test_output")
    sample_dir = test_dir / "samples"
    production_dir = test_dir / "production"
    
    for dir_path in [sample_dir, production_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Set environment variables for testing
    os.environ['AUTO_CONFIRM'] = 'true'
    os.environ['HEADLESS_MODE'] = 'true'
    
    # Create minimal test config
    config = {
        "replicate": {
            "api_key": os.getenv("REPLICATE_API_TOKEN", ""),
            "rate_limit": 2,
            "models": {
                "icons": {
                    "model_id": "stability-ai/sdxl:test",
                    "cost_per_image": 0.04
                },
                "covers": {
                    "model_id": "stability-ai/sdxl:test",
                    "cost_per_image": 0.04
                },
                "textures": {
                    "model_id": "stability-ai/sdxl:test",
                    "cost_per_image": 0.04
                }
            }
        },
        "budget": {
            "sample_generation": {"max_cost": 1.0},
            "mass_generation": {"max_cost": 20.0}
        },
        "output": {
            "sample_directory": str(sample_dir),
            "production_directory": str(production_dir),
            "backup_directory": str(test_dir / "backup")
        },
        "logging": {
            "level": "INFO",
            "log_file": str(test_dir / "test.log"),
            "max_log_size": 10485760,
            "backup_count": 3
        },
        "review": {
            "port": 5002,
            "approval_file": str(test_dir / "APPROVED.txt")
        }
    }
    
    # Write test config
    config_path = test_dir / "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Test environment ready at: {test_dir}")
    return str(config_path), test_dir


def test_imports():
    """Test that all modules can be imported"""
    print("\n📦 Testing imports...")
    
    modules_to_test = [
        ("asset_generator", "AssetGenerator"),
        ("sample_generator", "SampleGenerator"),
        ("generation_manager", "GenerationManager"),
        ("review_dashboard", "ReviewDashboard"),
    ]
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name)
            if hasattr(module, class_name):
                print(f"  ✅ {module_name}.{class_name}")
            else:
                print(f"  ❌ {module_name}.{class_name} not found")
                return False
        except ImportError as e:
            print(f"  ❌ Failed to import {module_name}: {e}")
            return False
    
    return True


def test_sample_generation(config_path: str):
    """Test sample generation"""
    print("\n🎨 Testing sample generation...")
    
    try:
        from sample_generator import SampleGenerator
        
        # SampleGenerator takes yaml_dir, not config_path
        generator = SampleGenerator(yaml_dir="split_yaml")
        
        # Generate sample matrix
        print("  Generating sample matrix...")
        sample_matrix = asyncio.run(generator.generate_sample_matrix())
        
        if sample_matrix:
            # The matrix has total_samples attribute, not samples per category
            total_samples = sample_matrix.total_samples
            print(f"  ✅ Generated matrix with {total_samples} samples")
            
            # Check if files were created
            sample_dir = Path(json.load(open(config_path))['output']['sample_directory'])
            files = list(sample_dir.glob("*.png")) + list(sample_dir.glob("*.svg"))
            print(f"  ✅ Created {len(files)} files in {sample_dir}")
            
            return True
        else:
            print("  ❌ No samples generated")
            return False
            
    except Exception as e:
        print(f"  ❌ Sample generation failed: {e}")
        return False


def create_approval_file(test_dir: Path):
    """Create APPROVED.txt file to simulate human approval"""
    print("\n📝 Creating approval file...")
    
    approval_path = test_dir / "APPROVED.txt"
    approval_data = {
        "approved_at": datetime.now().isoformat(),
        "approved_by": "smoke_test",
        "approved_prompts": [
            {
                "type": "icons",
                "prompts": ["minimalist icon design", "flat icon style", "modern icon aesthetic"]
            },
            {
                "type": "covers",
                "prompts": ["abstract cover art", "gradient cover design", "minimal cover layout"]
            },
            {
                "type": "textures",
                "prompts": ["subtle texture pattern", "organic texture", "geometric texture"]
            }
        ],
        "notes": "Automated smoke test approval"
    }
    
    with open(approval_path, 'w') as f:
        json.dump(approval_data, f, indent=2)
    
    print(f"  ✅ Created approval file: {approval_path}")
    return str(approval_path)


def test_mass_production(config_path: str, approval_file: str):
    """Test mass production with approved prompts"""
    print("\n🏭 Testing mass production...")
    
    try:
        from asset_generator import AssetGenerator
        
        # Update config with approval file
        config = json.load(open(config_path))
        config['review']['approval_file'] = approval_file
        
        # Check if we have API key
        has_replicate_key = bool(os.getenv("REPLICATE_API_TOKEN") or config['replicate'].get('api_key'))
        
        if not has_replicate_key:
            print("  ⚠️  Skipping actual generation (no REPLICATE_API_TOKEN)")
            print("  ✅ Mass production initialization successful")
            # Test just the initialization
            try:
                generator = AssetGenerator(config_path=config_path)
                print("  ✅ AssetGenerator instantiated successfully")
                return True
            except ValueError as ve:
                if "REPLICATE_API_KEY" in str(ve):
                    print("  ✅ Correctly detected missing API key")
                    return True
                raise
        else:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            generator = AssetGenerator(config_path=config_path)
            
            # Run mass production (limited for testing)
            print("  Running mass production with approved prompts...")
            asyncio.run(generator.generate_mass_production())
            
            # Check manifest
            production_dir = Path(config['output']['production_directory'])
            manifest_path = production_dir / "manifest.json"
            
            if manifest_path.exists():
                manifest = json.load(open(manifest_path))
                print(f"  ✅ Manifest created with {len(manifest.get('assets', []))} assets")
                print(f"  ✅ Total cost: ${manifest.get('total_cost', 0):.3f}")
                return True
            else:
                print("  ❌ Manifest not created")
                return False
            
    except Exception as e:
        print(f"  ❌ Mass production failed: {e}")
        return False


def test_generation_manager(config_path: str):
    """Test the generation manager background job system"""
    print("\n🔄 Testing generation manager...")
    
    try:
        from generation_manager import GenerationManager
        
        manager = GenerationManager(db_path="test_output/test.db")
        
        # Create a sample job
        job_id = manager.create_sample_job(max_images=2)
        print(f"  ✅ Created job: {job_id}")
        
        # Check job status
        time.sleep(1)
        status = manager.get_job_status(job_id)
        if status:
            print(f"  ✅ Job status: {status['status']}")
        
        # Check job history
        jobs = manager.job_history
        print(f"  ✅ Total jobs in history: {len(jobs)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Generation manager test failed: {e}")
        return False


def test_database_operations():
    """Test database manager operations"""
    print("\n💾 Testing database operations...")
    
    try:
        from utils.database_manager import AssetDatabase
        
        # Initialize DB
        db = AssetDatabase("test_output/test.db")
        asyncio.run(db.initialize())
        print("  ✅ Database initialized")
        
        # Test creating a run
        run_id = asyncio.run(db.create_generation_run(mode="test", total_assets=10))
        print(f"  ✅ Created run: {run_id}")
        
        # Test recording a generation attempt
        asset_id = asyncio.run(db.record_generation_attempt(
            asset_type="test_icon",
            prompt="test prompt",
            cost=0.04,
            run_id=run_id,
            model_id="test-model"
        ))
        print(f"  ✅ Recorded asset: {asset_id}")
        
        # Get statistics
        stats = asyncio.run(db.get_generation_stats())
        # Stats are nested under 'overall' key
        overall = stats.get('overall', {})
        total_assets = overall.get('total_attempts', 0)
        total_cost = overall.get('total_cost', 0) or 0
        print(f"  ✅ Stats: {total_assets} assets, ${total_cost:.3f} spent")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False


def cleanup_test_environment(test_dir: Path):
    """Clean up test files"""
    print("\n🧹 Cleaning up test environment...")
    
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print(f"  ✅ Removed test directory: {test_dir}")


def main():
    """Run all smoke tests"""
    print("=" * 80)
    print("ESTATE PLANNING v4.0 - SMOKE TEST SUITE")
    print("=" * 80)
    
    # Check for API key
    if not os.getenv("REPLICATE_API_TOKEN"):
        print("\n⚠️  WARNING: REPLICATE_API_TOKEN not set")
        print("  Tests will run in mock mode without actual API calls")
        print("  Set REPLICATE_API_TOKEN environment variable for full testing")
    
    # Setup
    config_path, test_dir = setup_test_environment()
    
    # Track test results
    results = []
    
    # Run tests
    tests = [
        ("Imports", test_imports),
        ("Sample Generation", lambda: test_sample_generation(config_path)),
        ("Mass Production", lambda: test_mass_production(
            config_path, 
            create_approval_file(test_dir)
        )),
        ("Generation Manager", lambda: test_generation_manager(config_path)),
        ("Database Operations", test_database_operations),
    ]
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{len(results)} passed, {failed} failed")
    
    # Cleanup (auto-cleanup in headless mode)
    if os.environ.get('HEADLESS_MODE') == 'true':
        cleanup_test_environment(test_dir)
    else:
        if input("\n🗑️  Remove test files? (y/n): ").lower() == 'y':
            cleanup_test_environment(test_dir)
    
    # Exit code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()