#!/usr/bin/env python3
"""
Pre-Deployment Validation Script for Estate Planning Concierge v4.0
Run this before deployment to ensure all requirements are met
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

class DeploymentValidator:
    """Validate deployment readiness"""
    
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.is_ready = True
        
    def validate(self) -> bool:
        """Run all validation checks"""
        print("\n" + "=" * 70)
        print("ESTATE PLANNING CONCIERGE v4.0 - DEPLOYMENT READINESS CHECK")
        print("=" * 70)
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Required Files", self.check_required_files),
            ("Environment Setup", self.check_environment),
            ("Dependencies", self.check_dependencies),
            ("Module Imports", self.check_imports),
            ("Configuration", self.check_configuration),
            ("API Credentials", self.check_api_credentials),
            ("GitHub Assets", self.check_github_assets),
            ("YAML Files", self.check_yaml_files),
            ("No Duplicate Functions", self.check_no_duplicates)
        ]
        
        for check_name, check_func in checks:
            print(f"\n🔍 Checking: {check_name}")
            try:
                result, message = check_func()
                if result:
                    print(f"  ✅ {message}")
                    self.checks_passed.append(check_name)
                else:
                    print(f"  ❌ {message}")
                    self.checks_failed.append(check_name)
                    self.is_ready = False
            except Exception as e:
                print(f"  ❌ Error: {e}")
                self.checks_failed.append(check_name)
                self.is_ready = False
        
        self.print_summary()
        return self.is_ready
    
    def check_python_version(self) -> Tuple[bool, str]:
        """Check Python version compatibility"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            return True, f"Python {version.major}.{version.minor}.{version.micro} is compatible"
        return False, f"Python 3.8+ required, found {version.major}.{version.minor}"
    
    def check_required_files(self) -> Tuple[bool, str]:
        """Check if all required files exist"""
        required = [
            "deploy.py",
            "requirements.txt",
            ".env.example",
            "config.yaml",
            "modules/__init__.py",
            "modules/config.py",
            "modules/auth.py",
            "modules/notion_api.py",
            "modules/validation.py",
            "modules/exceptions.py",
            "modules/visuals.py",
            "modules/database.py",
            "modules/logging_config.py"
        ]
        
        missing = []
        for file in required:
            if not Path(file).exists():
                missing.append(file)
        
        if missing:
            return False, f"Missing files: {', '.join(missing[:3])}..."
        return True, f"All {len(required)} required files present"
    
    def check_environment(self) -> Tuple[bool, str]:
        """Check environment variables"""
        if Path(".env").exists():
            return True, ".env file exists (credentials configured)"
        elif Path(".env.example").exists():
            return False, ".env.example exists but .env not created - copy and configure it"
        return False, "No .env or .env.example found"
    
    def check_dependencies(self) -> Tuple[bool, str]:
        """Check if dependencies can be imported"""
        try:
            import requests
            import yaml
            from PIL import Image
            return True, "Core dependencies (requests, PyYAML, Pillow) are installed"
        except ImportError as e:
            missing = str(e).split("'")[1] if "'" in str(e) else "dependencies"
            return False, f"Missing dependency: {missing} - run 'pip install -r requirements.txt'"
    
    def check_imports(self) -> Tuple[bool, str]:
        """Check if all modules can be imported"""
        try:
            from modules.config import load_config
            from modules.auth import validate_token
            from modules.notion_api import throttle
            from modules.validation import sanitize_input
            from modules.exceptions import NotionAPIError
            from modules.visuals import get_estate_emoji
            from modules.database import create_database_entry
            from modules.logging_config import setup_logging
            return True, "All modules import successfully"
        except ImportError as e:
            return False, f"Module import error: {e}"
    
    def check_configuration(self) -> Tuple[bool, str]:
        """Check configuration validity"""
        try:
            import yaml
            with open("config.yaml", 'r') as f:
                config = yaml.safe_load(f)
            
            # Check critical settings
            api_version = config.get('notion_api_version')
            expected_version = '2022-06-28'
            
            # Handle both string and date formats from YAML
            if hasattr(api_version, 'strftime'):
                # It's a date object
                api_version = api_version.strftime('%Y-%m-%d')
            
            if str(api_version) != expected_version:
                return False, f"API version is {api_version}, should be {expected_version}"
            
            rate_limit = config.get('rate_limit_rps', 2.5)
            if rate_limit > 3:
                return False, f"Rate limit too high: {rate_limit} RPS (max 3)"
            
            return True, "Configuration is valid"
        except Exception as e:
            return False, f"Configuration error: {e}"
    
    def check_api_credentials(self) -> Tuple[bool, str]:
        """Check if API credentials are configured"""
        # Try to load from .env file if it exists
        if Path(".env").exists():
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                # If python-dotenv is not installed, try to parse manually
                with open(".env", 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
        
        token = os.getenv("NOTION_TOKEN")
        parent_id = os.getenv("NOTION_PARENT_PAGEID")
        
        if not token:
            return False, "NOTION_TOKEN not set in environment"
        if not parent_id:
            return False, "NOTION_PARENT_PAGEID not set in environment"
        
        # Validate token format
        if token.startswith("secret_") or token.startswith("ntn_"):
            return True, "API credentials configured and formatted correctly"
        return False, "NOTION_TOKEN has invalid format (should start with secret_ or ntn_)"
    
    def check_github_assets(self) -> Tuple[bool, str]:
        """Check GitHub assets configuration"""
        try:
            from modules.config import load_config
            config = load_config(Path("config.yaml"))
            
            github_url = config.get('visual_config', {}).get('github_assets_base_url')
            if github_url and 'github' in github_url:
                return True, f"GitHub assets configured: {github_url}"
            return False, "GitHub assets URL not configured"
        except Exception as e:
            return False, f"Cannot check GitHub assets: {e}"
    
    def check_yaml_files(self) -> Tuple[bool, str]:
        """Check YAML files validity"""
        yaml_dir = Path("split_yaml")
        if not yaml_dir.exists():
            return False, "split_yaml directory not found"
        
        yaml_files = list(yaml_dir.glob("*.yaml"))
        if len(yaml_files) < 10:
            return False, f"Only {len(yaml_files)} YAML files found (expected 20+)"
        
        return True, f"{len(yaml_files)} YAML configuration files found"
    
    def check_no_duplicates(self) -> Tuple[bool, str]:
        """Check for duplicate function definitions"""
        with open("deploy.py", 'r') as f:
            content = f.read()
        
        # Check if problematic functions are still locally defined
        if 'def validate_token(' in content and 'from modules.auth import validate_token' in content:
            return False, "validate_token is both imported and defined locally"
        
        return True, "No duplicate function conflicts detected"
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        
        total = len(self.checks_passed) + len(self.checks_failed)
        print(f"\n📊 Results: {len(self.checks_passed)}/{total} checks passed")
        
        if self.checks_passed:
            print(f"\n✅ Passed Checks:")
            for check in self.checks_passed:
                print(f"  • {check}")
        
        if self.checks_failed:
            print(f"\n❌ Failed Checks:")
            for check in self.checks_failed:
                print(f"  • {check}")
        
        print("\n" + "=" * 70)
        
        if self.is_ready:
            print("🎉 DEPLOYMENT READY!")
            print("✨ All checks passed. You can now run deploy.py")
            print("\n📝 To deploy:")
            print("  1. Ensure .env file has your Notion credentials")
            print("  2. Run: python deploy.py")
        else:
            print("⚠️  NOT READY FOR DEPLOYMENT")
            print(f"❌ Fix the {len(self.checks_failed)} failed checks above")
            print("\n📝 Next steps:")
            print("  1. Fix the issues listed above")
            print("  2. Run this validation again")
            print("  3. Only deploy when all checks pass")
        
        print("=" * 70)


def main():
    """Run deployment validation"""
    validator = DeploymentValidator()
    is_ready = validator.validate()
    
    # Exit with appropriate code
    sys.exit(0 if is_ready else 1)


if __name__ == "__main__":
    main()