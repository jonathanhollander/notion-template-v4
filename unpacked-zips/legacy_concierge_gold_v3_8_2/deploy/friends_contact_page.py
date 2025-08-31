"""Friends to Contact Page for Notion Deployment.

Implements a specialized Friends to Contact page within Notion with:
- Contact notification system
- Friend categorization and tagging
- Notification preferences
- Communication tracking
- Automated reminder setup
- Contact history timeline
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

from constants import *

logger = logging.getLogger(__name__)


class ContactCategory(Enum):
    """Categories of friends to contact."""
    IMMEDIATE_FAMILY = "immediate_family"
    EXTENDED_FAMILY = "extended_family"
    CLOSE_FRIENDS = "close_friends"
    PROFESSIONAL = "professional"
    ADVISORS = "advisors"
    NEIGHBORS = "neighbors"
    COMMUNITY = "community"


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    URGENT = "urgent"          # Contact immediately
    HIGH = "high"              # Within 24 hours
    MEDIUM = "medium"          # Within 1 week
    LOW = "low"                # When convenient
    MEMORIAL = "memorial"      # For memorial service


class FriendsContactManager:
    """Manages Friends to Contact page and functionality."""
    
    def __init__(self):
        """Initialize friends contact manager."""
        self.contact_lists = {}
        self.notification_templates = {}
        self.communication_log = []
        self.reminder_rules = []
    
    def create_friends_contact_page(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create the main Friends to Contact page.
        
        Args:
            state: Current deployment state
            
        Returns:
            Page creation result
        """
        parent_page_id = state.get('pages', {}).get('Family Hub')
        
        # Create page structure
        page_config = {
            'parent_id': parent_page_id,
            'title': 'Friends to Contact',
            'icon': '📞',
            'cover': None,
            'properties': {
                'Type': 'Contact Management',
                'Created': datetime.now().isoformat(),
                'Visibility': 'Family & Executor'
            }
        }
        
        # Generate page blocks
        blocks = self._create_page_blocks(state)
        page_config['blocks'] = blocks
        
        # Create the page (mock for now)
        page_id = f"friends_contact_{datetime.now().timestamp()}"
        
        # Store in state
        if 'friends_contact_page' not in state:
            state['friends_contact_page'] = {}
        
        state['friends_contact_page']['id'] = page_id
        state['friends_contact_page']['config'] = page_config
        state['friends_contact_page']['created_at'] = datetime.now().isoformat()
        
        logger.info(f"Created Friends to Contact page: {page_id}")
        
        return {
            'page_id': page_id,
            'blocks_created': len(blocks)
        }
    
    def _create_page_blocks(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create blocks for Friends to Contact page.
        
        Args:
            state: Current deployment state
            
        Returns:
            List of Notion blocks
        """
        blocks = []
        
        # Header section
        blocks.extend([
            {
                'type': 'heading_1',
                'heading_1': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': 'Friends & Family to Contact'}
                    }]
                }
            },
            {
                'type': 'callout',
                'callout': {
                    'icon': {'emoji': '📋'},
                    'rich_text': [{
                        'type': 'text',
                        'text': {
                            'content': 'This page helps coordinate notifications to friends and family. '
                                     'Use this to track who needs to be contacted and when.'
                        }
                    }]
                }
            },
            {'type': 'divider', 'divider': {}}
        ])
        
        # Priority contact lists
        blocks.extend(self._create_priority_sections())
        
        # Contact categories
        blocks.extend(self._create_category_sections())
        
        # Communication templates
        blocks.extend(self._create_template_section())
        
        # Contact tracking database view
        blocks.extend(self._create_tracking_section(state))
        
        # Instructions section
        blocks.extend(self._create_instructions_section())
        
        return blocks
    
    def _create_priority_sections(self) -> List[Dict[str, Any]]:
        """Create priority-based contact sections.
        
        Returns:
            List of Notion blocks
        """
        blocks = [
            {
                'type': 'heading_2',
                'heading_2': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': '🚨 Priority Contacts'}
                    }]
                }
            }
        ]
        
        priorities = [
            {
                'level': NotificationPriority.URGENT,
                'emoji': '🔴',
                'title': 'Immediate Contact Required',
                'description': 'Contact these individuals immediately'
            },
            {
                'level': NotificationPriority.HIGH,
                'emoji': '🟠',
                'title': 'Contact Within 24 Hours',
                'description': 'High priority contacts'
            },
            {
                'level': NotificationPriority.MEDIUM,
                'emoji': '🟡',
                'title': 'Contact Within One Week',
                'description': 'Standard priority contacts'
            }
        ]
        
        for priority in priorities:
            blocks.append({
                'type': 'toggle',
                'toggle': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {
                            'content': f"{priority['emoji']} {priority['title']}"
                        }
                    }],
                    'children': [
                        {
                            'type': 'paragraph',
                            'paragraph': {
                                'rich_text': [{
                                    'type': 'text',
                                    'text': {'content': priority['description']}
                                }]
                            }
                        },
                        {
                            'type': 'to_do',
                            'to_do': {
                                'rich_text': [{
                                    'type': 'text',
                                    'text': {'content': 'Contact list will be populated here'}
                                }],
                                'checked': False
                            }
                        }
                    ]
                }
            })
        
        return blocks
    
    def _create_category_sections(self) -> List[Dict[str, Any]]:
        """Create contact category sections.
        
        Returns:
            List of Notion blocks
        """
        blocks = [
            {'type': 'divider', 'divider': {}},
            {
                'type': 'heading_2',
                'heading_2': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': '👥 Contact Categories'}
                    }]
                }
            }
        ]
        
        categories = [
            ('👨‍👩‍👧‍👦', 'Immediate Family', ContactCategory.IMMEDIATE_FAMILY),
            ('👫', 'Extended Family', ContactCategory.EXTENDED_FAMILY),
            ('🤝', 'Close Friends', ContactCategory.CLOSE_FRIENDS),
            ('💼', 'Professional Contacts', ContactCategory.PROFESSIONAL),
            ('📚', 'Advisors & Consultants', ContactCategory.ADVISORS),
            ('🏘️', 'Neighbors & Community', ContactCategory.NEIGHBORS)
        ]
        
        for emoji, title, category in categories:
            blocks.append({
                'type': 'toggle',
                'toggle': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': f"{emoji} {title}"}
                    }],
                    'children': [
                        {
                            'type': 'numbered_list_item',
                            'numbered_list_item': {
                                'rich_text': [{
                                    'type': 'text',
                                    'text': {'content': f'Contacts in {title} category'}
                                }]
                            }
                        }
                    ]
                }
            })
        
        return blocks
    
    def _create_template_section(self) -> List[Dict[str, Any]]:
        """Create communication template section.
        
        Returns:
            List of Notion blocks
        """
        blocks = [
            {'type': 'divider', 'divider': {}},
            {
                'type': 'heading_2',
                'heading_2': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': '📝 Communication Templates'}
                    }]
                }
            }
        ]
        
        templates = [
            {
                'name': 'Initial Notification',
                'content': 'Dear [Name], I wanted to inform you that [Estate Owner] has passed away...'
            },
            {
                'name': 'Memorial Service Invitation',
                'content': 'You are invited to attend the memorial service for [Estate Owner]...'
            },
            {
                'name': 'Estate Update',
                'content': 'This is an update regarding the estate of [Estate Owner]...'
            }
        ]
        
        for template in templates:
            blocks.append({
                'type': 'toggle',
                'toggle': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': template['name']}
                    }],
                    'children': [
                        {
                            'type': 'quote',
                            'quote': {
                                'rich_text': [{
                                    'type': 'text',
                                    'text': {'content': template['content']}
                                }]
                            }
                        }
                    ]
                }
            })
        
        return blocks
    
    def _create_tracking_section(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create contact tracking section.
        
        Args:
            state: Current deployment state
            
        Returns:
            List of Notion blocks
        """
        blocks = [
            {'type': 'divider', 'divider': {}},
            {
                'type': 'heading_2',
                'heading_2': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': '📊 Contact Tracking'}
                    }]
                }
            },
            {
                'type': 'callout',
                'callout': {
                    'icon': {'emoji': '📈'},
                    'rich_text': [{
                        'type': 'text',
                        'text': {
                            'content': 'Track communication status with each contact'
                        }
                    }]
                }
            }
        ]
        
        # Add database view for contact tracking
        if 'databases' in state and 'Contacts' in state['databases']:
            blocks.append({
                'type': 'child_database',
                'child_database': {
                    'title': 'Contact Communication Log'
                }
            })
        
        return blocks
    
    def _create_instructions_section(self) -> List[Dict[str, Any]]:
        """Create instructions section.
        
        Returns:
            List of Notion blocks
        """
        return [
            {'type': 'divider', 'divider': {}},
            {
                'type': 'heading_2',
                'heading_2': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': '📖 Instructions'}
                    }]
                }
            },
            {
                'type': 'numbered_list_item',
                'numbered_list_item': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': 'Review and update contact priorities regularly'}
                    }]
                }
            },
            {
                'type': 'numbered_list_item',
                'numbered_list_item': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': 'Use templates for consistent communication'}
                    }]
                }
            },
            {
                'type': 'numbered_list_item',
                'numbered_list_item': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': 'Track all communications in the log'}
                    }]
                }
            },
            {
                'type': 'numbered_list_item',
                'numbered_list_item': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': 'Set reminders for follow-up communications'}
                    }]
                }
            }
        ]
    
    def create_contact_list(self, category: ContactCategory, 
                           contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a categorized contact list.
        
        Args:
            category: Contact category
            contacts: List of contacts
            
        Returns:
            Contact list creation result
        """
        list_id = f"{category.value}_list"
        
        self.contact_lists[list_id] = {
            'category': category.value,
            'contacts': contacts,
            'created_at': datetime.now().isoformat(),
            'last_updated': None
        }
        
        return {
            'list_id': list_id,
            'contacts_added': len(contacts)
        }
    
    def add_notification_template(self, template_id: str, 
                                 template: Dict[str, Any]) -> Dict[str, Any]:
        """Add a notification template.
        
        Args:
            template_id: Template identifier
            template: Template configuration
            
        Returns:
            Template addition result
        """
        self.notification_templates[template_id] = {
            **template,
            'created_at': datetime.now().isoformat(),
            'usage_count': 0
        }
        
        return {
            'template_id': template_id,
            'created': True
        }
    
    def log_communication(self, contact_id: str, 
                         communication: Dict[str, Any]) -> Dict[str, Any]:
        """Log a communication with a contact.
        
        Args:
            contact_id: Contact identifier
            communication: Communication details
            
        Returns:
            Logging result
        """
        log_entry = {
            'id': f"comm_{datetime.now().timestamp()}",
            'contact_id': contact_id,
            'timestamp': datetime.now().isoformat(),
            **communication
        }
        
        self.communication_log.append(log_entry)
        
        return {
            'logged': True,
            'entry_id': log_entry['id']
        }
    
    def setup_reminder(self, contact_id: str, 
                      reminder_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup a reminder for contacting someone.
        
        Args:
            contact_id: Contact identifier
            reminder_config: Reminder configuration
            
        Returns:
            Reminder setup result
        """
        reminder = {
            'id': f"reminder_{datetime.now().timestamp()}",
            'contact_id': contact_id,
            'due_date': reminder_config.get('due_date'),
            'priority': reminder_config.get('priority', NotificationPriority.MEDIUM.value),
            'message': reminder_config.get('message'),
            'created_at': datetime.now().isoformat(),
            'completed': False
        }
        
        self.reminder_rules.append(reminder)
        
        return {
            'reminder_id': reminder['id'],
            'scheduled': True
        }
    
    def get_contact_report(self) -> Dict[str, Any]:
        """Get contact management report.
        
        Returns:
            Contact report
        """
        total_contacts = sum(
            len(cl['contacts']) for cl in self.contact_lists.values()
        )
        
        communications_by_priority = {}
        for entry in self.communication_log:
            priority = entry.get('priority', 'medium')
            communications_by_priority[priority] = \
                communications_by_priority.get(priority, 0) + 1
        
        return {
            'total_contact_lists': len(self.contact_lists),
            'total_contacts': total_contacts,
            'total_communications': len(self.communication_log),
            'communications_by_priority': communications_by_priority,
            'pending_reminders': sum(
                1 for r in self.reminder_rules if not r['completed']
            ),
            'templates_available': len(self.notification_templates)
        }


def setup_friends_contact_page(state: Dict[str, Any]) -> Dict[str, Any]:
    """Setup Friends to Contact page for Estate Planning system.
    
    Args:
        state: Current deployment state
        
    Returns:
        Setup results
    """
    manager = FriendsContactManager()
    
    # Create the main Friends to Contact page
    page_result = manager.create_friends_contact_page(state)
    
    # Set up default notification templates
    templates = [
        {
            'id': 'initial_notification',
            'name': 'Initial Notification',
            'subject': 'Important Information',
            'body': 'Template for initial contact notification'
        },
        {
            'id': 'memorial_invitation',
            'name': 'Memorial Service Invitation',
            'subject': 'Memorial Service Information',
            'body': 'Template for memorial service details'
        },
        {
            'id': 'estate_update',
            'name': 'Estate Update',
            'subject': 'Estate Administration Update',
            'body': 'Template for estate progress updates'
        }
    ]
    
    for template in templates:
        manager.add_notification_template(template['id'], template)
    
    # Create sample contact lists
    sample_contacts = {
        ContactCategory.IMMEDIATE_FAMILY: [
            {'name': 'Spouse', 'priority': NotificationPriority.URGENT.value},
            {'name': 'Children', 'priority': NotificationPriority.URGENT.value}
        ],
        ContactCategory.CLOSE_FRIENDS: [
            {'name': 'Best Friend', 'priority': NotificationPriority.HIGH.value}
        ],
        ContactCategory.PROFESSIONAL: [
            {'name': 'Attorney', 'priority': NotificationPriority.HIGH.value},
            {'name': 'Accountant', 'priority': NotificationPriority.MEDIUM.value}
        ]
    }
    
    for category, contacts in sample_contacts.items():
        manager.create_contact_list(category, contacts)
    
    # Store manager in state
    state['friends_contact_manager'] = manager
    
    # Get report
    report = manager.get_contact_report()
    
    return {
        'page_created': page_result['page_id'] is not None,
        'blocks_created': page_result['blocks_created'],
        'contact_lists': report['total_contact_lists'],
        'templates_created': report['templates_available'],
        'total_contacts': report['total_contacts']
    }