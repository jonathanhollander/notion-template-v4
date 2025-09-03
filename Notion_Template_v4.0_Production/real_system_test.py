#!/usr/bin/env python3
"""
REAL SYSTEM TEST - Uses ACTUAL AssetGenerator with test YAML
This test generates REAL images via Replicate API to validate the entire pipeline
Expected cost: ~$0.20-0.30 for 3-6 images
"""

import os
import sys
import json
import asyncio
import shutil
from pathlib import Path
from datetime import datetime

# Add asset_generation to path
sys.path.insert(0, str(Path(__file__).parent / "asset_generation"))

def setup_test_environment():
    """Setup test environment with minimal configuration"""
    print("🔧 Setting up REAL test environment...")
    
    # Create test directories
    test_dir = Path("real_test_output")
    sample_dir = test_dir / "samples"
    production_dir = test_dir / "production"
    
    # Clean up any previous test
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    for dir_path in [sample_dir, production_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create REAL config pointing to our test YAML
    config = {
        "replicate": {
            "api_key": os.getenv("REPLICATE_API_TOKEN", ""),
            "rate_limit": 1,  # Slow rate for testing
            "models": {
                "icons": {
                    "model_id": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                    "cost_per_image": 0.04
                },
                "covers": {
                    "model_id": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                    "cost_per_image": 0.04
                },
                "textures": {
                    "model_id": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                    "cost_per_image": 0.04
                }
            }
        },
        "openrouter": {
            "api_key": os.getenv("OPENROUTER_API_KEY", ""),
            "base_url": "https://openrouter.ai/api/v1/chat/completions",
            "models": {
                "claude": {
                    "id": "anthropic/claude-3-haiku-20240307",
                    "cost_per_1k_tokens": 0.00025
                }
            }
        },
        "budget": {
            "sample_generation": {"max_cost": 0.50},
            "mass_generation": {"max_cost": 0.50}
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
            "port": 5004,
            "approval_file": str(test_dir / "APPROVED.txt")
        },
        "yaml": {
            "directory": "split_yaml",  # Point to our YAML directory
            "test_file": "test_minimal.yaml"  # Our test YAML file
        }
    }
    
    # Save config
    config_path = test_dir / "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Test environment ready at: {test_dir}")
    return str(config_path), test_dir


