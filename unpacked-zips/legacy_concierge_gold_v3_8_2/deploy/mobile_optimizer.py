"""Mobile Optimization Module for Notion Deployment.

Enhances Notion pages for mobile viewing with:
- Responsive layouts
- Touch-friendly navigation
- Optimized content stacking
- Mobile-specific UI elements
- Performance optimizations
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from enum import Enum

from constants import *

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class ViewportSize(Enum):
    """Common mobile viewport sizes."""
    MOBILE_SMALL = (320, 568)    # iPhone SE
    MOBILE_MEDIUM = (375, 667)   # iPhone 8
    MOBILE_LARGE = (414, 896)    # iPhone 11 Pro Max
    TABLET = (768, 1024)         # iPad
    DESKTOP = (1920, 1080)       # Standard desktop


class MobileOptimizer:
    """Optimizes Notion content for mobile viewing."""
    
    def __init__(self):
        """Initialize mobile optimizer."""
        self.mobile_tips = {
            "navigation": "📱 On mobile: Use ••• menu to jump between sections",
            "scrolling": "👆 Swipe up/down to navigate. Tap tiles to expand",
            "offline": "💾 Save pages offline: Tap ⋯ → Make Available Offline",
            "search": "🔍 Pull down to search within the page",
            "sharing": "📤 Share: Tap ⋯ → Share → Copy Link"
        }
        
        self.optimization_stats = {
            "pages_optimized": 0,
            "mobile_blocks_added": 0,
            "layouts_adjusted": 0
        }
    
    def optimize_hub_for_mobile(self, state: Dict[str, Any], hub_name: str, 
                               hub_id: str) -> Dict[str, Any]:
        """Optimize a hub page for mobile viewing.
        
        Args:
            state: Current deployment state
            hub_name: Name of the hub
            hub_id: Notion page ID of the hub
            
        Returns:
            Optimization results
        """
        logger.info(f"Optimizing {hub_name} for mobile...")
        
        mobile_blocks = []
        
        # Add mobile navigation helper
        mobile_blocks.append(self._create_mobile_nav_block(hub_name))
        
        # Add collapsible sections for better mobile organization
        mobile_blocks.extend(self._create_mobile_sections(hub_name))
        
        # Add quick action buttons
        mobile_blocks.append(self._create_quick_actions_block(hub_name))
        
        # Add mobile-specific tips
        mobile_blocks.append(self._create_mobile_tips_block())
        
        # Store blocks for later API calls
        if "mobile_optimizations" not in state:
            state["mobile_optimizations"] = {}
        
        state["mobile_optimizations"][hub_id] = {
            "hub_name": hub_name,
            "mobile_blocks": mobile_blocks,
            "timestamp": None  # Will be set when applied
        }
        
        self.optimization_stats["pages_optimized"] += 1
        self.optimization_stats["mobile_blocks_added"] += len(mobile_blocks)
        
        return {
            "hub_name": hub_name,
            "blocks_added": len(mobile_blocks),
            "status": "optimized"
        }
    
    def _create_mobile_nav_block(self, hub_name: str) -> Dict[str, Any]:
        """Create mobile navigation helper block.
        
        Args:
            hub_name: Name of the hub
            
        Returns:
            Notion block object
        """
        nav_content = self._get_hub_navigation(hub_name)
        
        return {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "📱 Quick Navigation"},
                        "annotations": {"bold": True}
                    }
                ],
                "children": nav_content
            }
        }
    
    def _get_hub_navigation(self, hub_name: str) -> List[Dict[str, Any]]:
        """Get navigation items for a hub.
        
        Args:
            hub_name: Name of the hub
            
        Returns:
            List of navigation blocks
        """
        nav_items = {
            "Preparation Hub": [
                "📝 Getting Started",
                "👤 Personal Information",
                "💰 Financial Overview",
                "📄 Legal Documents",
                "🏥 Medical Information"
            ],
            "Executor Hub": [
                "✅ Immediate Actions",
                "📊 Estate Overview",
                "🏦 Financial Accounts",
                "🏠 Property & Assets",
                "📋 Task Tracker"
            ],
            "Family Hub": [
                "👨‍👩‍👧‍👦 Family Contacts",
                "💭 Memorial Wishes",
                "📸 Photo Gallery",
                "💌 Letters to Loved Ones",
                "🎯 Legacy Goals"
            ]
        }
        
        items = nav_items.get(hub_name, ["📌 Section 1", "📌 Section 2", "📌 Section 3"])
        
        return [
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": item}}]
                }
            }
            for item in items
        ]
    
    def _create_mobile_sections(self, hub_name: str) -> List[Dict[str, Any]]:
        """Create collapsible sections for mobile.
        
        Args:
            hub_name: Name of the hub
            
        Returns:
            List of section blocks
        """
        sections = []
        
        # Create collapsible sections based on hub type
        if "Preparation" in hub_name:
            sections.append(self._create_section_block(
                "Essential Information",
                "Store critical details that your executor will need immediately",
                "🔑"
            ))
            sections.append(self._create_section_block(
                "Financial Planning",
                "Organize accounts, assets, and financial documents",
                "💰"
            ))
        elif "Executor" in hub_name:
            sections.append(self._create_section_block(
                "First 48 Hours",
                "Immediate actions and notifications required",
                "⏰"
            ))
            sections.append(self._create_section_block(
                "Estate Administration",
                "Legal and financial tasks for estate settlement",
                "⚖️"
            ))
        elif "Family" in hub_name:
            sections.append(self._create_section_block(
                "Family Information",
                "Contact details and important family data",
                "👨‍👩‍👧‍👦"
            ))
            sections.append(self._create_section_block(
                "Legacy & Memories",
                "Personal messages and memorial preferences",
                "💝"
            ))
        
        return sections
    
    def _create_section_block(self, title: str, description: str, 
                             emoji: str) -> Dict[str, Any]:
        """Create a collapsible section block.
        
        Args:
            title: Section title
            description: Section description
            emoji: Section emoji icon
            
        Returns:
            Notion block object
        """
        return {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"{emoji} {title}"},
                        "annotations": {"bold": True}
                    }
                ],
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": description},
                                    "annotations": {"italic": True, "color": "gray"}
                                }
                            ]
                        }
                    }
                ]
            }
        }
    
    def _create_quick_actions_block(self, hub_name: str) -> Dict[str, Any]:
        """Create quick action buttons for mobile.
        
        Args:
            hub_name: Name of the hub
            
        Returns:
            Notion block object
        """
        actions = {
            "Preparation Hub": [
                "➕ Add Contact",
                "📄 Upload Document",
                "💰 Add Account"
            ],
            "Executor Hub": [
                "✅ Mark Complete",
                "📞 Contact Professional",
                "📊 View Report"
            ],
            "Family Hub": [
                "👤 Update Contact",
                "💌 Write Letter",
                "📸 Add Photo"
            ]
        }
        
        hub_actions = actions.get(hub_name, ["➕ Add", "✏️ Edit", "👁 View"])
        
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "icon": {"type": "emoji", "emoji": "⚡"},
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Quick Actions: "},
                        "annotations": {"bold": True}
                    },
                    {
                        "type": "text",
                        "text": {"content": " • ".join(hub_actions)}
                    }
                ],
                "color": "blue_background"
            }
        }
    
    def _create_mobile_tips_block(self) -> Dict[str, Any]:
        """Create mobile tips callout block.
        
        Returns:
            Notion block object
        """
        tips_text = " | ".join([
            self.mobile_tips["navigation"],
            self.mobile_tips["scrolling"]
        ])
        
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "icon": {"type": "emoji", "emoji": "💡"},
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Mobile Tips: "},
                        "annotations": {"bold": True}
                    },
                    {
                        "type": "text",
                        "text": {"content": tips_text},
                        "annotations": {"italic": True, "color": "gray"}
                    }
                ],
                "color": "gray_background"
            }
        }
    
    def create_mobile_dashboard(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create a mobile-optimized dashboard view.
        
        Args:
            state: Current deployment state
            
        Returns:
            Dashboard configuration
        """
        dashboard = {
            "title": "Mobile Dashboard",
            "icon": "📱",
            "blocks": [
                self._create_dashboard_header(),
                self._create_status_cards(),
                self._create_recent_activity(),
                self._create_quick_links()
            ]
        }
        
        # Store dashboard in state
        if "mobile_dashboard" not in state:
            state["mobile_dashboard"] = dashboard
        
        self.optimization_stats["layouts_adjusted"] += 1
        
        return dashboard
    
    def _create_dashboard_header(self) -> Dict[str, Any]:
        """Create dashboard header block."""
        return {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "📱 Estate Planning Dashboard"}
                    }
                ]
            }
        }
    
    def _create_status_cards(self) -> Dict[str, Any]:
        """Create status cards for mobile dashboard."""
        return {
            "object": "block",
            "type": "column_list",
            "column_list": {
                "children": [
                    self._create_status_card("Documents", "12/15", "📄", "green"),
                    self._create_status_card("Contacts", "24", "👥", "blue"),
                    self._create_status_card("Tasks", "8/10", "✅", "yellow")
                ]
            }
        }
    
    def _create_status_card(self, title: str, value: str, emoji: str, 
                           color: str) -> Dict[str, Any]:
        """Create a single status card."""
        return {
            "object": "block",
            "type": "column",
            "column": {
                "children": [
                    {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "icon": {"type": "emoji", "emoji": emoji},
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": f"{title}\n"},
                                    "annotations": {"bold": True}
                                },
                                {
                                    "type": "text",
                                    "text": {"content": value},
                                    "annotations": {"code": True}
                                }
                            ],
                            "color": f"{color}_background"
                        }
                    }
                ]
            }
        }
    
    def _create_recent_activity(self) -> Dict[str, Any]:
        """Create recent activity section."""
        return {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "📊 Recent Activity"},
                        "annotations": {"bold": True}
                    }
                ],
                "children": [
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "Document uploaded: Will & Testament"}}
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "Contact added: Estate Attorney"}}
                            ]
                        }
                    }
                ]
            }
        }
    
    def _create_quick_links(self) -> Dict[str, Any]:
        """Create quick links section."""
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "icon": {"type": "emoji", "emoji": "🔗"},
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Quick Links: "},
                        "annotations": {"bold": True}
                    },
                    {
                        "type": "text",
                        "text": {"content": "Preparation Hub | Executor Hub | Family Hub"},
                        "annotations": {"color": "blue"}
                    }
                ],
                "color": "gray_background"
            }
        }
    
    def get_optimization_stats(self) -> Dict[str, int]:
        """Get mobile optimization statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.optimization_stats


def optimize_for_mobile(state: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for mobile optimization.
    
    Args:
        state: Current deployment state
        
    Returns:
        Optimization results
    """
    optimizer = MobileOptimizer()
    results = {
        "optimized_hubs": [],
        "dashboard_created": False,
        "stats": {}
    }
    
    # Optimize each hub
    hub_names = ["Preparation Hub", "Executor Hub", "Family Hub"]
    for hub_name in hub_names:
        hub_id = state.get("pages", {}).get(hub_name)
        if hub_id:
            result = optimizer.optimize_hub_for_mobile(state, hub_name, hub_id)
            results["optimized_hubs"].append(result)
            logger.info(f"Optimized {hub_name} with {result['blocks_added']} mobile blocks")
    
    # Create mobile dashboard
    if os.getenv("CREATE_MOBILE_DASHBOARD", "true").lower() == "true":
        dashboard = optimizer.create_mobile_dashboard(state)
        results["dashboard_created"] = True
        logger.info("Created mobile dashboard")
    
    # Get final statistics
    results["stats"] = optimizer.get_optimization_stats()
    
    return results