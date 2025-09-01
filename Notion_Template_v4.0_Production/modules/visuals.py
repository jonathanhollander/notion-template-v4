"""
Premium Visual Components for Estate Planning Concierge v4.0
Tasteful, professional visual elements appropriate for estate planning
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path
from .config import load_config

logger = logging.getLogger(__name__)

# Load estate-appropriate emoji from config
config = load_config(Path("config.yaml"))
ESTATE_EMOJI = config.get('visual_config', {}).get('estate_emoji', {})
THEMES = config.get('visual_config', {}).get('themes', {})


def get_estate_emoji(category: str, default: str = "•") -> str:
    """Get tasteful emoji appropriate for estate planning context"""
    return ESTATE_EMOJI.get(category, default)


def create_professional_header(title: str, subtitle: str = "", theme: str = "executive_blue") -> List[Dict]:
    """Create dignified header for estate planning pages"""
    theme_colors = THEMES.get(theme, THEMES["executive_blue"])
    
    return [
        {
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": title},
                    "annotations": {"color": "default"}  # Professional, no bright colors
                }]
            }
        },
        {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": subtitle},
                    "annotations": {"italic": True, "color": "gray"}
                }] if subtitle else []
            }
        },
        create_professional_divider()
    ]


def create_professional_divider(style: str = "simple") -> Dict:
    """Create tasteful divider for estate documents"""
    dividers = {
        "simple": "―――――――――――――――――――――",
        "section": "━━━━━━━━━━━━━━━━━━━━",
        "subtle": "· · · · · · · · · · ·",
        "formal": "══════════════════════"
    }
    
    return {
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "text": {"content": dividers.get(style, dividers["simple"])},
                "annotations": {"color": "gray"}
            }]
        }
    }


def create_estate_status_indicator(status: str) -> str:
    """Create professional status indicators for estate planning tasks"""
    status_map = {
        "complete": f"{get_estate_emoji('complete')} Complete",
        "in_progress": f"{get_estate_emoji('in_progress')} In Progress",
        "pending": f"{get_estate_emoji('pending')} Pending",
        "review": f"{get_estate_emoji('attention')} Requires Review",
        "verified": f"{get_estate_emoji('verified')} Verified",
        "confidential": f"{get_estate_emoji('confidential')} Confidential"
    }
    return status_map.get(status, status)


def create_document_callout(content: str, doc_type: str = "legal") -> Dict:
    """Create professional callout for estate documents"""
    icon_map = {
        "legal": get_estate_emoji("legal"),
        "financial": get_estate_emoji("assets"),
        "family": get_estate_emoji("family"),
        "property": get_estate_emoji("property"),
        "important": get_estate_emoji("important")
    }
    
    return {
        "type": "callout",
        "callout": {
            "rich_text": [{
                "type": "text",
                "text": {"content": content}
            }],
            "icon": {"emoji": icon_map.get(doc_type, get_estate_emoji("document"))},
            "color": "gray_background"  # Subtle, professional
        }
    }


def create_estate_progress_indicator(percentage: int, label: str) -> Dict:
    """Create dignified progress indicator for estate planning tasks"""
    # Use simple, professional progress representation
    completed = "█" * (percentage // 10)
    remaining = "░" * (10 - (percentage // 10))
    
    return {
        "type": "callout",
        "callout": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": f"{label}\n"},
                    "annotations": {"bold": True}
                },
                {
                    "type": "text",
                    "text": {"content": f"{completed}{remaining} {percentage}%"},
                    "annotations": {"color": "default"}
                }
            ],
            "icon": {"emoji": get_estate_emoji("in_progress")},
            "color": "gray_background"
        }
    }


def create_beneficiary_list(beneficiaries: List[Dict]) -> List[Dict]:
    """Create professional beneficiary listing"""
    blocks = [
        {
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"{get_estate_emoji('generations')} Beneficiary Designations"}
                }]
            }
        }
    ]
    
    for beneficiary in beneficiaries:
        blocks.append({
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"{get_estate_emoji('subsection')} {beneficiary['name']} - {beneficiary['relationship']} ({beneficiary['percentage']}%)"}
                }]
            }
        })
    
    return blocks


def create_estate_checklist(title: str, items: List[Dict]) -> List[Dict]:
    """Create professional checklist for estate planning tasks"""
    blocks = [
        {
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"{get_estate_emoji('document')} {title}"}
                }]
            }
        }
    ]
    
    for item in items:
        status_emoji = get_estate_emoji("complete") if item.get("completed") else get_estate_emoji("pending")
        blocks.append({
            "type": "to_do",
            "to_do": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"{status_emoji} {item['task']}"}
                }],
                "checked": item.get("completed", False)
            }
        })
    
    return blocks


def create_asset_summary_card(asset_type: str, value: str, details: str = "") -> Dict:
    """Create professional asset summary card"""
    icon_map = {
        "real_estate": get_estate_emoji("property"),
        "financial": get_estate_emoji("assets"),
        "investment": get_estate_emoji("investment"),
        "personal": get_estate_emoji("secure")
    }
    
    return {
        "type": "callout",
        "callout": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": f"{asset_type}\n"},
                    "annotations": {"bold": True}
                },
                {
                    "type": "text",
                    "text": {"content": f"{value}"},
                    "annotations": {"bold": True, "color": "default"}
                },
                {
                    "type": "text",
                    "text": {"content": f"\n{details}"},
                    "annotations": {"italic": True, "color": "gray"}
                } if details else {"type": "text", "text": {"content": ""}}
            ],
            "icon": {"emoji": icon_map.get(asset_type.lower().replace(" ", "_"), get_estate_emoji("assets"))},
            "color": "gray_background"
        }
    }


def create_professional_timeline(milestones: List[Dict]) -> List[Dict]:
    """Create dignified timeline for estate planning milestones"""
    blocks = [
        {
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"{get_estate_emoji('heritage')} Estate Planning Timeline"}
                }]
            }
        }
    ]
    
    for i, milestone in enumerate(milestones):
        # Milestone block
        status_emoji = get_estate_emoji("complete") if milestone.get("completed") else get_estate_emoji("pending")
        blocks.append({
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"{status_emoji} {milestone['title']}\n"},
                        "annotations": {"bold": True}
                    },
                    {
                        "type": "text",
                        "text": {"content": milestone.get("date", "")},
                        "annotations": {"italic": True, "color": "gray"}
                    }
                ],
                "icon": {"emoji": get_estate_emoji("heritage")},
                "color": "gray_background"
            }
        })
        
        # Connection line (except for last item)
        if i < len(milestones) - 1:
            blocks.append({
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "text": {"content": "     │"},
                        "annotations": {"color": "gray"}
                    }]
                }
            })
    
    return blocks


def create_legal_document_section(doc_title: str, doc_status: str, last_updated: str) -> Dict:
    """Create professional legal document status section"""
    status_indicator = create_estate_status_indicator(doc_status)
    
    return {
        "type": "callout",
        "callout": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": f"{get_estate_emoji('legal')} {doc_title}\n"},
                    "annotations": {"bold": True}
                },
                {
                    "type": "text",
                    "text": {"content": f"Status: {status_indicator}\n"},
                    "annotations": {"color": "default"}
                },
                {
                    "type": "text",
                    "text": {"content": f"Last Updated: {last_updated}"},
                    "annotations": {"italic": True, "color": "gray"}
                }
            ],
            "icon": {"emoji": get_estate_emoji("sealed")},
            "color": "gray_background"
        }
    }


def create_confidential_notice() -> Dict:
    """Create professional confidentiality notice for estate documents"""
    return {
        "type": "callout",
        "callout": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "CONFIDENTIAL: This document contains sensitive estate planning information. Access is restricted to authorized individuals only."},
                "annotations": {"bold": True, "color": "default"}
            }],
            "icon": {"emoji": get_estate_emoji("confidential")},
            "color": "gray_background"
        }
    }


def create_professional_footer(page_type: str = "document") -> List[Dict]:
    """Create professional footer for estate planning pages"""
    return [
        create_professional_divider("simple"),
        {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"{get_estate_emoji('archived')} Document archived in Estate Planning System"},
                    "annotations": {"italic": True, "color": "gray", "font_size": "small"}
                }]
            }
        }
    ]