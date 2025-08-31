#!/usr/bin/env python3
"""
Test script to verify Estate Analytics database deployment
"""

import yaml
import json
from pathlib import Path

def test_yaml_parsing():
    """Test that the YAML file can be parsed correctly"""
    yaml_path = Path("split_yaml/10_databases_analytics.yaml")
    
    if not yaml_path.exists():
        print(f"❌ YAML file not found: {yaml_path}")
        return False
    
    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        print(f"✅ YAML file parsed successfully")
        
        # Check databases structure
        if "databases" not in data:
            print("❌ No 'databases' key found")
            return False
        
        databases = data["databases"]
        if not isinstance(databases, list):
            print("❌ 'databases' is not a list")
            return False
        
        print(f"✅ Found {len(databases)} databases")
        
        # Check Estate Analytics database
        estate_analytics = None
        for db in databases:
            if db.get("title") == "Estate Analytics":
                estate_analytics = db
                break
        
        if not estate_analytics:
            print("❌ Estate Analytics database not found")
            return False
        
        print("✅ Estate Analytics database found")
        
        # Check required properties
        required_props = ["Metric Name", "Section", "Category", "Value", "Target", "Progress %", "Completion Status"]
        properties = estate_analytics.get("properties", {})
        
        for prop in required_props:
            if prop not in properties:
                print(f"❌ Missing property: {prop}")
                return False
        
        print(f"✅ All {len(required_props)} required properties present")
        
        # Check formula properties
        formula_props = ["Progress %", "Completion Status"]
        for prop in formula_props:
            if properties[prop].get("type") != "formula":
                print(f"❌ {prop} is not a formula property")
                return False
            if "expression" not in properties[prop].get("formula", {}):
                print(f"❌ {prop} formula missing expression")
                return False
        
        print(f"✅ Formula properties configured correctly")
        
        # Check database entries
        if "database_entries" not in data:
            print("❌ No database_entries section")
            return False
        
        if "Estate Analytics" not in data["database_entries"]:
            print("❌ No entries for Estate Analytics")
            return False
        
        entries = data["database_entries"]["Estate Analytics"]
        print(f"✅ Found {len(entries)} initial entries for Estate Analytics")
        
        # Verify other databases
        expected_dbs = ["Estate Analytics", "Professional Coordination", "Crisis Management", "Memory Preservation"]
        found_dbs = [db.get("title") for db in databases]
        
        for expected in expected_dbs:
            if expected not in found_dbs:
                print(f"❌ Missing database: {expected}")
                return False
        
        print(f"✅ All {len(expected_dbs)} expected databases present")
        
        return True
        
    except Exception as e:
        print(f"❌ Error parsing YAML: {e}")
        return False

def check_deploy_script():
    """Verify deploy.py has the necessary modifications"""
    deploy_path = Path("deploy.py")
    
    if not deploy_path.exists():
        print(f"❌ deploy.py not found")
        return False
    
    with open(deploy_path, 'r') as f:
        content = f.read()
    
    # Check for key modifications
    checks = [
        ("Database list format handling", "isinstance(data[\"databases\"], list)"),
        ("Database entries merging", "database_entries"),
        ("Formula property support", "\"formula\""),
        ("Email property support", "\"email\""),
        ("Phone number property support", "\"phone_number\""),
        ("Checkbox property support", "\"checkbox\""),
        ("Icon support", "\"icon\""),
        ("Description support", "\"description\""),
    ]
    
    all_good = True
    for check_name, check_str in checks:
        if check_str in content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Not found")
            all_good = False
    
    return all_good

def main():
    print("=" * 60)
    print("Testing Estate Analytics Database Configuration")
    print("=" * 60)
    print()
    
    print("1. Testing YAML Configuration:")
    print("-" * 40)
    yaml_ok = test_yaml_parsing()
    print()
    
    print("2. Checking deploy.py Modifications:")
    print("-" * 40)
    deploy_ok = check_deploy_script()
    print()
    
    print("=" * 60)
    if yaml_ok and deploy_ok:
        print("✅ ALL TESTS PASSED - Ready for deployment!")
        print()
        print("Next steps:")
        print("1. Set environment variables:")
        print("   export NOTION_TOKEN='your_token_here'")
        print("   export NOTION_PARENT_PAGE_ID='your_page_id_here'")
        print()
        print("2. Run deployment:")
        print("   python deploy.py --dry-run  # Test first")
        print("   python deploy.py            # Actual deployment")
    else:
        print("❌ TESTS FAILED - Please fix issues before deployment")
    print("=" * 60)

if __name__ == "__main__":
    main()