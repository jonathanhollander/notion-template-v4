#!/usr/bin/env python3
"""
Script to integrate WebSocket visibility into the asset generation system
Run this to patch the asset_generator.py with visibility features
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime


def backup_file(filepath):
    """Create a backup of the file before modifying"""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path


def add_visibility_methods():
    """Add the visibility helper methods to asset_generator.py"""
    
    visibility_methods = '''
    async def check_control_flags(self):
        """Check for pause/abort/skip commands from WebSocket"""
        
        # Check if paused
        while self.broadcaster.generation_paused:
            self.broadcaster.emit_log("⏸️ Generation paused", "info")
            await asyncio.sleep(1)
        
        # Check if aborted
        if hasattr(self.broadcaster, 'generation_aborted') and self.broadcaster.generation_aborted:
            self.broadcaster.emit_log("🛑 Generation aborted", "error")
            raise Exception("Generation aborted by user")
        
        # Check if skip requested
        if hasattr(self.broadcaster, 'skip_current') and self.broadcaster.skip_current:
            self.broadcaster.skip_current = False
            return "skip"
        
        # Apply speed control
        speed = self.broadcaster.generation_speed
        if speed == "slow":
            await asyncio.sleep(2)
        elif speed == "fast":
            pass  # No delay
        else:  # normal
            await asyncio.sleep(0.5)
        
        return None
'''
    
    # Read the file
    filepath = Path("asset_generator.py")
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Find a good place to insert (after the __init__ method)
    insert_index = None
    for i, line in enumerate(lines):
        if "def setup_logging(self)" in line:
            insert_index = i
            break
    
    if insert_index:
        # Insert the new method before setup_logging
        lines.insert(insert_index, visibility_methods)
        
        with open(filepath, 'w') as f:
            f.writelines(lines)
        
        print("✅ Added check_control_flags method")
        return True
    
    return False


def patch_generate_samples():
    """Patch the generate_samples method with visibility calls"""
    
    filepath = Path("asset_generator.py")
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Add visibility at the start of generate_samples
    old_start = '''    async def generate_samples(self):
        """Generate sample assets for review across ALL asset categories"""
        self.logger.info("\\n" + "="*80)
        self.logger.info("STAGE 1: COMPREHENSIVE SAMPLE GENERATION")
        self.logger.info("="*80)'''
    
    new_start = '''    async def generate_samples(self):
        """Generate sample assets for review across ALL asset categories"""
        self.logger.info("\\n" + "="*80)
        self.logger.info("STAGE 1: COMPREHENSIVE SAMPLE GENERATION")
        self.logger.info("="*80)
        
        # Start visibility session
        self.broadcaster.start_generation(mode="sample", total_items=0)
        self.broadcaster.update_pipeline_stage("discovery")
        self.broadcaster.emit_log("📁 Discovering assets from YAML files...", "info")'''
    
    if old_start in content:
        content = content.replace(old_start, new_start)
        print("✅ Patched generate_samples start")
    
    # Add visibility in the generation loop
    old_loop = '''                for i, page_data in enumerate(page_items, 1):
                    prompt = page_data['prompt']
                    # Pass page data for metadata
                    task = self.generate_asset_with_metadata(asset_type, prompt, i, count, page_data)
                    tasks.append(task)'''
    
    new_loop = '''                for i, page_data in enumerate(page_items, 1):
                    # Check for pause/abort controls
                    if await self.check_control_flags() == "skip":
                        self.broadcaster.emit_log(f"⏭️ Skipped {page_data.get('page_title')}", "warning")
                        continue
                    
                    # Notify prompt generation
                    asset_name = page_data.get('page_title', f'{asset_type}_{i}')
                    self.broadcaster.update_pipeline_stage("prompt")
                    self.broadcaster.prompt_generating_start(asset_name, 'OpenRouter')
                    
                    prompt = page_data['prompt']
                    
                    # Emit prompt created
                    self.broadcaster.prompt_created(
                        asset_name=asset_name,
                        model='OpenRouter',
                        prompt=prompt[:500] + '...',
                        confidence=95.0,
                        selected=True
                    )
                    
                    # Update to image stage
                    self.broadcaster.update_pipeline_stage("image")
                    
                    # Pass page data for metadata
                    task = self.generate_asset_with_metadata(asset_type, prompt, i, count, page_data)
                    tasks.append(task)'''
    
    if old_loop in content:
        content = content.replace(old_loop, new_loop)
        print("✅ Patched generate_samples loop")
    
    # Add cost tracking in results processing
    old_results = '''                for result in results:
                    if result:
                        samples.append(result)
                        self.generated_assets.append(result)
                    pbar.update(1)'''
    
    new_results = '''                for result in results:
                    if result:
                        samples.append(result)
                        self.generated_assets.append(result)
                        
                        # Update cost tracking
                        item_cost = result.get('cost', 0.04)
                        self.broadcaster.update_cost(
                            item_cost=item_cost,
                            total_cost=self.total_cost,
                            images_completed=len(self.generated_assets)
                        )
                        
                        # Update progress
                        self.broadcaster.update_progress(
                            len(self.generated_assets),
                            total_samples,
                            f"Generated {result.get('filename', 'asset')}"
                        )
                    pbar.update(1)'''
    
    if old_results in content:
        content = content.replace(old_results, new_results)
        print("✅ Patched generate_samples results processing")
    
    # Add completion at the end
    old_end = '''        self.logger.info("\\n" + "="*80)
        self.logger.info(f"SAMPLE GENERATION COMPLETE")
        self.logger.info(f"Generated: {len(samples)} samples")'''
    
    new_end = '''        # Complete the session
        self.broadcaster.update_pipeline_stage("save")
        self.broadcaster.complete_generation()
        
        self.logger.info("\\n" + "="*80)
        self.logger.info(f"SAMPLE GENERATION COMPLETE")
        self.logger.info(f"Generated: {len(samples)} samples")'''
    
    if old_end in content:
        content = content.replace(old_end, new_end)
        print("✅ Patched generate_samples completion")
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    return True


def patch_generate_asset_with_metadata():
    """Patch generate_asset_with_metadata to emit visibility events"""
    
    filepath = Path("asset_generator.py")
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find and patch the method
    old_method_start = '''    async def generate_asset_with_metadata(self, asset_type: str, prompt: str, index: int, total: int, page_data: Dict) -> Optional[Dict]:
        """Generate asset with metadata from page data"""
        try:
            # Generate the asset
            result = await self.generate_asset(asset_type, prompt, index, total)'''
    
    new_method_start = '''    async def generate_asset_with_metadata(self, asset_type: str, prompt: str, index: int, total: int, page_data: Dict) -> Optional[Dict]:
        """Generate asset with metadata from page data"""
        asset_name = page_data.get('page_title', f'{asset_type}_{index}')
        
        # Emit generation start
        self.broadcaster.emit('image_generating', {
            'asset_name': asset_name,
            'asset_type': asset_type,
            'status': 'starting',
            'model': self.config['replicate']['model']
        })
        
        try:
            # Generate the asset
            result = await self.generate_asset(asset_type, prompt, index, total)'''
    
    if old_method_start in content:
        content = content.replace(old_method_start, new_method_start)
        print("✅ Patched generate_asset_with_metadata start")
    
    # Add completion event
    old_return = '''                result['metadata'] = {
                    'page_title': page_data.get('page_title', 'Unknown'),
                    'page_icon': page_data.get('page_icon', ''),
                    'page_description': page_data.get('description', ''),
                    'asset_category': asset_type,
                    'yaml_source': page_data.get('yaml_source', 'unknown')
                }
            
            return result'''
    
    new_return = '''                result['metadata'] = {
                    'page_title': page_data.get('page_title', 'Unknown'),
                    'page_icon': page_data.get('page_icon', ''),
                    'page_description': page_data.get('description', ''),
                    'asset_category': asset_type,
                    'yaml_source': page_data.get('yaml_source', 'unknown')
                }
                
                # Emit completion
                self.broadcaster.emit('image_completed', {
                    'asset_name': asset_name,
                    'file_path': result.get('filename'),
                    'generation_time': result.get('generation_time', 0),
                    'cost': result.get('cost', 0.04)
                })
            
            return result'''
    
    if old_return in content:
        content = content.replace(old_return, new_return)
        print("✅ Patched generate_asset_with_metadata completion")
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    return True


def main():
    """Main integration script"""
    
    print("="*60)
    print("WebSocket Visibility Integration Script")
    print("="*60)
    
    os.chdir("/Users/jonathanhollander/AI Code/Notion Template/Notion_Template_v4.0_Production/asset_generation")
    
    # Check if asset_generator.py exists
    if not Path("asset_generator.py").exists():
        print("❌ asset_generator.py not found!")
        return 1
    
    # Create backup
    backup_path = backup_file("asset_generator.py")
    
    try:
        # Apply patches
        print("\nApplying visibility patches...")
        
        # Add helper methods
        if not add_visibility_methods():
            print("⚠️ Could not add helper methods (may already exist)")
        
        # Patch main methods
        patch_generate_samples()
        patch_generate_asset_with_metadata()
        
        print("\n✅ Integration complete!")
        print(f"Backup saved at: {backup_path}")
        print("\nTo test the integration:")
        print("1. Start the web server: python review_dashboard.py")
        print("2. Open http://localhost:4500/enhanced")
        print("3. Run: python asset_generator.py --test-pages 3")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, "asset_generator.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())