#!/usr/bin/env python3
"""
Integration script to add approval gate mechanism to asset_generator.py
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


def patch_imports(content):
    """Add approval gate import"""
    
    if "from approval_gate import ApprovalGate" not in content:
        # Find the websocket_broadcaster import
        websocket_import = "from websocket_broadcaster import get_broadcaster"
        
        if websocket_import in content:
            # Add approval gate import after websocket import
            new_import = websocket_import + "\nfrom approval_gate import ApprovalGate"
            content = content.replace(websocket_import, new_import)
            print("✅ Added ApprovalGate import")
        else:
            print("⚠️ Could not find websocket import, adding at top")
            content = "from approval_gate import ApprovalGate\n" + content
    else:
        print("⏭️ ApprovalGate import already exists")
    
    return content


def patch_init(content):
    """Add approval gate initialization"""
    
    if "self.approval_gate = " not in content:
        # Find the broadcaster initialization
        broadcaster_init = "self.broadcaster = get_broadcaster()"
        
        if broadcaster_init in content:
            # Add approval gate after broadcaster
            approval_init = """self.broadcaster = get_broadcaster()
        
        # Initialize approval gate for batch approvals
        self.approval_gate = ApprovalGate(timeout_seconds=300)  # 5 minute timeout
        self.require_approval = True  # Can be configured
        self.approval_threshold = 10  # Require approval for batches > 10 items"""
            
            content = content.replace(broadcaster_init, approval_init)
            print("✅ Added ApprovalGate initialization")
        else:
            print("⚠️ Could not find broadcaster init location")
    else:
        print("⏭️ ApprovalGate already initialized")
    
    return content


def add_approval_method(content):
    """Add method to handle batch approval"""
    
    approval_method = '''
    async def request_batch_approval(self, items: List[Dict], batch_type: str = "generation") -> List[Dict]:
        """
        Request approval for a batch of items
        
        Args:
            items: List of items to approve
            batch_type: Type of batch (generation, sample, production)
        
        Returns:
            List of approved items only
        """
        if not self.require_approval:
            return items
        
        # Skip approval for small batches
        if len(items) <= self.approval_threshold:
            self.logger.info(f"Auto-approving {len(items)} items (below threshold)")
            return items
        
        self.logger.info(f"Requesting approval for {len(items)} items...")
        
        # Prepare items for approval
        approval_items = []
        for item in items:
            approval_items.append({
                'asset_name': item.get('page_title', item.get('title', 'Unknown')),
                'asset_type': item.get('asset_type', 'unknown'),
                'prompt': item.get('prompt', '')[:500] + '...' if item.get('prompt') else '',
                'estimated_cost': 0.04,  # Default cost per image
                'metadata': {
                    'original_item': item
                }
            })
        
        # Request approval via approval gate
        try:
            batch = await self.approval_gate.request_approval(
                items=approval_items,
                batch_id=f"{batch_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            # Get only approved items
            approved_items = self.approval_gate.get_approved_items(batch)
            
            # Extract original items from approved
            approved_originals = []
            for approved in approved_items:
                if approved.metadata and 'original_item' in approved.metadata:
                    # Apply any prompt modifications
                    original = approved.metadata['original_item']
                    if approved.prompt and not approved.prompt.endswith('...'):
                        original['prompt'] = approved.prompt
                    approved_originals.append(original)
            
            self.logger.info(f"Approved {len(approved_originals)} out of {len(items)} items")
            
            if len(approved_originals) == 0:
                self.logger.warning("No items approved - skipping generation")
            
            return approved_originals
            
        except Exception as e:
            self.logger.error(f"Approval gate error: {e}")
            # Fallback to auto-approve on error
            self.logger.info("Auto-approving due to approval gate error")
            return items
'''
    
    if "async def request_batch_approval" not in content:
        # Find a good place to add it (after check_control_flags if it exists)
        if "async def check_control_flags" in content:
            # Find the end of check_control_flags method
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "async def check_control_flags" in line:
                    # Find the next method or class end
                    for j in range(i+1, len(lines)):
                        if lines[j].strip().startswith("async def ") or lines[j].strip().startswith("def "):
                            # Insert before next method
                            lines.insert(j, approval_method)
                            break
                    break
            content = '\n'.join(lines)
        else:
            # Add after __init__ method
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "def __init__" in line:
                    # Find the end of __init__
                    indent_count = 0
                    for j in range(i+1, len(lines)):
                        if lines[j].strip().startswith("def "):
                            # Insert before next method
                            lines.insert(j, approval_method)
                            break
                    break
            content = '\n'.join(lines)
        
        print("✅ Added request_batch_approval method")
    else:
        print("⏭️ request_batch_approval already exists")
    
    return content


