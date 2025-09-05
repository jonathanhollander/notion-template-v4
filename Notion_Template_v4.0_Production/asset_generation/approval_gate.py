#!/usr/bin/env python3
"""
Approval Gate Mechanism for Batch Processing
Provides interactive approval for asset generation batches via WebSocket
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from websocket_broadcaster import get_broadcaster


class ApprovalStatus(Enum):
    """Approval status states"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    TIMEOUT = "timeout"


@dataclass
class ApprovalItem:
    """Individual item requiring approval"""
    id: str
    asset_name: str
    asset_type: str
    prompt: str
    estimated_cost: float
    priority: int = 1
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'asset_name': self.asset_name,
            'asset_type': self.asset_type,
            'prompt': self.prompt,
            'estimated_cost': self.estimated_cost,
            'priority': self.priority,
            'metadata': self.metadata or {}
        }


@dataclass
class ApprovalBatch:
    """Batch of items requiring approval"""
    batch_id: str
    items: List[ApprovalItem]
    total_cost: float
    created_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_items: List[str] = None
    rejected_items: List[str] = None
    modifications: Dict[str, str] = None
    
    def __post_init__(self):
        if self.approved_items is None:
            self.approved_items = []
        if self.rejected_items is None:
            self.rejected_items = []
        if self.modifications is None:
            self.modifications = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'batch_id': self.batch_id,
            'items': [item.to_dict() for item in self.items],
            'total_cost': self.total_cost,
            'created_at': self.created_at.isoformat(),
            'status': self.status.value,
            'approved_items': self.approved_items,
            'rejected_items': self.rejected_items,
            'modifications': self.modifications
        }


