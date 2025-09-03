#!/usr/bin/env python3
"""
Approval Workflow Service for Estate Planning Concierge v4.0
Orchestrates the complete competitive prompt approval workflow.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from ..utils.database_manager import AssetDatabase
from .prompt_competition_service import PromptCompetitionService
from ..quality_scorer import QualityScorer
from ..prompts import ESTATE_PROMPT_BUILDER


class ApprovalWorkflowService:
    """Orchestrates the complete approval workflow from prompt competition to final approval.
    
    Workflow:
    1. Create competitive prompts for each asset type
    2. Evaluate prompt quality with AI models
    3. Present results to human reviewers via web dashboard
    4. Store human decisions in database
    5. Mark competitions as complete when human decisions are made
    """
    
    def __init__(self, db_path: str = "estate_planning_assets.db", api_key: str = None):
        """Initialize the approval workflow service.
        
        Args:
            db_path: Path to the approval database
            api_key: OpenRouter API key for AI services
        """
        self.db_path = db_path
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        
        # Initialize components
        self.db = AssetDatabase(db_path)
        self.prompt_service = PromptCompetitionService(self.db, self.api_key)
        self.quality_scorer = QualityScorer(api_key=self.api_key)
        
        self.logger = self._setup_logger()
        
        if not self.api_key:
            self.logger.warning("No OpenRouter API key - AI services will use fallbacks")
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the service."""
        logger = logging.getLogger('ApprovalWorkflowService')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def initialize(self):
        """Initialize the database and services."""
        await self.db.init_database()
        self.logger.info("Approval workflow service initialized")
    
    async def create_full_workflow(
        self, 
        asset_counts: Optional[Dict[str, int]] = None,
        category: str = "Estate Planning"
    ) -> Dict[str, Any]:
        """Create complete approval workflow for all asset types.
        
        Args:
            asset_counts: Optional custom asset counts
            category: Category name for competitions
            
        Returns:
            Workflow creation statistics
        """
        if asset_counts is None:
            # Default asset counts for Estate Planning Concierge v4.0
            asset_counts = {
                'icons': 150,
                'covers': 100,  
                'textures': 50,
                'letter_headers': 150,
                'database_icons': 40
            }
        
        self.logger.info(f"Creating approval workflow for {sum(asset_counts.values())} total assets")
        
        workflow_stats = {
            'start_time': datetime.now().isoformat(),
            'competitions_created': 0,
            'total_assets': sum(asset_counts.values()),
            'asset_breakdown': asset_counts,
            'errors': []
        }
        
        # Create competitions for each asset type
        for asset_type, count in asset_counts.items():
            try:
                self.logger.info(f"Creating {count} competitions for {asset_type}")
                
                competition_ids = await self.prompt_service.create_competitions_for_asset_type(
                    asset_type, count, category
                )
                
                workflow_stats['competitions_created'] += len(competition_ids)
                workflow_stats[f'{asset_type}_competitions'] = competition_ids
                
                self.logger.info(f"✅ Created {len(competition_ids)} {asset_type} competitions")
                
            except Exception as e:
                error_msg = f"Failed to create {asset_type} competitions: {e}"
                self.logger.error(error_msg)
                workflow_stats['errors'].append(error_msg)
        
        workflow_stats['end_time'] = datetime.now().isoformat()
        workflow_stats['success'] = len(workflow_stats['errors']) == 0
        
        self.logger.info(f"✅ Workflow creation complete: {workflow_stats['competitions_created']} competitions created")
        
        return workflow_stats
    
    async def evaluate_all_competitions(self, max_competitions: int = None) -> Dict[str, Any]:
        """Evaluate all pending competitions with AI quality scoring.
        
        Args:
            max_competitions: Optional limit on competitions to evaluate
            
        Returns:
            Evaluation statistics
        """
        self.logger.info("Starting batch evaluation of all pending competitions")
        
        evaluation_stats = {
            'start_time': datetime.now().isoformat(),
            'competitions_evaluated': 0,
            'total_pending': 0,
            'evaluation_results': [],
            'errors': []
        }
        
        try:
            # Get pending competitions count
            pending_competitions = await self.db.get_pending_competitions()
            evaluation_stats['total_pending'] = len(pending_competitions)
            
            if max_competitions:
                pending_competitions = pending_competitions[:max_competitions]
            
            self.logger.info(f"Found {evaluation_stats['total_pending']} pending competitions")
            self.logger.info(f"Evaluating {len(pending_competitions)} competitions")
            
            # Evaluate competitions using quality scorer
            evaluated_ids = await self.quality_scorer.batch_evaluate_pending_competitions(
                self.db, 
                max_competitions=max_competitions
            )
            
            evaluation_stats['competitions_evaluated'] = len(evaluated_ids)
            evaluation_stats['evaluation_results'] = evaluated_ids
            evaluation_stats['success'] = True
            
        except Exception as e:
            error_msg = f"Batch evaluation failed: {e}"
            self.logger.error(error_msg)
            evaluation_stats['errors'].append(error_msg)
            evaluation_stats['success'] = False
        
        evaluation_stats['end_time'] = datetime.now().isoformat()
        
        self.logger.info(f"✅ Batch evaluation complete: {evaluation_stats['competitions_evaluated']} competitions evaluated")
        
        return evaluation_stats
    
    async def get_workflow_status(self) -> Dict[str, Any]:
        """Get current status of the approval workflow.
        
        Returns:
            Complete workflow status information
        """
        await self.db.init_database()
        
        async with self.db.get_connection() as conn:
            # Get competition statistics by status
            cursor = await conn.execute("""
                SELECT competition_status, COUNT(*) as count 
                FROM prompt_competitions 
                GROUP BY competition_status
            """)
            status_counts = {row['competition_status']: row['count'] for row in await cursor.fetchall()}
            
            # Get asset type breakdown
            cursor = await conn.execute("""
                SELECT asset_type, COUNT(*) as count 
                FROM prompt_competitions 
                GROUP BY asset_type
            """)
            asset_type_counts = {row['asset_type']: row['count'] for row in await cursor.fetchall()}
            
            # Get recent activity
            cursor = await conn.execute("""
                SELECT * FROM prompt_competitions 
                ORDER BY updated_at DESC 
                LIMIT 10
            """)
            recent_activity = [dict(row) for row in await cursor.fetchall()]
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'competition_status': status_counts,
            'asset_type_breakdown': asset_type_counts,
            'total_competitions': sum(status_counts.values()),
            'pending_count': status_counts.get('pending', 0),
            'evaluated_count': status_counts.get('evaluated', 0),
            'decided_count': status_counts.get('decided', 0),
            'completed_count': status_counts.get('completed', 0),
            'recent_activity': recent_activity,
            'workflow_progress': {
                'competitions_created': sum(status_counts.values()) > 0,
                'evaluations_complete': status_counts.get('pending', 0) == 0,
                'human_review_needed': status_counts.get('evaluated', 0) > 0,
                'ready_for_generation': status_counts.get('decided', 0) > 0,
                'fully_complete': status_counts.get('completed', 0) == sum(status_counts.values())
            }
        }
        
        return status
    
    async def run_complete_workflow(
        self, 
        asset_counts: Optional[Dict[str, int]] = None,
        evaluate_immediately: bool = True,
        max_evaluations: int = None
    ) -> Dict[str, Any]:
        """Run the complete approval workflow from start to evaluation.
        
        Note: Human review must be done via the web dashboard.
        
        Args:
            asset_counts: Optional custom asset counts
            evaluate_immediately: Whether to run evaluations after creating competitions
            max_evaluations: Optional limit on evaluations to run
            
        Returns:
            Complete workflow statistics
        """
        self.logger.info("🚀 Starting complete approval workflow")
        
        complete_stats = {
            'workflow_start': datetime.now().isoformat(),
            'phases_completed': [],
            'errors': []
        }
        
        try:
            # Phase 1: Create competitions
            self.logger.info("📋 Phase 1: Creating competitive prompts...")
            creation_stats = await self.create_full_workflow(asset_counts)
            complete_stats['creation_stats'] = creation_stats
            complete_stats['phases_completed'].append('creation')
            
            if not creation_stats['success']:
                raise Exception(f"Competition creation failed: {creation_stats['errors']}")
            
            # Phase 2: Evaluate competitions (if requested)
            if evaluate_immediately:
                self.logger.info("🎯 Phase 2: Evaluating prompt quality...")
                evaluation_stats = await self.evaluate_all_competitions(max_evaluations)
                complete_stats['evaluation_stats'] = evaluation_stats
                complete_stats['phases_completed'].append('evaluation')
                
                if not evaluation_stats['success']:
                    raise Exception(f"Evaluation failed: {evaluation_stats['errors']}")
            
            # Get final status
            complete_stats['final_status'] = await self.get_workflow_status()
            complete_stats['success'] = True
            
        except Exception as e:
            error_msg = f"Complete workflow failed: {e}"
            self.logger.error(error_msg)
            complete_stats['errors'].append(error_msg)
            complete_stats['success'] = False
        
        complete_stats['workflow_end'] = datetime.now().isoformat()
        
        # Print summary
        self.logger.info("=" * 60)
        self.logger.info("🏛️ ESTATE PLANNING CONCIERGE v4.0 - APPROVAL WORKFLOW COMPLETE")
        self.logger.info("=" * 60)
        
        if complete_stats['success']:
            self.logger.info("✅ Workflow executed successfully")
            self.logger.info(f"📊 Competitions created: {complete_stats['creation_stats']['competitions_created']}")
            if 'evaluation_stats' in complete_stats:
                self.logger.info(f"🎯 Competitions evaluated: {complete_stats['evaluation_stats']['competitions_evaluated']}")
            self.logger.info("🌐 Next step: Use the web dashboard for human review")
            self.logger.info("   python review_dashboard.py")
        else:
            self.logger.error("❌ Workflow failed")
            for error in complete_stats['errors']:
                self.logger.error(f"   - {error}")
        
        return complete_stats
    
    async def cleanup(self):
        """Clean up resources."""
        await self.db.close()
        self.logger.info("Approval workflow service cleaned up")


async def test_approval_workflow_service():
    """Test the approval workflow service."""
    print("🔄 Testing Approval Workflow Service...")
    
    # Initialize service
    service = ApprovalWorkflowService("test_approval_workflow.db")
    await service.initialize()
    
    try:
        # Test with small asset counts
        test_counts = {
            'icons': 3,
            'covers': 2,
            'textures': 2
        }
        
        # Run complete workflow
        stats = await service.run_complete_workflow(
            asset_counts=test_counts,
            evaluate_immediately=True,
            max_evaluations=5
        )
        
        print(f"✅ Workflow test complete!")
        print(f"📊 Success: {stats['success']}")
        print(f"📋 Competitions created: {stats['creation_stats']['competitions_created']}")
        
        if 'evaluation_stats' in stats:
            print(f"🎯 Competitions evaluated: {stats['evaluation_stats']['competitions_evaluated']}")
        
        # Get status
        status = await service.get_workflow_status()
        print(f"📈 Current status: {status['competition_status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        await service.cleanup()


if __name__ == "__main__":
    asyncio.run(test_approval_workflow_service())