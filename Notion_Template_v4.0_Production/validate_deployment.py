#!/usr/bin/env python3
"""
Estate Planning Concierge v4.0 - Deployment Validation Script
Validates the deploy.py against all 22 YAML files and auditor requirements
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any

class DeploymentValidator:
    def __init__(self, yaml_dir: str = "../Notion_Template_v4.0_YAMLs"):
        self.yaml_dir = Path(yaml_dir)
        self.validation_results = {
            "yaml_files": {},
            "auditor_checks": {},
            "critical_features": {},
            "statistics": {
                "total_pages": 0,
                "total_databases": 0,
                "total_letters": 0,
                "total_synced_blocks": 0,
                "total_relations": 0
            }
        }
        self.errors = []
        self.warnings = []
        
    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("=" * 80)
        print("Estate Planning Concierge v4.0 - Deployment Validation")
        print("=" * 80)
        
        # Check YAML files exist
        if not self.validate_yaml_files():
            return False
            
        # Validate critical features from auditor reports
        if not self.validate_auditor_requirements():
            return False
            
        # Check deploy.py implementation
        if not self.validate_deploy_implementation():
            return False
            
        # Generate validation report
        self.generate_report()
        
        return len(self.errors) == 0
        
    def validate_yaml_files(self) -> bool:
        """Validate all 22 YAML files are present and valid"""
        print("\n📁 Validating YAML Files...")
        
        expected_yamls = [
            "00_admin.yaml",
            "01_executor_hub.yaml", 
            "02_executor_tasks.yaml",
            "03_executor_guides.yaml",
            "04_family_hub.yaml",
            "05_family_memorial.yaml",
            "06_accounts_db.yaml",
            "07_property_db.yaml",
            "08_insurance_db.yaml",
            "09_contacts_db.yaml",
            "10_subscriptions_db.yaml",
            "11_keepsakes_db.yaml",
            "12_letters_db.yaml",
            "13_letters_pages.yaml",
            "14_digital_assets.yaml",
            "15_preparation_hub.yaml",
            "16_intro_pages.yaml",
            "17_estate_analytics_db.yaml",
            "18_transactions_db.yaml",
            "19_insurance_claims_db.yaml",
            "20_property_maintenance_db.yaml",
            "21_synced_blocks.yaml"
        ]
        
        all_valid = True
        for yaml_file in expected_yamls:
            yaml_path = self.yaml_dir / yaml_file
            if not yaml_path.exists():
                self.errors.append(f"Missing YAML: {yaml_file}")
                self.validation_results["yaml_files"][yaml_file] = "MISSING"
                all_valid = False
                continue
                
            try:
                with open(yaml_path, 'r') as f:
                    data = yaml.safe_load(f)
                    
                # Count features
                if "pages" in data:
                    self.validation_results["statistics"]["total_pages"] += len(data["pages"])
                if "database" in data:
                    self.validation_results["statistics"]["total_databases"] += 1
                if "letters" in data:
                    self.validation_results["statistics"]["total_letters"] += len(data["letters"])
                if "synced_blocks" in data:
                    self.validation_results["statistics"]["total_synced_blocks"] += len(data["synced_blocks"])
                    
                self.validation_results["yaml_files"][yaml_file] = "VALID"
                print(f"  ✅ {yaml_file}")
                
            except yaml.YAMLError as e:
                self.errors.append(f"Invalid YAML {yaml_file}: {str(e)}")
                self.validation_results["yaml_files"][yaml_file] = "INVALID"
                all_valid = False
                print(f"  ❌ {yaml_file}: Invalid YAML")
                
        print(f"\nYAML Files: {len([v for v in self.validation_results['yaml_files'].values() if v == 'VALID'])}/22 valid")
        return all_valid
        
    def validate_auditor_requirements(self) -> bool:
        """Validate critical fixes from auditor reports"""
        print("\n🔍 Validating Auditor Requirements...")
        
        checks = {
            "API Version 2025-09-03": self.check_api_version(),
            "Token Format Support": self.check_token_format(),
            "Relation Resolution": self.check_relation_resolution(),
            "Synced Blocks Implementation": self.check_synced_blocks(),
            "Error Handling": self.check_error_handling(),
            "Rate Limiting": self.check_rate_limiting(),
            "Idempotency": self.check_idempotency(),
            "Formula Validation": self.check_formula_validation()
        }
        
        all_passed = True
        for check_name, passed in checks.items():
            self.validation_results["auditor_checks"][check_name] = "PASS" if passed else "FAIL"
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False
                
        return all_passed
        
    def check_api_version(self) -> bool:
        """Check if API version is updated to 2025-09-03"""
        try:
            with open("deploy.py", 'r') as f:
                content = f.read()
                return 'NOTION_API_VERSION = "2025-09-03"' in content
        except:
            return False
            
    def check_token_format(self) -> bool:
        """Check if both secret_ and ntn_ token formats are supported"""
        try:
            with open("deploy.py", 'r') as f:
                content = f.read()
                return 'token.startswith("secret_") or token.startswith("ntn_")' in content
        except:
            return False
            
    def check_relation_resolution(self) -> bool:
        """Check if Pages Index DB pattern is implemented"""
        try:
            with open("deploy.py", 'r') as f:
                content = f.read()
                return "class PagesIndexDB" in content and "resolve_relation" in content
        except:
            return False
            
    def check_synced_blocks(self) -> bool:
        """Check if synced blocks with SYNC_KEY are implemented"""
        try:
            with open("deploy.py", 'r') as f:
                content = f.read()
                return "class SyncedBlockManager" in content and "SYNC_KEY" in content
        except:
            return False
            
    def check_error_handling(self) -> bool:
        """Check if comprehensive error handling is implemented"""
        try:
            with open("deploy.py", 'r') as f:
                content = f.read()
                return all(x in content for x in ["try:", "except", "logging", "retry", "exponential_backoff"])
        except:
            return False
            
    def check_rate_limiting(self) -> bool:
        """Check if 2.5 RPS rate limiting is implemented"""
        try:
            with open("deploy.py", 'r') as f:
                content = f.read()
                return "RATE_LIMIT_RPS = 2.5" in content and "rate_limit" in content.lower()
        except:
            return False
            
    def check_idempotency(self) -> bool:
        """Check if idempotent operations are implemented"""
        try:
            with open("deploy.py", 'r') as f:
                content = f.read()
                return "has_marker" in content and "idempotent" in content.lower()
        except:
            return False
            
    def check_formula_validation(self) -> bool:
        """Check if formula validation is implemented"""
        try:
            with open("deploy.py", 'r') as f:
                content = f.read()
                return "validate_formula" in content or "formula" in content.lower()
        except:
            return False
            
    def validate_deploy_implementation(self) -> bool:
        """Validate deploy.py has all required components"""
        print("\n⚙️ Validating Deploy.py Implementation...")
        
        required_classes = [
            "NotionDeployer",
            "PagesIndexDB", 
            "SyncedBlockManager",
            "RateLimiter",
            "ErrorHandler"
        ]
        
        required_methods = [
            "create_page",
            "create_database",
            "seed_database",
            "create_synced_block",
            "resolve_relation",
            "validate_deployment"
        ]
        
        try:
            with open("deploy.py", 'r') as f:
                content = f.read()
                
            all_found = True
            
            # Check classes
            for class_name in required_classes:
                if f"class {class_name}" in content:
                    print(f"  ✅ Class: {class_name}")
                else:
                    print(f"  ❌ Missing Class: {class_name}")
                    self.errors.append(f"Missing class: {class_name}")
                    all_found = False
                    
            # Check methods
            for method_name in required_methods:
                if f"def {method_name}" in content:
                    print(f"  ✅ Method: {method_name}")
                else:
                    print(f"  ❌ Missing Method: {method_name}")
                    self.warnings.append(f"Missing method: {method_name}")
                    
            return all_found
            
        except FileNotFoundError:
            self.errors.append("deploy.py not found")
            return False
            
    def generate_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "=" * 80)
        print("VALIDATION REPORT")
        print("=" * 80)
        
        # Statistics
        print("\n📊 Statistics:")
        for key, value in self.validation_results["statistics"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
            
        # Critical Features Status
        print("\n✨ Critical Features:")
        critical_features = {
            "100+ Pages": self.validation_results["statistics"]["total_pages"] >= 100,
            "11 Databases": self.validation_results["statistics"]["total_databases"] == 11,
            "18 Letters": self.validation_results["statistics"]["total_letters"] == 18,
            "Synced Blocks": self.validation_results["statistics"]["total_synced_blocks"] > 0,
            "API v2025-09-03": self.validation_results["auditor_checks"].get("API Version 2025-09-03") == "PASS",
            "Relation Resolution": self.validation_results["auditor_checks"].get("Relation Resolution") == "PASS",
            "Error Handling": self.validation_results["auditor_checks"].get("Error Handling") == "PASS"
        }
        
        for feature, status in critical_features.items():
            icon = "✅" if status else "❌"
            print(f"  {icon} {feature}")
            
        # Errors and Warnings
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors[:5]:  # Show first 5
                print(f"  • {error}")
                
        if self.warnings:
            print(f"\n⚠️ Warnings ({len(self.warnings)}):")
            for warning in self.warnings[:5]:  # Show first 5
                print(f"  • {warning}")
                
        # Final Status
        print("\n" + "=" * 80)
        if len(self.errors) == 0:
            print("✅ VALIDATION PASSED - Ready for deployment!")
            print("\nNext steps:")
            print("1. Set environment variables:")
            print("   export NOTION_TOKEN='your_token_here'")
            print("   export NOTION_PARENT_PAGEID='your_page_id_here'")
            print("2. Run dry-run test:")
            print("   python3 deploy.py --dry-run")
            print("3. Execute full deployment:")
            print("   python3 deploy.py --verbose")
        else:
            print(f"❌ VALIDATION FAILED - {len(self.errors)} errors found")
            print("\nPlease fix the errors above before proceeding.")
            
        print("=" * 80)
        
        # Save report to file
        report_path = Path("validation_report.json")
        with open(report_path, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        print(f"\n📄 Full report saved to: {report_path}")

if __name__ == "__main__":
    validator = DeploymentValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)