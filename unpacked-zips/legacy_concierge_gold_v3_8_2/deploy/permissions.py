"""Role-Based Permissions Module for Notion Deployment.

Implements advanced permission management with:
- Multiple user roles (Admin, Executor, Family, Advisor)
- Granular page/database access control
- Permission inheritance
- Audit logging
"""

import json
import logging
from typing import Dict, List, Any, Optional, Set
from enum import Enum
from datetime import datetime

from constants import *

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User role definitions for the Estate Planning system."""
    ADMIN = "admin"           # Full system access
    EXECUTOR = "executor"     # Manage estate execution
    FAMILY = "family"         # View family-related information
    ADVISOR = "advisor"       # Professional advisors (lawyers, accountants)
    VIEWER = "viewer"         # Read-only access
    

class PermissionLevel(Enum):
    """Permission levels for Notion content."""
    FULL_ACCESS = "full_access"       # Can edit, delete, share
    EDIT = "edit"                     # Can edit content
    COMMENT = "comment"               # Can comment only
    VIEW = "view"                     # Read-only access
    NO_ACCESS = "no_access"           # No access


class RolePermissionManager:
    """Manages role-based permissions for Notion deployment."""
    
    def __init__(self, config_file: str = "permissions_config.json"):
        """Initialize permission manager with configuration.
        
        Args:
            config_file: Path to permissions configuration file
        """
        self.config_file = config_file
        self.permissions = self._load_permissions()
        self.audit_log = []
        
    def _load_permissions(self) -> Dict[str, Any]:
        """Load permissions configuration."""
        default_permissions = self._get_default_permissions()
        
        try:
            with open(self.config_file, 'r') as f:
                custom_permissions = json.load(f)
                # Merge custom with defaults
                return {**default_permissions, **custom_permissions}
        except FileNotFoundError:
            logger.info(f"No custom permissions file found, using defaults")
            return default_permissions
        except json.JSONDecodeError as e:
            logger.error(f"Invalid permissions config: {e}")
            return default_permissions
    
    def _get_default_permissions(self) -> Dict[str, Any]:
        """Define default permission structure."""
        return {
            "roles": {
                UserRole.ADMIN.value: {
                    "description": "System administrator with full access",
                    "permissions": {
                        "pages": PermissionLevel.FULL_ACCESS.value,
                        "databases": PermissionLevel.FULL_ACCESS.value,
                        "settings": PermissionLevel.FULL_ACCESS.value,
                        "users": PermissionLevel.FULL_ACCESS.value
                    },
                    "accessible_hubs": ["*"]  # All hubs
                },
                UserRole.EXECUTOR.value: {
                    "description": "Estate executor with management access",
                    "permissions": {
                        "pages": PermissionLevel.EDIT.value,
                        "databases": PermissionLevel.EDIT.value,
                        "settings": PermissionLevel.VIEW.value,
                        "users": PermissionLevel.VIEW.value
                    },
                    "accessible_hubs": ["executor_hub", "preparation_hub"]
                },
                UserRole.FAMILY.value: {
                    "description": "Family members with limited access",
                    "permissions": {
                        "pages": PermissionLevel.VIEW.value,
                        "databases": PermissionLevel.VIEW.value,
                        "settings": PermissionLevel.NO_ACCESS.value,
                        "users": PermissionLevel.NO_ACCESS.value
                    },
                    "accessible_hubs": ["family_hub"]
                },
                UserRole.ADVISOR.value: {
                    "description": "Professional advisors with document access",
                    "permissions": {
                        "pages": PermissionLevel.COMMENT.value,
                        "databases": PermissionLevel.VIEW.value,
                        "settings": PermissionLevel.NO_ACCESS.value,
                        "users": PermissionLevel.NO_ACCESS.value
                    },
                    "accessible_hubs": ["preparation_hub"]
                },
                UserRole.VIEWER.value: {
                    "description": "Read-only viewer",
                    "permissions": {
                        "pages": PermissionLevel.VIEW.value,
                        "databases": PermissionLevel.VIEW.value,
                        "settings": PermissionLevel.NO_ACCESS.value,
                        "users": PermissionLevel.NO_ACCESS.value
                    },
                    "accessible_hubs": ["family_hub"]
                }
            },
            "page_permissions": {
                # Specific page-level permissions
                "financial_accounts": [UserRole.ADMIN.value, UserRole.EXECUTOR.value],
                "legal_documents": [UserRole.ADMIN.value, UserRole.EXECUTOR.value, UserRole.ADVISOR.value],
                "family_contacts": [UserRole.ADMIN.value, UserRole.EXECUTOR.value, UserRole.FAMILY.value],
                "memorial_wishes": [UserRole.ADMIN.value, UserRole.FAMILY.value]
            },
            "database_permissions": {
                # Database-specific permissions
                "Assets": {
                    UserRole.ADMIN.value: PermissionLevel.FULL_ACCESS.value,
                    UserRole.EXECUTOR.value: PermissionLevel.EDIT.value,
                    UserRole.FAMILY.value: PermissionLevel.VIEW.value,
                    UserRole.ADVISOR.value: PermissionLevel.VIEW.value
                },
                "Contacts": {
                    UserRole.ADMIN.value: PermissionLevel.FULL_ACCESS.value,
                    UserRole.EXECUTOR.value: PermissionLevel.EDIT.value,
                    UserRole.FAMILY.value: PermissionLevel.EDIT.value,
                    UserRole.ADVISOR.value: PermissionLevel.VIEW.value
                },
                "Important Documents": {
                    UserRole.ADMIN.value: PermissionLevel.FULL_ACCESS.value,
                    UserRole.EXECUTOR.value: PermissionLevel.EDIT.value,
                    UserRole.FAMILY.value: PermissionLevel.VIEW.value,
                    UserRole.ADVISOR.value: PermissionLevel.COMMENT.value
                }
            }
        }
    
    def check_permission(self, user_role: str, resource_type: str, 
                        resource_name: str) -> PermissionLevel:
        """Check permission level for a user role on a resource.
        
        Args:
            user_role: User's role
            resource_type: Type of resource (page, database, etc.)
            resource_name: Name of the specific resource
            
        Returns:
            Permission level for the user
        """
        # Log permission check
        self._log_access_attempt(user_role, resource_type, resource_name)
        
        # Check specific resource permissions first
        if resource_type == "database" and resource_name in self.permissions["database_permissions"]:
            db_perms = self.permissions["database_permissions"][resource_name]
            if user_role in db_perms:
                return PermissionLevel(db_perms[user_role])
        
        if resource_type == "page" and resource_name in self.permissions["page_permissions"]:
            allowed_roles = self.permissions["page_permissions"][resource_name]
            if user_role in allowed_roles:
                # Get general permission level for pages
                role_perms = self.permissions["roles"][user_role]["permissions"]
                return PermissionLevel(role_perms.get("pages", PermissionLevel.NO_ACCESS.value))
        
        # Fall back to general role permissions
        if user_role in self.permissions["roles"]:
            role_perms = self.permissions["roles"][user_role]["permissions"]
            resource_key = f"{resource_type}s"  # pages, databases, etc.
            if resource_key in role_perms:
                return PermissionLevel(role_perms[resource_key])
        
        return PermissionLevel.NO_ACCESS
    
    def get_accessible_hubs(self, user_role: str) -> List[str]:
        """Get list of hubs accessible to a user role.
        
        Args:
            user_role: User's role
            
        Returns:
            List of accessible hub names
        """
        if user_role in self.permissions["roles"]:
            hubs = self.permissions["roles"][user_role].get("accessible_hubs", [])
            if "*" in hubs:
                return ["preparation_hub", "executor_hub", "family_hub"]
            return hubs
        return []
    
    def apply_permissions_to_notion(self, state: Dict[str, Any], 
                                   user_mappings: Dict[str, str]) -> Dict[str, Any]:
        """Apply permissions to Notion pages and databases.
        
        Args:
            state: Current deployment state
            user_mappings: Mapping of user emails to roles
            
        Returns:
            Updated state with permissions applied
        """
        results = {
            "updated_pages": 0,
            "updated_databases": 0,
            "errors": []
        }
        
        for user_email, user_role in user_mappings.items():
            try:
                # Apply page permissions
                pages_updated = self._apply_page_permissions(state, user_email, user_role)
                results["updated_pages"] += pages_updated
                
                # Apply database permissions
                dbs_updated = self._apply_database_permissions(state, user_email, user_role)
                results["updated_databases"] += dbs_updated
                
            except Exception as e:
                logger.error(f"Error applying permissions for {user_email}: {e}")
                results["errors"].append(str(e))
        
        # Store permission state
        state["permissions"] = {
            "applied_at": datetime.now().isoformat(),
            "user_mappings": user_mappings,
            "results": results
        }
        
        return results
    
    def _apply_page_permissions(self, state: Dict[str, Any], 
                               user_email: str, user_role: str) -> int:
        """Apply permissions to pages for a user.
        
        Args:
            state: Current deployment state
            user_email: User's email
            user_role: User's role
            
        Returns:
            Number of pages updated
        """
        pages_updated = 0
        accessible_hubs = self.get_accessible_hubs(user_role)
        
        # Store permission updates in state for later API calls
        if "permission_updates" not in state:
            state["permission_updates"] = []
        
        for page_id, page_info in state.get("pages", {}).items():
            page_hub = page_info.get("hub")
            page_name = page_info.get("name")
            
            # Check if user should have access to this page
            if page_hub in accessible_hubs or "*" in accessible_hubs:
                permission_level = self.check_permission(user_role, "page", page_name)
                
                state["permission_updates"].append({
                    "type": "page",
                    "id": page_id,
                    "user_email": user_email,
                    "permission": permission_level.value
                })
                pages_updated += 1
        
        return pages_updated
    
    def _apply_database_permissions(self, state: Dict[str, Any], 
                                   user_email: str, user_role: str) -> int:
        """Apply permissions to databases for a user.
        
        Args:
            state: Current deployment state
            user_email: User's email
            user_role: User's role
            
        Returns:
            Number of databases updated
        """
        databases_updated = 0
        
        if "permission_updates" not in state:
            state["permission_updates"] = []
        
        for db_id, db_info in state.get("databases", {}).items():
            db_name = db_info.get("name")
            permission_level = self.check_permission(user_role, "database", db_name)
            
            if permission_level != PermissionLevel.NO_ACCESS:
                state["permission_updates"].append({
                    "type": "database",
                    "id": db_id,
                    "user_email": user_email,
                    "permission": permission_level.value
                })
                databases_updated += 1
        
        return databases_updated
    
    def _log_access_attempt(self, user_role: str, resource_type: str, 
                           resource_name: str):
        """Log permission check for audit trail.
        
        Args:
            user_role: User's role
            resource_type: Type of resource
            resource_name: Name of resource
        """
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "role": user_role,
            "resource_type": resource_type,
            "resource_name": resource_name
        })
    
    def get_permission_matrix(self) -> Dict[str, Any]:
        """Generate a permission matrix for documentation.
        
        Returns:
            Permission matrix showing all role-resource combinations
        """
        matrix = {}
        
        for role in UserRole:
            matrix[role.value] = {
                "description": self.permissions["roles"].get(
                    role.value, {}
                ).get("description", ""),
                "accessible_hubs": self.get_accessible_hubs(role.value),
                "permissions": {}
            }
            
            # Add specific permissions
            for resource_type in ["page", "database"]:
                matrix[role.value]["permissions"][resource_type] = []
                
                # Check page permissions
                if resource_type == "page":
                    for page_name, allowed_roles in self.permissions["page_permissions"].items():
                        if role.value in allowed_roles:
                            matrix[role.value]["permissions"][resource_type].append(page_name)
                
                # Check database permissions
                elif resource_type == "database":
                    for db_name, db_perms in self.permissions["database_permissions"].items():
                        if role.value in db_perms:
                            matrix[role.value]["permissions"][resource_type].append({
                                "name": db_name,
                                "level": db_perms[role.value]
                            })
        
        return matrix
    
    def export_audit_log(self, filepath: str):
        """Export audit log to file.
        
        Args:
            filepath: Path to export audit log
        """
        with open(filepath, 'w') as f:
            json.dump(self.audit_log, f, indent=2)
        logger.info(f"Audit log exported to {filepath}")


def setup_role_permissions(state: Dict[str, Any], 
                          user_mappings: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Main entry point for setting up role-based permissions.
    
    Args:
        state: Current deployment state
        user_mappings: Optional mapping of user emails to roles
        
    Returns:
        Permission application results
    """
    manager = RolePermissionManager()
    
    # Use provided mappings or load from environment
    if not user_mappings:
        user_mappings = {
            os.getenv("ADMIN_EMAIL", ""): UserRole.ADMIN.value,
            os.getenv("EXECUTOR_EMAIL", ""): UserRole.EXECUTOR.value,
        }
        # Remove empty entries
        user_mappings = {k: v for k, v in user_mappings.items() if k}
    
    if not user_mappings:
        logger.warning("No user mappings provided, skipping permission setup")
        return {"status": "skipped", "reason": "no_user_mappings"}
    
    logger.info(f"Setting up permissions for {len(user_mappings)} users")
    results = manager.apply_permissions_to_notion(state, user_mappings)
    
    # Export permission matrix for documentation
    matrix = manager.get_permission_matrix()
    state["permission_matrix"] = matrix
    
    # Export audit log
    if os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true":
        manager.export_audit_log("artifacts/permission_audit.json")
    
    return results