def patch_generate_samples(content):
    """Add approval gate to generate_samples"""
    
    # Find where we process the sample configs
    old_pattern = '''        # Progress bar for overall sample generation
        with tqdm(total=total_samples, desc="Generating Samples", unit="asset") as pbar:
            
            for asset_type, page_items in asset_configs:'''
    
    new_pattern = '''        # Request approval for all samples if needed
        all_items_for_approval = []
        for asset_type, page_items in asset_configs:
            for item in page_items:
                item['asset_type'] = asset_type
                all_items_for_approval.append(item)
        
        # Get approved items
        approved_items = await self.request_batch_approval(all_items_for_approval, "sample")
        
        # Reorganize approved items by type
        approved_by_type = {}
        for item in approved_items:
            asset_type = item.pop('asset_type')
            if asset_type not in approved_by_type:
                approved_by_type[asset_type] = []
            approved_by_type[asset_type].append(item)
        
        # Update asset_configs with only approved items
        asset_configs = [(k, v) for k, v in approved_by_type.items()]
        total_samples = sum(len(items) for _, items in asset_configs)
        
        # Progress bar for overall sample generation
        with tqdm(total=total_samples, desc="Generating Samples", unit="asset") as pbar:
            
            for asset_type, page_items in asset_configs:'''
    
    if "request_batch_approval" not in content or "# Request approval for all samples" not in content:
        content = content.replace(old_pattern, new_pattern)
        print("✅ Added approval gate to generate_samples")
    else:
        print("⏭️ Approval gate already in generate_samples")
    
    return content


def patch_mass_production(content):
    """Add approval gate to mass production"""
    
    # Look for generate_mass_production method
    if "async def generate_mass_production" in content:
        # Find the section where we iterate through pages_by_type
        old_pattern = '''        with tqdm(total=total_assets, desc="Mass Production", unit="asset") as pbar:
            for asset_type, page_items in pages_by_type.items():'''
        
        new_pattern = '''        # Request approval for mass production
        all_items_for_approval = []
        for asset_type, page_items in pages_by_type.items():
            for item in page_items:
                item['asset_type'] = asset_type
                all_items_for_approval.append(item)
        
        # Get approved items
        self.logger.info(f"Requesting approval for {len(all_items_for_approval)} production items...")
        approved_items = await self.request_batch_approval(all_items_for_approval, "production")
        
        if not approved_items:
            self.logger.warning("No items approved for production")
            return []
        
        # Reorganize approved items by type
        approved_by_type = {}
        for item in approved_items:
            asset_type = item.pop('asset_type', 'unknown')
            if asset_type not in approved_by_type:
                approved_by_type[asset_type] = []
            approved_by_type[asset_type].append(item)
        
        # Update totals
        total_assets = sum(len(items) for items in approved_by_type.values())
        self.logger.info(f"Proceeding with {total_assets} approved items")
        
        with tqdm(total=total_assets, desc="Mass Production", unit="asset") as pbar:
            for asset_type, page_items in approved_by_type.items():'''
        
        if "# Request approval for mass production" not in content:
            content = content.replace(old_pattern, new_pattern)
            print("✅ Added approval gate to mass production")
        else:
            print("⏭️ Approval gate already in mass production")
    
    return content


def main():
    """Main integration script"""
    
    print("="*60)
    print("Approval Gate Integration Script")
    print("="*60)
    
    os.chdir("/Users/jonathanhollander/AI Code/Notion Template/Notion_Template_v4.0_Production/asset_generation")
    
    filepath = Path("asset_generator.py")
    
    if not filepath.exists():
        print("❌ asset_generator.py not found!")
        return 1
    
    # Create backup
    backup_path = backup_file(filepath)
    
    try:
        # Read the file
        with open(filepath, 'r') as f:
            content = f.read()
        
        print("\nApplying approval gate patches...")
        
        # Apply patches
        content = patch_imports(content)
        content = patch_init(content)
        content = add_approval_method(content)
        content = patch_generate_samples(content)
        content = patch_mass_production(content)
        
        # Add datetime import if needed
        if "from datetime import datetime" not in content:
            content = "from datetime import datetime\n" + content
            print("✅ Added datetime import")
        
        # Write back
        with open(filepath, 'w') as f:
            f.write(content)
        
        print("\n✅ Approval gate integration complete!")
        print(f"Backup saved at: {backup_path}")
        print("\nFeatures added:")
        print("- Approval gate for batches > 10 items")
        print("- 5-minute timeout for approval")
        print("- Partial approval support")
        print("- Prompt modification support")
        print("- Automatic fallback on errors")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, filepath)
        return 1


if __name__ == "__main__":
    sys.exit(main())