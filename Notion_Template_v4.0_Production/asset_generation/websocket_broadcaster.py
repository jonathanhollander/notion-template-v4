#!/usr/bin/env python3
"""
WebSocket Broadcasting Module
Enables real-time status updates from asset generation to web interface
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from flask_socketio import SocketIO
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    print("Warning: flask-socketio not available. Real-time updates disabled.")

class WebSocketBroadcaster:
    """Handles WebSocket broadcasting for real-time status updates"""
    
    _instance: Optional['WebSocketBroadcaster'] = None
    _socketio: Optional[SocketIO] = None
    
    def __new__(cls):
        """Singleton pattern to ensure single broadcaster instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the broadcaster"""
        if not hasattr(self, 'initialized'):
            self.logger = logging.getLogger('WebSocketBroadcaster')
            self.enabled = False
            self.initialized = True
            self.generation_stats = {
                'prompts_generated': 0,
                'images_created': 0,
                'total_cost': 0.0,
                'start_time': None,
                'current_phase': 'idle'
            }
    
    def set_socketio(self, socketio: SocketIO):
        """Set the SocketIO instance from the web server"""
        if SOCKETIO_AVAILABLE and socketio:
            self._socketio = socketio
            self.enabled = True
            self.logger.info("WebSocket broadcasting enabled")
        else:
            self.logger.warning("WebSocket broadcasting not available")
    
    def emit(self, event: str, data: Dict[str, Any]):
        """Emit an event to all connected clients"""
        if self.enabled and self._socketio:
            try:
                self._socketio.emit(event, data, broadcast=True)
                self.logger.debug(f"Emitted {event}: {data}")
            except Exception as e:
                self.logger.error(f"Error emitting {event}: {e}")
        else:
            # Log the event even if not broadcasting
            self.logger.debug(f"Would emit {event}: {data}")
    
    def update_generation_status(self, phase: str, progress: int = 0, **kwargs):
        """Update and broadcast generation status"""
        self.generation_stats['current_phase'] = phase
        
        status_data = {
            'phase': phase,
            'progress': progress,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        # Update internal stats
        if 'prompts_count' in kwargs:
            self.generation_stats['prompts_generated'] = kwargs['prompts_count']
        if 'images_count' in kwargs:
            self.generation_stats['images_created'] = kwargs['images_count']
        if 'cost' in kwargs:
            self.generation_stats['total_cost'] = kwargs['cost']
        
        self.emit('generation_status', status_data)
    
    def emit_prompt_generation(self, model: str, message: str, **kwargs):
        """Emit prompt generation event"""
        data = {
            'model': model,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        self.emit('prompt_generation', data)
    
    def emit_image_generation(self, asset_type: str, message: str, **kwargs):
        """Emit image generation event"""
        data = {
            'asset_type': asset_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        # Update images count if provided
        if 'images_completed' in kwargs:
            self.generation_stats['images_created'] = kwargs['images_completed']
        
        self.emit('image_generation', data)
    
    def emit_circuit_breaker_status(self, state: str, **kwargs):
        """Emit circuit breaker status update"""
        data = {
            'state': state,  # 'CLOSED', 'OPEN', 'HALF_OPEN'
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        self.emit('circuit_breaker_status', data)
    
    def emit_error(self, error: str, **kwargs):
        """Emit error event"""
        data = {
            'error': error,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        self.emit('generation_error', data)
    
    def emit_log(self, message: str, level: str = 'info'):
        """Emit log message for display in web interface"""
        data = {
            'message': message,
            'level': level,  # 'info', 'warning', 'error'
            'timestamp': datetime.now().isoformat()
        }
        self.emit('log_message', data)
    
    def start_generation(self, mode: str = 'sample', total_items: int = 0):
        """Mark the start of a generation session"""
        self.generation_stats = {
            'prompts_generated': 0,
            'images_created': 0,
            'total_cost': 0.0,
            'start_time': datetime.now(),
            'current_phase': 'initializing',
            'mode': mode,
            'total_items': total_items
        }
        
        self.update_generation_status(
            phase='initializing',
            progress=0,
            mode=mode,
            total_items=total_items
        )
        
        self.emit_log(f"🚀 Starting {mode} generation ({total_items} items)", 'info')
    
    def complete_generation(self):
        """Mark the completion of a generation session"""
        duration = None
        if self.generation_stats['start_time']:
            duration = (datetime.now() - self.generation_stats['start_time']).total_seconds()
        
        self.update_generation_status(
            phase='completed',
            progress=100,
            prompts_count=self.generation_stats['prompts_generated'],
            images_count=self.generation_stats['images_created'],
            cost=self.generation_stats['total_cost'],
            duration=duration
        )
        
        self.emit_log(
            f"✅ Generation completed: {self.generation_stats['images_created']} images, "
            f"${self.generation_stats['total_cost']:.2f} cost", 
            'info'
        )
    
    def update_progress(self, completed: int, total: int, message: str = None):
        """Update progress percentage"""
        if total > 0:
            progress = int((completed / total) * 100)
        else:
            progress = 0
        
        self.update_generation_status(
            phase=self.generation_stats['current_phase'],
            progress=progress,
            completed=completed,
            total=total
        )
        
        if message:
            self.emit_log(message, 'info')


# Global broadcaster instance
broadcaster = WebSocketBroadcaster()


def get_broadcaster() -> WebSocketBroadcaster:
    """Get the global broadcaster instance"""
    return broadcaster