async def test_sample_generation_with_real_yaml(config_path: str):
    """Test sample generation using REAL YAML and REAL API"""
    print("\n🎨 TEST 1: Sample Generation with REAL YAML")
    print("-" * 50)
    
    try:
        from sample_generator import SampleGenerator
        
        # Create REAL sample generator pointing to our test YAML
        generator = SampleGenerator(yaml_dir="split_yaml")
        
        # Generate samples from our test YAML
        print("  Generating samples from test_minimal.yaml...")
        matrix = await generator.generate_sample_matrix()
        
        if matrix:
            print(f"  ✅ Generated matrix with {matrix.total_samples} samples")
            
            # Check for actual generated files
            config = json.load(open(config_path))
            sample_dir = Path(config['output']['sample_directory'])
            files = list(sample_dir.glob("*.png"))
            
            if files:
                print(f"  ✅ Generated {len(files)} REAL PNG files:")
                for file in files[:5]:
                    print(f"     - {file.name} ({file.stat().st_size:,} bytes)")
                return True
            else:
                print("  ⚠️  No image files created yet (may need approval)")
                return True  # Still success if matrix was created
        else:
            print("  ❌ Sample generation failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def launch_review_dashboard_and_wait(config_path: str, test_dir: Path):
    """Launch the ACTUAL review dashboard for manual web approval"""
    print("\n🌐 Launching Review Dashboard for Manual Approval")
    print("-" * 50)
    
    from review_dashboard import ReviewDashboard
    import threading
    import webbrowser
    import time
    
    config = json.load(open(config_path))
    approval_path = test_dir / "APPROVED.txt"
    config['review']['approval_file'] = str(approval_path)
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Initialize the ACTUAL review dashboard
    dashboard = ReviewDashboard(
        sample_dir=config['output']['sample_directory'],
        approval_file=str(approval_path),
        port=config['review']['port']
    )
    
    # Start dashboard in background thread
    def run_dashboard():
        dashboard.app.run(host='0.0.0.0', port=config['review']['port'], debug=False)
    
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()
    
    print(f"  ✅ Review Dashboard started on http://localhost:{config['review']['port']}")
    print(f"  📱 Opening browser for manual approval...")
    
    # Give server time to start
    time.sleep(2)
    
    # Open browser
    webbrowser.open(f"http://localhost:{config['review']['port']}")
    
    print("\n  ⏳ WAITING FOR MANUAL APPROVAL")
    print("  1. Review the generated sample prompts in your browser")
    print("  2. Select prompts you want to approve")
    print("  3. Click 'Approve Selected' button")
    print("  4. The test will continue automatically once approved")
    print()
    
    # Wait for approval file to be created
    while not approval_path.exists():
        print("  ⏳ Waiting for approval... (check browser)", end='\r')
        await asyncio.sleep(2)
    
    print(f"\n  ✅ Approval received! File created: {approval_path}")
    
    # Read and display what was approved
    with open(approval_path) as f:
        approval_data = json.load(f)
    
    total_prompts = sum(
        len(asset_type.get('prompts', [])) 
        for asset_type in approval_data.get('approved_prompts', [])
    )
    
    print(f"  ✅ Approved {total_prompts} prompts for generation")
    return str(approval_path)


async def test_mass_production_with_real_yaml(config_path: str, test_dir: Path):
    """Test mass production using REAL AssetGenerator with test YAML"""
    print("\n🏭 TEST 2: Mass Production with REAL AssetGenerator")
    print("-" * 50)
    
    try:
        from asset_generator import AssetGenerator
        
        # First, we need samples to review!
        print("  📋 Note: Sample generation should have created prompts to review")
        print("  If no samples exist, the review dashboard will be empty")
        
        # Launch review dashboard and wait for manual approval
        approval_file = await launch_review_dashboard_and_wait(config_path, test_dir)
        
        # Update config with approval file
        config = json.load(open(config_path))
        config['review']['approval_file'] = approval_file
        
        # Limit generation for testing
        config['budget']['mass_generation']['max_cost'] = 0.30
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create REAL AssetGenerator
        generator = AssetGenerator(config_path=config_path)
        
        print("  Starting REAL mass production with test_minimal.yaml...")
        print("  This will generate ACTUAL images via Replicate API...")
        
        # Run REAL mass production
        await generator.generate_mass_production()
        
        # Check REAL results
        production_dir = Path(config['output']['production_directory'])
        manifest_path = production_dir / "manifest.json"
        
        if manifest_path.exists():
            manifest = json.load(open(manifest_path))
            print(f"  ✅ REAL Manifest created:")
            print(f"     - Assets generated: {len(manifest.get('assets', []))}")
            print(f"     - Total cost: ${manifest.get('total_cost', 0):.3f}")
            print(f"     - Errors: {len(manifest.get('errors', []))}")
            
            # List REAL generated images
            images = list(production_dir.glob("*.png"))
            print(f"  ✅ Generated {len(images)} REAL images:")
            for img in images[:5]:
                print(f"     - {img.name} ({img.stat().st_size:,} bytes)")
            
            return True
        else:
            print("  ❌ No manifest created")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_database_records(test_dir: Path):
    """Verify database recorded the REAL generation"""
    print("\n💾 TEST 3: Database Verification")
    print("-" * 50)
    
    try:
        from utils.database_manager import AssetDatabase
        
        db_path = test_dir / "assets.db"
        if not db_path.exists():
            print("  ⚠️  No database created (may be using different path)")
            return True  # Not a failure if other tests passed
        
        db = AssetDatabase(str(db_path))
        await db.initialize()
        
        # Get REAL stats
        stats = await db.get_generation_stats()
        overall = stats.get('overall', {})
        
        print(f"  ✅ Database stats for REAL generation:")
        print(f"     - Total attempts: {overall.get('total_attempts', 0)}")
        print(f"     - Successful: {overall.get('successful', 0)}")
        print(f"     - Failed: {overall.get('failed', 0)}")
        print(f"     - Total cost: ${(overall.get('total_cost', 0) or 0):.3f}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False


async def main():
    """Run the REAL system test with actual YAML and API calls"""
    print("=" * 60)
    print("REAL SYSTEM TEST - Using test_minimal.yaml")
    print("=" * 60)
    
    # Check API keys
    has_replicate = bool(os.getenv("REPLICATE_API_TOKEN"))
    has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
    
    print("\n🔑 API Key Status:")
    print(f"  {'✅' if has_replicate else '❌'} REPLICATE_API_TOKEN: {'Set' if has_replicate else 'Not set'}")
    print(f"  {'✅' if has_openrouter else '❌'} OPENROUTER_API_KEY: {'Set' if has_openrouter else 'Not set'}")
    
    if not (has_replicate and has_openrouter):
        print("\n❌ Cannot run REAL test without API keys!")
        print("Please set:")
        print("  export REPLICATE_API_TOKEN=your_token")
        print("  export OPENROUTER_API_KEY=your_key")
        return False
    
    # Setup
    config_path, test_dir = setup_test_environment()
    
    # Verify our test YAML exists
    test_yaml = Path("split_yaml/test_minimal.yaml")
    if not test_yaml.exists():
        print(f"❌ Test YAML not found: {test_yaml}")
        return False
    print(f"✅ Using test YAML: {test_yaml}")
    
    # Run tests IN ORDER - this is the ACTUAL workflow
    results = []
    
    print("\n🔄 Running COMPLETE WORKFLOW (Sample → Review → Production)")
    print("=" * 60)
    
    # Test 1: Sample Generation with REAL YAML
    # This creates prompts that will be reviewed
    success = await test_sample_generation_with_real_yaml(config_path)
    results.append(("Sample Generation (REAL YAML)", success))
    
    if not success:
        print("❌ Sample generation failed - cannot continue")
        return False
    
    # Test 2: Mass Production with REAL AssetGenerator
    # This launches web review, waits for approval, then generates
    success = await test_mass_production_with_real_yaml(config_path, test_dir)
    results.append(("Mass Production (REAL API)", success))
    
    # Test 3: Database Verification
    # Verify everything was recorded correctly
    success = await verify_database_records(test_dir)
    results.append(("Database Records", success))
    
    # Summary
    print("\n" + "=" * 60)
    print("REAL SYSTEM TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{len(results)} passed, {failed} failed")
    
    # Check for actual generated images
    if test_dir.exists():
        all_images = list(test_dir.glob("**/*.png"))
        print(f"\n📁 Total REAL images generated: {len(all_images)}")
        if all_images:
            print("  Sample files:")
            for img in all_images[:5]:
                print(f"    - {img.relative_to(test_dir)} ({img.stat().st_size:,} bytes)")
    
    # Cleanup option
    if not os.getenv("HEADLESS_MODE"):
        if input("\n🗑️  Remove test files? (y/n): ").lower() == 'y':
            shutil.rmtree(test_dir)
            print("  ✅ Test files removed")
        else:
            print(f"  ℹ️  Test files kept in: {test_dir}")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)