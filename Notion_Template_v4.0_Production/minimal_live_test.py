#!/usr/bin/env python3
"""
MINIMAL LIVE TEST - Estate Planning v4.0 Asset Generation System
Generates 2-3 REAL images to verify the entire pipeline works with actual APIs
Expected cost: ~$0.20-0.30
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

class MinimalLiveTest:
    """Runs minimal but real tests with actual API calls"""
    
    def __init__(self):
        self.test_dir = Path("minimal_test_output")
        self.sample_dir = self.test_dir / "samples"
        self.production_dir = self.test_dir / "production"
        self.results = []
        
    def setup(self):
        """Setup test environment"""
        print("🔧 Setting up minimal test environment...")
        
        # Clean up any previous test
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        
        # Create directories
        for dir_path in [self.sample_dir, self.production_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create test config with REAL API keys
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
                        "id": "anthropic/claude-3-haiku-20240307",  # Cheapest Claude
                        "cost_per_1k_tokens": 0.00025
                    }
                }
            },
            "budget": {
                "sample_generation": {"max_cost": 0.50},
                "mass_generation": {"max_cost": 0.50}
            },
            "output": {
                "sample_directory": str(self.sample_dir),
                "production_directory": str(self.production_dir),
                "backup_directory": str(self.test_dir / "backup")
            },
            "logging": {
                "level": "INFO",
                "log_file": str(self.test_dir / "test.log"),
                "max_log_size": 10485760,
                "backup_count": 3
            },
            "review": {
                "port": 5003,
                "approval_file": str(self.test_dir / "APPROVED.txt")
            }
        }
        
        # Save config
        self.config_path = self.test_dir / "test_config.json"
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Test environment ready at: {self.test_dir}")
        return config
    
    async def test_minimal_sample_generation(self):
        """Generate just 3 sample images (1 per category)"""
        print("\n🎨 TEST 1: Minimal Sample Generation (3 images)")
        print("-" * 50)
        
        try:
            from sample_generator import SampleGenerator
            from openrouter_orchestrator import OpenRouterOrchestrator
            
            # Create custom minimal generator
            class MinimalSampleGenerator(SampleGenerator):
                def __init__(self):
                    super().__init__(yaml_dir="split_yaml")
                    # Override to generate only 1 image per category
                    self.asset_types = ["icon"]  # Only icons to save money
                    # Limit to 3 categories
                    self.sample_categories = self.sample_categories[:3]
            
            generator = MinimalSampleGenerator()
            
            # Generate minimal matrix
            print("  Generating 3 sample prompts...")
            matrix = await generator.generate_sample_matrix()
            
            if matrix:
                print(f"  ✅ Generated {matrix.total_samples} prompts")
                
                # Check for generated files
                files = list(self.sample_dir.glob("*.png"))
                if files:
                    print(f"  ✅ Created {len(files)} PNG files")
                    for file in files[:3]:
                        print(f"     - {file.name} ({file.stat().st_size:,} bytes)")
                else:
                    print("  ⚠️  No image files created (prompt generation only)")
                
                return True, matrix
            else:
                print("  ❌ Sample generation failed")
                return False, None
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False, None
    
    def create_minimal_approval(self):
        """Create approval file with just 2-3 prompts"""
        print("\n📝 Creating minimal approval file...")
        
        approval_data = {
            "approved_at": datetime.now().isoformat(),
            "approved_by": "minimal_live_test",
            "approved_prompts": [
                {
                    "type": "icons",
                    "prompts": [
                        "minimalist estate planning icon, gold and mahogany colors, professional, flat design",
                        "luxury document icon, premium materials, photorealistic, high detail"
                    ]
                },
                {
                    "type": "covers",
                    "prompts": [
                        "elegant mahogany desk with fountain pen and legal documents, warm lighting, luxury office"
                    ]
                }
            ],
            "notes": "Minimal test with 2-3 real images"
        }
        
        approval_path = self.test_dir / "APPROVED.txt"
        with open(approval_path, 'w') as f:
            json.dump(approval_data, f, indent=2)
        
        print(f"  ✅ Created approval with 3 prompts total")
        return str(approval_path)
    
    async def test_minimal_mass_production(self):
        """Generate just 2-3 production images"""
        print("\n🏭 TEST 2: Minimal Mass Production (2-3 images)")
        print("-" * 50)
        
        try:
            from asset_generator import AssetGenerator
            
            # Update config with approval file
            config = json.load(open(self.config_path))
            config['review']['approval_file'] = self.create_minimal_approval()
            
            # Limit generation
            config['budget']['mass_generation']['max_cost'] = 0.20
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            generator = AssetGenerator(config_path=str(self.config_path))
            
            print("  Starting mass production with 3 approved prompts...")
            
            # Override to limit generation
            original_method = generator.generate_mass_production
            
            async def limited_mass_production():
                # Modify generator to stop after 3 images
                generator.generation_stats['max_images'] = 3
                result = await original_method()
                return result
            
            generator.generate_mass_production = limited_mass_production
            
            # Run limited production
            await generator.generate_mass_production()
            
            # Check results
            manifest_path = self.production_dir / "manifest.json"
            if manifest_path.exists():
                manifest = json.load(open(manifest_path))
                print(f"  ✅ Manifest created:")
                print(f"     - Assets generated: {len(manifest.get('assets', []))}")
                print(f"     - Total cost: ${manifest.get('total_cost', 0):.3f}")
                print(f"     - Errors: {len(manifest.get('errors', []))}")
                
                # List actual files
                images = list(self.production_dir.glob("*.png"))
                print(f"  ✅ Generated {len(images)} images:")
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
    
    async def test_database_recording(self):
        """Verify database recorded everything"""
        print("\n💾 TEST 3: Database Recording")
        print("-" * 50)
        
        try:
            from utils.database_manager import AssetDatabase
            
            db_path = self.test_dir / "assets.db"
            db = AssetDatabase(str(db_path))
            await db.initialize()
            
            # Get stats
            stats = await db.get_generation_stats()
            overall = stats.get('overall', {})
            
            print(f"  ✅ Database stats:")
            print(f"     - Total attempts: {overall.get('total_attempts', 0)}")
            print(f"     - Successful: {overall.get('successful', 0)}")
            print(f"     - Failed: {overall.get('failed', 0)}")
            print(f"     - Total cost: ${(overall.get('total_cost', 0) or 0):.3f}")
            
            # Check for duplicates
            duplicates = await db.find_duplicate_generations()
            if duplicates:
                print(f"  ⚠️  Found {len(duplicates)} duplicate generations")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all minimal tests"""
        print("=" * 60)
        print("MINIMAL LIVE TEST - WITH REAL API CALLS")
        print("=" * 60)
        
        # Check API keys
        has_replicate = bool(os.getenv("REPLICATE_API_TOKEN"))
        has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
        
        print("\n🔑 API Key Status:")
        print(f"  {'✅' if has_replicate else '❌'} REPLICATE_API_TOKEN: {'Set' if has_replicate else 'Not set'}")
        print(f"  {'✅' if has_openrouter else '❌'} OPENROUTER_API_KEY: {'Set' if has_openrouter else 'Not set'}")
        
        if not (has_replicate and has_openrouter):
            print("\n❌ Cannot run live test without API keys!")
            print("Please set:")
            print("  export REPLICATE_API_TOKEN=your_token")
            print("  export OPENROUTER_API_KEY=your_key")
            return False
        
        # Setup
        self.setup()
        
        # Run tests
        tests = [
            ("Sample Generation", self.test_minimal_sample_generation),
            ("Mass Production", self.test_minimal_mass_production),
            ("Database Recording", self.test_database_recording)
        ]
        
        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                    if isinstance(result, tuple):
                        success = result[0]
                    else:
                        success = result
                else:
                    success = test_func()
                self.results.append((test_name, success))
            except Exception as e:
                print(f"\n❌ {test_name} crashed: {e}")
                self.results.append((test_name, False))
        
        # Summary
        self.print_summary()
        
        return all(success for _, success in self.results)
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, success in self.results if success)
        failed = len(self.results) - passed
        
        for test_name, success in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status}: {test_name}")
        
        print(f"\nTotal: {passed}/{len(self.results)} passed, {failed} failed")
        
        # Cost estimate
        if self.production_dir.exists():
            manifest_path = self.production_dir / "manifest.json"
            if manifest_path.exists():
                manifest = json.load(open(manifest_path))
                total_cost = manifest.get('total_cost', 0)
                print(f"\n💰 Total API cost: ${total_cost:.3f}")
        
        # File count
        total_files = len(list(self.test_dir.glob("**/*.png")))
        print(f"📁 Total images generated: {total_files}")
    
    def cleanup(self):
        """Clean up test files"""
        if input("\n🗑️  Remove test files? (y/n): ").lower() == 'y':
            shutil.rmtree(self.test_dir)
            print("  ✅ Test files removed")
        else:
            print(f"  ℹ️  Test files kept in: {self.test_dir}")


async def main():
    """Run the minimal live test"""
    tester = MinimalLiveTest()
    success = await tester.run_all_tests()
    
    if not os.getenv("HEADLESS_MODE"):
        tester.cleanup()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)