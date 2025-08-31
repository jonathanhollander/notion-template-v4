"""Progress Tracking Dashboard for Notion Deployment.

Implements progress tracking dashboard within Notion with:
- Visual progress indicators using Notion blocks
- Database view configurations for tracking
- Automated status rollups
- Milestone tracking
- Progress charts using callout blocks
- Activity timeline views
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

from constants import *

logger = logging.getLogger(__name__)


class DashboardWidgetType(Enum):
    """Types of dashboard widgets."""
    PROGRESS_BAR = "progress_bar"
    MILESTONE_TRACKER = "milestone_tracker"
    ACTIVITY_TIMELINE = "activity_timeline"
    STATUS_SUMMARY = "status_summary"
    METRIC_CARD = "metric_card"
    CHART_VIEW = "chart_view"


class ProgressDashboardManager:
    """Manages progress tracking dashboard in Notion."""
    
    def __init__(self):
        """Initialize dashboard manager."""
        self.dashboards = {}
        self.widgets = []
        self.metrics = {}
        self.milestones = []
    
    def create_dashboard(self, dashboard_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a progress tracking dashboard.
        
        Args:
            dashboard_id: Unique dashboard identifier
            config: Dashboard configuration including:
                - title: Dashboard title
                - parent_page_id: Parent page ID
                - widgets: List of widget configurations
                - refresh_interval: Auto-refresh interval
                - permissions: View permissions
                
        Returns:
            Dashboard creation result
        """
        self.dashboards[dashboard_id] = {
            **config,
            'created_at': datetime.now().isoformat(),
            'last_updated': None,
            'view_count': 0,
            'widgets': []
        }
        
        # Create dashboard widgets
        for widget_config in config.get('widgets', []):
            widget = self._create_widget(widget_config)
            self.dashboards[dashboard_id]['widgets'].append(widget['id'])
            self.widgets.append(widget)
        
        logger.info(f"Created dashboard: {dashboard_id}")
        
        return {
            'dashboard_id': dashboard_id,
            'widgets_created': len(self.dashboards[dashboard_id]['widgets'])
        }
    
    def _create_widget(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a dashboard widget.
        
        Args:
            config: Widget configuration
            
        Returns:
            Created widget
        """
        widget_type = DashboardWidgetType(config['type'])
        widget_id = f"widget_{datetime.now().timestamp()}"
        
        widget = {
            'id': widget_id,
            'type': widget_type.value,
            'config': config,
            'created_at': datetime.now().isoformat(),
            'last_updated': None
        }
        
        # Generate widget blocks based on type
        if widget_type == DashboardWidgetType.PROGRESS_BAR:
            widget['blocks'] = self._create_progress_bar_blocks(config)
        elif widget_type == DashboardWidgetType.MILESTONE_TRACKER:
            widget['blocks'] = self._create_milestone_blocks(config)
        elif widget_type == DashboardWidgetType.ACTIVITY_TIMELINE:
            widget['blocks'] = self._create_timeline_blocks(config)
        elif widget_type == DashboardWidgetType.STATUS_SUMMARY:
            widget['blocks'] = self._create_status_blocks(config)
        elif widget_type == DashboardWidgetType.METRIC_CARD:
            widget['blocks'] = self._create_metric_blocks(config)
        elif widget_type == DashboardWidgetType.CHART_VIEW:
            widget['blocks'] = self._create_chart_blocks(config)
        
        return widget
    
    def _create_progress_bar_blocks(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create progress bar blocks using Notion elements.
        
        Args:
            config: Progress bar configuration
            
        Returns:
            List of Notion blocks
        """
        progress = config.get('progress', 0)
        total = config.get('total', 100)
        percentage = (progress / total * 100) if total > 0 else 0
        
        # Create visual progress bar using emoji blocks
        filled_blocks = int(percentage / 10)
        empty_blocks = 10 - filled_blocks
        progress_visual = '🟩' * filled_blocks + '⬜' * empty_blocks
        
        return [
            {
                'type': 'heading_3',
                'heading_3': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': config.get('title', 'Progress')}
                    }]
                }
            },
            {
                'type': 'callout',
                'callout': {
                    'icon': {'emoji': '📊'},
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': f'{progress_visual} {percentage:.1f}%'}
                    }]
                }
            },
            {
                'type': 'paragraph',
                'paragraph': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': f'{progress} of {total} completed'}
                    }]
                }
            }
        ]
    
    def _create_milestone_blocks(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create milestone tracker blocks.
        
        Args:
            config: Milestone configuration
            
        Returns:
            List of Notion blocks
        """
        milestones = config.get('milestones', [])
        blocks = [
            {
                'type': 'heading_3',
                'heading_3': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': 'Milestones'}
                    }]
                }
            }
        ]
        
        for milestone in milestones:
            status_emoji = '✅' if milestone['completed'] else '⏳'
            blocks.append({
                'type': 'to_do',
                'to_do': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': f"{status_emoji} {milestone['name']} - {milestone['date']}"}
                    }],
                    'checked': milestone['completed']
                }
            })
        
        return blocks
    
    def _create_timeline_blocks(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create activity timeline blocks.
        
        Args:
            config: Timeline configuration
            
        Returns:
            List of Notion blocks
        """
        activities = config.get('activities', [])
        blocks = [
            {
                'type': 'heading_3',
                'heading_3': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': 'Recent Activity'}
                    }]
                }
            }
        ]
        
        for activity in activities[-5:]:  # Show last 5 activities
            blocks.append({
                'type': 'bulleted_list_item',
                'bulleted_list_item': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': f"{activity['timestamp']}: {activity['description']}"}
                    }]
                }
            })
        
        return blocks
    
    def _create_status_blocks(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create status summary blocks.
        
        Args:
            config: Status configuration
            
        Returns:
            List of Notion blocks
        """
        statuses = config.get('statuses', {})
        blocks = [
            {
                'type': 'heading_3',
                'heading_3': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': 'Status Summary'}
                    }]
                }
            }
        ]
        
        # Create a table-like view using columns
        status_items = []
        for status_name, count in statuses.items():
            emoji = self._get_status_emoji(status_name)
            status_items.append(f"{emoji} {status_name}: {count}")
        
        blocks.append({
            'type': 'callout',
            'callout': {
                'icon': {'emoji': '📋'},
                'rich_text': [{
                    'type': 'text',
                    'text': {'content': ' | '.join(status_items)}
                }]
            }
        })
        
        return blocks
    
    def _create_metric_blocks(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create metric card blocks.
        
        Args:
            config: Metric configuration
            
        Returns:
            List of Notion blocks
        """
        return [
            {
                'type': 'callout',
                'callout': {
                    'icon': {'emoji': config.get('icon', '📈')},
                    'rich_text': [
                        {
                            'type': 'text',
                            'text': {'content': config.get('label', 'Metric')},
                            'annotations': {'bold': True}
                        },
                        {
                            'type': 'text',
                            'text': {'content': f"\n{config.get('value', '0')}"}
                        }
                    ]
                }
            }
        ]
    
    def _create_chart_blocks(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chart view blocks using ASCII art.
        
        Args:
            config: Chart configuration
            
        Returns:
            List of Notion blocks
        """
        data_points = config.get('data', [])
        chart_type = config.get('chart_type', 'bar')
        
        if chart_type == 'bar':
            chart = self._generate_bar_chart(data_points)
        else:
            chart = "Chart visualization"
        
        return [
            {
                'type': 'heading_3',
                'heading_3': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': config.get('title', 'Chart')}
                    }]
                }
            },
            {
                'type': 'code',
                'code': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': chart}
                    }],
                    'language': 'plain text'
                }
            }
        ]
    
    def _generate_bar_chart(self, data_points: List[Dict[str, Any]]) -> str:
        """Generate ASCII bar chart.
        
        Args:
            data_points: List of data points with label and value
            
        Returns:
            ASCII bar chart string
        """
        if not data_points:
            return "No data available"
        
        max_value = max(point['value'] for point in data_points)
        chart_lines = []
        
        for point in data_points:
            bar_length = int((point['value'] / max_value) * 20) if max_value > 0 else 0
            bar = '█' * bar_length
            chart_lines.append(f"{point['label']:10} {bar} {point['value']}")
        
        return '\n'.join(chart_lines)
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status.
        
        Args:
            status: Status name
            
        Returns:
            Status emoji
        """
        status_emojis = {
            'pending': '⏳',
            'in_progress': '🔄',
            'review': '👀',
            'done': '✅',
            'blocked': '🚫',
            'deferred': '⏸️',
            'cancelled': '❌'
        }
        return status_emojis.get(status.lower(), '📌')
    
    def update_dashboard(self, dashboard_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Update dashboard with latest data.
        
        Args:
            dashboard_id: Dashboard identifier
            state: Current deployment state
            
        Returns:
            Update result
        """
        if dashboard_id not in self.dashboards:
            return {'success': False, 'error': 'Dashboard not found'}
        
        dashboard = self.dashboards[dashboard_id]
        updated_widgets = 0
        
        # Update each widget
        for widget_id in dashboard['widgets']:
            widget = next((w for w in self.widgets if w['id'] == widget_id), None)
            if widget:
                # Update widget data based on state
                self._update_widget_data(widget, state)
                widget['last_updated'] = datetime.now().isoformat()
                updated_widgets += 1
        
        dashboard['last_updated'] = datetime.now().isoformat()
        
        return {
            'success': True,
            'widgets_updated': updated_widgets
        }
    
    def _update_widget_data(self, widget: Dict[str, Any], state: Dict[str, Any]):
        """Update widget data from state.
        
        Args:
            widget: Widget to update
            state: Current deployment state
        """
        widget_type = DashboardWidgetType(widget['type'])
        
        if widget_type == DashboardWidgetType.PROGRESS_BAR:
            # Update progress from state
            tasks = state.get('tasks', [])
            completed = sum(1 for t in tasks if t.get('status') == 'done')
            widget['config']['progress'] = completed
            widget['config']['total'] = len(tasks)
        
        elif widget_type == DashboardWidgetType.STATUS_SUMMARY:
            # Update status counts
            tasks = state.get('tasks', [])
            statuses = {}
            for task in tasks:
                status = task.get('status', 'pending')
                statuses[status] = statuses.get(status, 0) + 1
            widget['config']['statuses'] = statuses
    
    def create_deployment_dashboard(self, state: Dict[str, Any]) -> str:
        """Create deployment progress dashboard page.
        
        Args:
            state: Current deployment state
            
        Returns:
            Dashboard page ID
        """
        # Calculate metrics
        tasks = state.get('tasks', [])
        completed_tasks = sum(1 for t in tasks if t.get('status') == 'done')
        total_tasks = len(tasks)
        
        databases = state.get('databases', {})
        pages = state.get('pages', {})
        
        # Create dashboard configuration
        dashboard_config = {
            'title': 'Estate Planning Deployment Dashboard',
            'parent_page_id': state.get('parent_page_id'),
            'widgets': [
                {
                    'type': DashboardWidgetType.PROGRESS_BAR.value,
                    'title': 'Overall Progress',
                    'progress': completed_tasks,
                    'total': total_tasks
                },
                {
                    'type': DashboardWidgetType.METRIC_CARD.value,
                    'label': 'Databases Created',
                    'value': len(databases),
                    'icon': '🗄️'
                },
                {
                    'type': DashboardWidgetType.METRIC_CARD.value,
                    'label': 'Pages Created',
                    'value': len(pages),
                    'icon': '📄'
                },
                {
                    'type': DashboardWidgetType.STATUS_SUMMARY.value,
                    'statuses': self._calculate_status_distribution(tasks)
                },
                {
                    'type': DashboardWidgetType.MILESTONE_TRACKER.value,
                    'milestones': self._extract_milestones(state)
                },
                {
                    'type': DashboardWidgetType.ACTIVITY_TIMELINE.value,
                    'activities': self._get_recent_activities(state)
                }
            ]
        }
        
        # Create dashboard
        result = self.create_dashboard('main_dashboard', dashboard_config)
        
        # Store in state
        if 'dashboards' not in state:
            state['dashboards'] = {}
        state['dashboards']['main_dashboard'] = result
        
        return 'main_dashboard'
    
    def _calculate_status_distribution(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate task status distribution.
        
        Args:
            tasks: List of tasks
            
        Returns:
            Status counts
        """
        distribution = {}
        for task in tasks:
            status = task.get('status', 'pending')
            distribution[status] = distribution.get(status, 0) + 1
        return distribution
    
    def _extract_milestones(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract milestones from state.
        
        Args:
            state: Current deployment state
            
        Returns:
            List of milestones
        """
        return [
            {
                'name': 'Database Setup',
                'date': '2024-01-01',
                'completed': len(state.get('databases', {})) > 0
            },
            {
                'name': 'Page Creation',
                'date': '2024-01-02',
                'completed': len(state.get('pages', {})) > 0
            },
            {
                'name': 'Data Import',
                'date': '2024-01-03',
                'completed': state.get('csv_imported', False)
            },
            {
                'name': 'Permissions Setup',
                'date': '2024-01-04',
                'completed': state.get('permissions_configured', False)
            },
            {
                'name': 'Deployment Complete',
                'date': '2024-01-05',
                'completed': state.get('deployment_complete', False)
            }
        ]
    
    def _get_recent_activities(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recent deployment activities.
        
        Args:
            state: Current deployment state
            
        Returns:
            List of recent activities
        """
        activities = []
        
        # Add activities from state
        if 'deployment_log' in state:
            for log_entry in state['deployment_log'][-10:]:
                activities.append({
                    'timestamp': log_entry.get('timestamp', 'Unknown'),
                    'description': log_entry.get('message', 'Activity')
                })
        
        return activities


def setup_progress_dashboard(state: Dict[str, Any]) -> Dict[str, Any]:
    """Setup progress tracking dashboard for Estate Planning system.
    
    Args:
        state: Current deployment state
        
    Returns:
        Setup results
    """
    manager = ProgressDashboardManager()
    
    # Create main deployment dashboard
    dashboard_id = manager.create_deployment_dashboard(state)
    
    # Store manager in state
    state['dashboard_manager'] = manager
    
    # Get dashboard statistics
    dashboard = manager.dashboards.get(dashboard_id, {})
    
    return {
        'dashboard_created': dashboard_id is not None,
        'widgets_count': len(dashboard.get('widgets', [])),
        'metrics_tracked': len(manager.metrics),
        'last_updated': dashboard.get('last_updated')
    }