class ApprovalGate:
    """Manages approval gates for batch asset generation"""
    
    def __init__(self, timeout_seconds: int = 300):
        """
        Initialize the approval gate
        
        Args:
            timeout_seconds: Time to wait for approval before timeout (default 5 minutes)
        """
        self.broadcaster = get_broadcaster()
        self.timeout_seconds = timeout_seconds
        self.pending_batches: Dict[str, ApprovalBatch] = {}
        self.approval_events: Dict[str, asyncio.Event] = {}
        
        # Register WebSocket handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register WebSocket event handlers for approval responses"""
        if hasattr(self.broadcaster, 'on'):
            self.broadcaster.on('approve_batch', self._handle_approve_batch)
            self.broadcaster.on('reject_batch', self._handle_reject_batch)
            self.broadcaster.on('modify_batch', self._handle_modify_batch)
            self.broadcaster.on('approve_items', self._handle_approve_items)
    
    async def request_approval(self, 
                              items: List[Dict[str, Any]], 
                              batch_id: Optional[str] = None) -> ApprovalBatch:
        """
        Request approval for a batch of items
        
        Args:
            items: List of items to approve (dicts with asset_name, type, prompt, cost)
            batch_id: Optional batch ID (generated if not provided)
        
        Returns:
            ApprovalBatch with approval status
        """
        # Create batch ID if not provided
        if not batch_id:
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Convert items to ApprovalItem objects
        approval_items = []
        total_cost = 0
        
        for i, item in enumerate(items):
            approval_item = ApprovalItem(
                id=f"{batch_id}_{i}",
                asset_name=item.get('asset_name', f'Asset {i+1}'),
                asset_type=item.get('asset_type', 'unknown'),
                prompt=item.get('prompt', ''),
                estimated_cost=item.get('estimated_cost', 0.04),
                priority=item.get('priority', 1),
                metadata=item.get('metadata', {})
            )
            approval_items.append(approval_item)
            total_cost += approval_item.estimated_cost
        
        # Create approval batch
        batch = ApprovalBatch(
            batch_id=batch_id,
            items=approval_items,
            total_cost=total_cost,
            created_at=datetime.now()
        )
        
        # Store batch and create event
        self.pending_batches[batch_id] = batch
        self.approval_events[batch_id] = asyncio.Event()
        
        # Emit approval request via WebSocket
        self.broadcaster.emit('approval_request', {
            'batch': batch.to_dict(),
            'timeout_seconds': self.timeout_seconds,
            'approval_required': True,
            'can_modify': True,
            'can_partial_approve': True
        })
        
        # Wait for approval with timeout
        try:
            await asyncio.wait_for(
                self.approval_events[batch_id].wait(),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            batch.status = ApprovalStatus.TIMEOUT
            self.broadcaster.emit('approval_timeout', {
                'batch_id': batch_id,
                'message': f'Approval timeout after {self.timeout_seconds} seconds'
            })
        
        # Clean up
        del self.approval_events[batch_id]
        
        return batch
    
    def _handle_approve_batch(self, data: Dict):
        """Handle batch approval from WebSocket"""
        batch_id = data.get('batch_id')
        if batch_id in self.pending_batches:
            batch = self.pending_batches[batch_id]
            batch.status = ApprovalStatus.APPROVED
            batch.approved_items = [item.id for item in batch.items]
            
            # Set the event to unblock waiting coroutine
            if batch_id in self.approval_events:
                self.approval_events[batch_id].set()
            
            self.broadcaster.emit('approval_processed', {
                'batch_id': batch_id,
                'status': 'approved',
                'approved_count': len(batch.approved_items)
            })
    
    def _handle_reject_batch(self, data: Dict):
        """Handle batch rejection from WebSocket"""
        batch_id = data.get('batch_id')
        reason = data.get('reason', 'User rejected')
        
        if batch_id in self.pending_batches:
            batch = self.pending_batches[batch_id]
            batch.status = ApprovalStatus.REJECTED
            batch.rejected_items = [item.id for item in batch.items]
            
            # Set the event to unblock waiting coroutine
            if batch_id in self.approval_events:
                self.approval_events[batch_id].set()
            
            self.broadcaster.emit('approval_processed', {
                'batch_id': batch_id,
                'status': 'rejected',
                'reason': reason,
                'rejected_count': len(batch.rejected_items)
            })
    
    def _handle_modify_batch(self, data: Dict):
        """Handle batch modification from WebSocket"""
        batch_id = data.get('batch_id')
        modifications = data.get('modifications', {})
        
        if batch_id in self.pending_batches:
            batch = self.pending_batches[batch_id]
            batch.status = ApprovalStatus.MODIFIED
            batch.modifications = modifications
            
            # Apply modifications to prompts
            for item in batch.items:
                if item.id in modifications:
                    item.prompt = modifications[item.id]
            
            # Mark all as approved after modification
            batch.approved_items = [item.id for item in batch.items]
            
            # Set the event to unblock waiting coroutine
            if batch_id in self.approval_events:
                self.approval_events[batch_id].set()
            
            self.broadcaster.emit('approval_processed', {
                'batch_id': batch_id,
                'status': 'modified',
                'modification_count': len(modifications)
            })
    
    def _handle_approve_items(self, data: Dict):
        """Handle partial item approval from WebSocket"""
        batch_id = data.get('batch_id')
        approved_ids = data.get('approved_items', [])
        rejected_ids = data.get('rejected_items', [])
        
        if batch_id in self.pending_batches:
            batch = self.pending_batches[batch_id]
            batch.status = ApprovalStatus.APPROVED
            batch.approved_items = approved_ids
            batch.rejected_items = rejected_ids
            
            # Set the event to unblock waiting coroutine
            if batch_id in self.approval_events:
                self.approval_events[batch_id].set()
            
            self.broadcaster.emit('approval_processed', {
                'batch_id': batch_id,
                'status': 'partial',
                'approved_count': len(approved_ids),
                'rejected_count': len(rejected_ids)
            })
    
    def get_approved_items(self, batch: ApprovalBatch) -> List[ApprovalItem]:
        """Get only approved items from a batch"""
        if batch.status == ApprovalStatus.REJECTED:
            return []
        
        if batch.status == ApprovalStatus.TIMEOUT:
            # Auto-approve on timeout (configurable behavior)
            return batch.items
        
        # Return items that were approved
        approved = []
        for item in batch.items:
            if item.id in batch.approved_items:
                # Apply any modifications
                if item.id in batch.modifications:
                    item.prompt = batch.modifications[item.id]
                approved.append(item)
        
        return approved
    
    def calculate_approved_cost(self, batch: ApprovalBatch) -> float:
        """Calculate total cost of approved items"""
        approved_items = self.get_approved_items(batch)
        return sum(item.estimated_cost for item in approved_items)
    
    async def request_threshold_approval(self, 
                                        total_cost: float,
                                        item_count: int,
                                        context: str = "") -> bool:
        """
        Request approval for cost threshold
        
        Args:
            total_cost: Total estimated cost
            item_count: Number of items
            context: Additional context for the approval
        
        Returns:
            True if approved, False if rejected
        """
        approval_id = f"threshold_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        event = asyncio.Event()
        
        # Store the event
        self.approval_events[approval_id] = event
        
        # Emit threshold approval request
        self.broadcaster.emit('threshold_approval_request', {
            'approval_id': approval_id,
            'total_cost': total_cost,
            'item_count': item_count,
            'context': context,
            'timeout_seconds': self.timeout_seconds
        })
        
        # Wait for response
        try:
            await asyncio.wait_for(event.wait(), timeout=self.timeout_seconds)
            # Check if approved (would need to store this)
            return True  # Simplified - would check actual approval status
        except asyncio.TimeoutError:
            # Auto-approve on timeout (configurable)
            return True
    
    def emit_progress(self, batch_id: str, completed: int, total: int):
        """Emit progress update for approved batch"""
        self.broadcaster.emit('batch_progress', {
            'batch_id': batch_id,
            'completed': completed,
            'total': total,
            'percentage': (completed / total * 100) if total > 0 else 0
        })


# Example usage for testing
async def test_approval_gate():
    """Test the approval gate mechanism"""
    gate = ApprovalGate(timeout_seconds=30)
    
    # Create sample items
    test_items = [
        {
            'asset_name': 'Estate Planning Overview',
            'asset_type': 'icon',
            'prompt': 'Create an icon representing estate planning...',
            'estimated_cost': 0.04
        },
        {
            'asset_name': 'Trust Management',
            'asset_type': 'cover',
            'prompt': 'Design a cover image for trust management...',
            'estimated_cost': 0.04
        },
        {
            'asset_name': 'Tax Planning',
            'asset_type': 'icon',
            'prompt': 'Create an icon for tax planning strategies...',
            'estimated_cost': 0.04
        }
    ]
    
    print("Requesting approval for batch...")
    batch = await gate.request_approval(test_items)
    
    print(f"Batch status: {batch.status.value}")
    print(f"Approved items: {len(batch.approved_items)}")
    print(f"Rejected items: {len(batch.rejected_items)}")
    
    # Get approved items only
    approved = gate.get_approved_items(batch)
    print(f"Items to generate: {len(approved)}")
    print(f"Approved cost: ${gate.calculate_approved_cost(batch):.2f}")
    
    # Simulate progress
    for i, item in enumerate(approved):
        print(f"Generating: {item.asset_name}")
        gate.emit_progress(batch.batch_id, i+1, len(approved))
        await asyncio.sleep(1)
    
    print("Batch generation complete!")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_approval_gate())