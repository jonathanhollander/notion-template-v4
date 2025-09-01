#!/usr/bin/env python3
"""
Human Review Dashboard for Estate Planning Concierge v4.0
Interactive web interface for reviewing and selecting competitive prompts
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import logging

# Web framework imports
try:
    from flask import Flask, render_template, request, jsonify, send_from_directory
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available. Install with: pip install flask flask-cors")

# Our modules
from openrouter_orchestrator import OpenRouterOrchestrator, PromptCompetition
from quality_scorer import QualityScorer, CompetitiveEvaluation
from sample_generator import SampleGenerator
from sync_yaml_comprehensive import YAMLSyncComprehensive

@dataclass
class ReviewSession:
    """Represents a human review session"""
    session_id: str
    reviewer_name: str
    start_time: str
    pages_reviewed: int
    decisions_made: int
    quality_feedback: List[Dict[str, Any]]
    session_notes: str
    completion_status: str  # 'active', 'paused', 'completed'

@dataclass 
class HumanDecision:
    """Represents a human decision on prompt selection"""
    page_title: str
    page_category: str
    asset_type: str
    selected_prompt_id: str
    selected_model: str
    decision_reasoning: str
    quality_override: Optional[float] = None
    custom_modifications: Optional[str] = None
    decision_timestamp: str = None
    
    def __post_init__(self):
        if self.decision_timestamp is None:
            self.decision_timestamp = datetime.now().isoformat()

class ReviewDashboard:
    """Web-based human review dashboard for prompt selection"""
    
    def __init__(self, port: int = 5000):
        """Initialize the review dashboard"""
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required. Install with: pip install flask flask-cors")
            
        self.port = port
        self.app = Flask(__name__, template_folder='templates', static_folder='static')
        CORS(self.app)
        
        # Initialize our components
        self.orchestrator = OpenRouterOrchestrator()
        self.quality_scorer = QualityScorer()
        self.sample_generator = SampleGenerator()
        self.yaml_system = YAMLSyncComprehensive()
        
        self.logger = self._setup_logger()
        
        # Session management
        self.current_session: Optional[ReviewSession] = None
        self.human_decisions: List[HumanDecision] = []
        self.competitive_evaluations: List[CompetitiveEvaluation] = []
        
        # Setup routes
        self._setup_routes()
        self._create_templates()
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the dashboard"""
        logger = logging.getLogger('ReviewDashboard')
        logger.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler
        fh = logging.FileHandler('review_dashboard.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        return logger
    
    def _setup_routes(self):
        """Setup Flask routes for the dashboard"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return render_template('dashboard.html', 
                                 session=self.current_session,
                                 total_evaluations=len(self.competitive_evaluations),
                                 decisions_made=len(self.human_decisions))
        
        @self.app.route('/api/start-session', methods=['POST'])
        def start_session():
            """Start a new review session"""
            data = request.json
            reviewer_name = data.get('reviewer_name', 'Anonymous')
            
            self.current_session = ReviewSession(
                session_id=f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                reviewer_name=reviewer_name,
                start_time=datetime.now().isoformat(),
                pages_reviewed=0,
                decisions_made=0,
                quality_feedback=[],
                session_notes="",
                completion_status='active'
            )
            
            self.logger.info(f"Started review session: {self.current_session.session_id}")
            return jsonify({'success': True, 'session': asdict(self.current_session)})
        
        @self.app.route('/api/load-evaluations', methods=['POST'])
        def load_evaluations():
            """Load evaluation results for review"""
            try:
                data = request.json
                file_path = data.get('file_path', 'quality_evaluation_results.json')
                
                if Path(file_path).exists():
                    with open(file_path, 'r') as f:
                        results_data = json.load(f)
                    
                    # Convert back to CompetitiveEvaluation objects
                    self.competitive_evaluations = self._parse_evaluation_results(results_data)
                    
                    return jsonify({
                        'success': True,
                        'evaluations_loaded': len(self.competitive_evaluations),
                        'message': f'Loaded {len(self.competitive_evaluations)} competitive evaluations'
                    })
                else:
                    return jsonify({'success': False, 'error': f'File not found: {file_path}'}), 404
                    
            except Exception as e:
                self.logger.error(f"Failed to load evaluations: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/get-evaluation/<int:index>')
        def get_evaluation(index):
            """Get specific evaluation for review"""
            if 0 <= index < len(self.competitive_evaluations):
                evaluation = self.competitive_evaluations[index]
                
                # Convert to dict for JSON serialization
                eval_data = {
                    'index': index,
                    'page_title': evaluation.page_title,
                    'page_category': evaluation.page_category,
                    'asset_type': evaluation.asset_type,
                    'prompts': [
                        {
                            'id': pe.prompt_id,
                            'text': pe.prompt_text,
                            'model_source': pe.model_source,
                            'overall_score': pe.overall_score,
                            'weighted_score': pe.weighted_score,
                            'score_breakdown': pe.score_breakdown
                        }
                        for pe in evaluation.prompt_evaluations
                    ],
                    'winner': {
                        'id': evaluation.winner.prompt_id,
                        'model_source': evaluation.winner.model_source,
                        'score': evaluation.winner.weighted_score
                    } if evaluation.winner else None,
                    'consensus_scores': evaluation.consensus_scores,
                    'evaluation_summary': evaluation.evaluation_summary
                }
                
                return jsonify({'success': True, 'evaluation': eval_data})
            else:
                return jsonify({'success': False, 'error': 'Invalid evaluation index'}), 400
        
        @self.app.route('/api/make-decision', methods=['POST'])
        def make_decision():
            """Record human decision on prompt selection"""
            try:
                data = request.json
                
                decision = HumanDecision(
                    page_title=data['page_title'],
                    page_category=data['page_category'],
                    asset_type=data['asset_type'],
                    selected_prompt_id=data['selected_prompt_id'],
                    selected_model=data['selected_model'],
                    decision_reasoning=data.get('reasoning', ''),
                    quality_override=data.get('quality_override'),
                    custom_modifications=data.get('custom_modifications')
                )
                
                self.human_decisions.append(decision)
                
                # Update session stats
                if self.current_session:
                    self.current_session.decisions_made += 1
                    self.current_session.pages_reviewed += 1
                
                self.logger.info(f"Decision recorded: {decision.page_title} -> {decision.selected_model}")
                
                return jsonify({
                    'success': True,
                    'decision_id': len(self.human_decisions) - 1,
                    'total_decisions': len(self.human_decisions)
                })
                
            except Exception as e:
                self.logger.error(f"Failed to record decision: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/get-progress')
        def get_progress():
            """Get current review progress"""
            total_evaluations = len(self.competitive_evaluations)
            decisions_made = len(self.human_decisions)
            
            progress_data = {
                'total_evaluations': total_evaluations,
                'decisions_made': decisions_made,
                'completion_percentage': (decisions_made / total_evaluations * 100) if total_evaluations > 0 else 0,
                'session': asdict(self.current_session) if self.current_session else None
            }
            
            return jsonify(progress_data)
        
        @self.app.route('/api/export-decisions')
        def export_decisions():
            """Export all human decisions"""
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'session': asdict(self.current_session) if self.current_session else None,
                'total_decisions': len(self.human_decisions),
                'decisions': [asdict(decision) for decision in self.human_decisions],
                'decision_summary': self._generate_decision_summary()
            }
            
            output_file = f"human_decisions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Exported {len(self.human_decisions)} decisions to {output_file}")
            
            return jsonify({
                'success': True,
                'file_path': output_file,
                'total_decisions': len(self.human_decisions)
            })
        
        @self.app.route('/api/generate-final-prompts')
        def generate_final_prompts():
            """Generate final prompt selections based on human decisions"""
            final_prompts = {}
            
            for decision in self.human_decisions:
                key = f"{decision.page_title}_{decision.asset_type}"
                
                # Find the selected prompt from evaluations
                selected_prompt = self._find_prompt_by_decision(decision)
                
                if selected_prompt:
                    final_prompts[key] = {
                        'page_title': decision.page_title,
                        'page_category': decision.page_category,
                        'asset_type': decision.asset_type,
                        'selected_prompt': selected_prompt,
                        'human_reasoning': decision.decision_reasoning,
                        'custom_modifications': decision.custom_modifications,
                        'decision_timestamp': decision.decision_timestamp
                    }
            
            # Save final prompts
            output_file = f"final_selected_prompts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(final_prompts, f, indent=2)
            
            self.logger.info(f"Generated {len(final_prompts)} final prompt selections")
            
            return jsonify({
                'success': True,
                'final_prompts_file': output_file,
                'total_selections': len(final_prompts)
            })
    
    def _parse_evaluation_results(self, results_data: Dict[str, Any]) -> List[CompetitiveEvaluation]:
        """Parse evaluation results back into objects"""
        evaluations = []
        
        for eval_data in results_data.get('competitive_evaluations', []):
            # This is a simplified parsing - in practice you'd want to reconstruct the full objects
            evaluation = type('CompetitiveEvaluation', (), eval_data)()
            evaluations.append(evaluation)
        
        return evaluations
    
    def _find_prompt_by_decision(self, decision: HumanDecision) -> Optional[str]:
        """Find the actual prompt text based on human decision"""
        for evaluation in self.competitive_evaluations:
            if (evaluation.page_title == decision.page_title and 
                evaluation.asset_type == decision.asset_type):
                
                for prompt_eval in evaluation.prompt_evaluations:
                    if prompt_eval.prompt_id == decision.selected_prompt_id:
                        return prompt_eval.prompt_text
        
        return None
    
    def _generate_decision_summary(self) -> Dict[str, Any]:
        """Generate summary statistics for human decisions"""
        if not self.human_decisions:
            return {}
        
        model_preferences = {}
        asset_type_counts = {}
        
        for decision in self.human_decisions:
            # Count model preferences
            model_preferences[decision.selected_model] = model_preferences.get(decision.selected_model, 0) + 1
            
            # Count asset types
            asset_type_counts[decision.asset_type] = asset_type_counts.get(decision.asset_type, 0) + 1
        
        return {
            'total_decisions': len(self.human_decisions),
            'model_preference_ranking': sorted(model_preferences.items(), key=lambda x: x[1], reverse=True),
            'asset_type_distribution': asset_type_counts,
            'decisions_with_custom_modifications': sum(1 for d in self.human_decisions if d.custom_modifications),
            'decisions_with_quality_override': sum(1 for d in self.human_decisions if d.quality_override),
            'average_decision_reasoning_length': sum(len(d.decision_reasoning) for d in self.human_decisions) / len(self.human_decisions)
        }
    
    def _create_templates(self):
        """Create HTML templates for the dashboard"""
        templates_dir = Path('templates')
        templates_dir.mkdir(exist_ok=True)
        
        # Main dashboard template
        dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estate Planning Concierge v4.0 - Prompt Review Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }
        
        .header {
            background: linear-gradient(135deg, #8B4513 0%, #D2691E 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.2em;
            font-weight: 300;
        }
        
        .header p {
            margin: 5px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .dashboard-container {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 30px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .panel {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #8B4513;
        }
        
        .progress-panel {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        }
        
        .button {
            background: linear-gradient(135deg, #8B4513 0%, #D2691E 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            transition: transform 0.2s, box-shadow 0.2s;
            margin: 5px;
        }
        
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(139,69,19,0.3);
        }
        
        .button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .prompt-container {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            background: #fafafa;
        }
        
        .prompt-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .score-badge {
            background: #28a745;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 15px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #8B4513 0%, #D2691E 100%);
            transition: width 0.3s ease;
        }
        
        .review-area {
            min-height: 600px;
        }
        
        #evaluation-display {
            display: none;
        }
        
        .decision-form {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        
        textarea {
            width: 100%;
            min-height: 60px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: inherit;
            resize: vertical;
        }
        
        select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ Estate Planning Concierge v4.0</h1>
        <p>Ultra-Premium Prompt Review Dashboard</p>
    </div>
    
    <div class="dashboard-container">
        <div class="panel progress-panel">
            <h2>📊 Review Progress</h2>
            
            <div id="progress-info">
                <p><strong>Session:</strong> <span id="session-status">Not Started</span></p>
                <p><strong>Evaluations Loaded:</strong> <span id="evaluations-count">0</span></p>
                <p><strong>Decisions Made:</strong> <span id="decisions-count">0</span></p>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
            </div>
            <p id="progress-text">0% Complete</p>
            
            <h3>🎯 Session Controls</h3>
            <input type="text" id="reviewer-name" placeholder="Enter your name" style="width: 100%; margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
            <button class="button" onclick="startSession()">Start Review Session</button>
            <button class="button" onclick="loadEvaluations()">Load Evaluations</button>
            <button class="button" onclick="exportDecisions()" disabled id="export-btn">Export Decisions</button>
            
            <h3>📈 Quality Metrics</h3>
            <div id="quality-metrics">
                <p>Start a session to view metrics</p>
            </div>
        </div>
        
        <div class="panel review-area">
            <h2>🎨 Prompt Review</h2>
            
            <div id="pre-review-message">
                <p>👋 Welcome to the Estate Planning Concierge v4.0 Prompt Review Dashboard!</p>
                <p>This interface allows you to review AI-generated prompts and make final selections for our luxury estate planning assets.</p>
                <p>To get started:</p>
                <ol>
                    <li>Enter your name and start a review session</li>
                    <li>Load evaluation results from the quality scorer</li>
                    <li>Review competing prompts and make your selections</li>
                    <li>Export your decisions for final generation</li>
                </ol>
            </div>
            
            <div id="evaluation-display">
                <div class="evaluation-header">
                    <h3 id="eval-title">Loading...</h3>
                    <p id="eval-details">Category: <span id="eval-category"></span> | Type: <span id="eval-type"></span></p>
                </div>
                
                <div id="prompts-container">
                    <!-- Prompts will be loaded here -->
                </div>
                
                <div class="decision-form">
                    <h4>🤔 Make Your Decision</h4>
                    <select id="selected-prompt">
                        <option value="">Select a prompt...</option>
                    </select>
                    <textarea id="decision-reasoning" placeholder="Why did you choose this prompt? What makes it best for our estate planning users?"></textarea>
                    <textarea id="custom-modifications" placeholder="Any modifications or improvements? (optional)"></textarea>
                    
                    <button class="button" onclick="makeDecision()">Record Decision</button>
                    <button class="button" onclick="nextEvaluation()" style="background: #6c757d;">Next →</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentEvaluationIndex = 0;
        let totalEvaluations = 0;
        let sessionActive = false;
        
        async function startSession() {
            const reviewerName = document.getElementById('reviewer-name').value || 'Anonymous';
            
            try {
                const response = await fetch('/api/start-session', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({reviewer_name: reviewerName})
                });
                
                const result = await response.json();
                if (result.success) {
                    sessionActive = true;
                    document.getElementById('session-status').textContent = `Active (${reviewerName})`;
                    alert('Review session started successfully!');
                } else {
                    alert('Failed to start session');
                }
            } catch (error) {
                console.error('Error starting session:', error);
                alert('Error starting session');
            }
        }
        
        async function loadEvaluations() {
            if (!sessionActive) {
                alert('Please start a review session first');
                return;
            }
            
            try {
                const response = await fetch('/api/load-evaluations', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({file_path: 'quality_evaluation_results.json'})
                });
                
                const result = await response.json();
                if (result.success) {
                    totalEvaluations = result.evaluations_loaded;
                    document.getElementById('evaluations-count').textContent = totalEvaluations;
                    document.getElementById('export-btn').disabled = false;
                    
                    // Load first evaluation
                    await loadEvaluation(0);
                    
                    document.getElementById('pre-review-message').style.display = 'none';
                    document.getElementById('evaluation-display').style.display = 'block';
                    
                    alert(`Loaded ${totalEvaluations} evaluations successfully!`);
                } else {
                    alert(`Failed to load evaluations: ${result.error}`);
                }
            } catch (error) {
                console.error('Error loading evaluations:', error);
                alert('Error loading evaluations');
            }
        }
        
        async function loadEvaluation(index) {
            try {
                const response = await fetch(`/api/get-evaluation/${index}`);
                const result = await response.json();
                
                if (result.success) {
                    const evaluation = result.evaluation;
                    
                    // Update header
                    document.getElementById('eval-title').textContent = evaluation.page_title;
                    document.getElementById('eval-category').textContent = evaluation.page_category;
                    document.getElementById('eval-type').textContent = evaluation.asset_type;
                    
                    // Update prompts container
                    const container = document.getElementById('prompts-container');
                    container.innerHTML = '';
                    
                    // Update selection dropdown
                    const select = document.getElementById('selected-prompt');
                    select.innerHTML = '<option value="">Select a prompt...</option>';
                    
                    evaluation.prompts.forEach((prompt, idx) => {
                        // Create prompt display
                        const promptDiv = document.createElement('div');
                        promptDiv.className = 'prompt-container';
                        promptDiv.innerHTML = `
                            <div class="prompt-header">
                                <strong>${prompt.model_source}</strong>
                                <span class="score-badge">${prompt.weighted_score.toFixed(2)}/10</span>
                            </div>
                            <p>${prompt.text}</p>
                            <small>Overall Score: ${prompt.overall_score.toFixed(1)} | Weighted: ${prompt.weighted_score.toFixed(2)}</small>
                        `;
                        
                        if (evaluation.winner && prompt.id === evaluation.winner.id) {
                            promptDiv.style.borderColor = '#28a745';
                            promptDiv.style.borderWidth = '2px';
                            const badge = document.createElement('span');
                            badge.style.background = '#28a745';
                            badge.style.color = 'white';
                            badge.style.padding = '4px 8px';
                            badge.style.borderRadius = '4px';
                            badge.style.fontSize = '12px';
                            badge.textContent = 'AI WINNER';
                            promptDiv.querySelector('.prompt-header').appendChild(badge);
                        }
                        
                        container.appendChild(promptDiv);
                        
                        // Add to selection dropdown
                        const option = document.createElement('option');
                        option.value = prompt.id;
                        option.textContent = `${prompt.model_source} (${prompt.weighted_score.toFixed(2)})`;
                        select.appendChild(option);
                    });
                    
                    currentEvaluationIndex = index;
                } else {
                    alert(`Error loading evaluation: ${result.error}`);
                }
            } catch (error) {
                console.error('Error loading evaluation:', error);
                alert('Error loading evaluation');
            }
        }
        
        async function makeDecision() {
            const selectedPromptId = document.getElementById('selected-prompt').value;
            const reasoning = document.getElementById('decision-reasoning').value;
            const modifications = document.getElementById('custom-modifications').value;
            
            if (!selectedPromptId) {
                alert('Please select a prompt first');
                return;
            }
            
            if (!reasoning.trim()) {
                alert('Please provide reasoning for your decision');
                return;
            }
            
            try {
                const response = await fetch('/api/make-decision', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        page_title: document.getElementById('eval-title').textContent,
                        page_category: document.getElementById('eval-category').textContent,
                        asset_type: document.getElementById('eval-type').textContent,
                        selected_prompt_id: selectedPromptId,
                        selected_model: document.getElementById('selected-prompt').selectedOptions[0].textContent.split(' (')[0],
                        reasoning: reasoning,
                        custom_modifications: modifications
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    // Update progress
                    document.getElementById('decisions-count').textContent = result.total_decisions;
                    const progress = (result.total_decisions / totalEvaluations) * 100;
                    document.getElementById('progress-fill').style.width = progress + '%';
                    document.getElementById('progress-text').textContent = progress.toFixed(1) + '% Complete';
                    
                    // Clear form
                    document.getElementById('selected-prompt').value = '';
                    document.getElementById('decision-reasoning').value = '';
                    document.getElementById('custom-modifications').value = '';
                    
                    alert('Decision recorded successfully!');
                } else {
                    alert(`Error recording decision: ${result.error}`);
                }
            } catch (error) {
                console.error('Error making decision:', error);
                alert('Error recording decision');
            }
        }
        
        async function nextEvaluation() {
            if (currentEvaluationIndex < totalEvaluations - 1) {
                await loadEvaluation(currentEvaluationIndex + 1);
            } else {
                alert('No more evaluations to review!');
            }
        }
        
        async function exportDecisions() {
            try {
                const response = await fetch('/api/export-decisions');
                const result = await response.json();
                
                if (result.success) {
                    alert(`Exported ${result.total_decisions} decisions to ${result.file_path}`);
                } else {
                    alert('Error exporting decisions');
                }
            } catch (error) {
                console.error('Error exporting decisions:', error);
                alert('Error exporting decisions');
            }
        }
        
        // Auto-refresh progress every 30 seconds
        setInterval(async () => {
            if (sessionActive) {
                try {
                    const response = await fetch('/api/get-progress');
                    const progress = await response.json();
                    
                    document.getElementById('decisions-count').textContent = progress.decisions_made;
                    const percentage = progress.completion_percentage;
                    document.getElementById('progress-fill').style.width = percentage + '%';
                    document.getElementById('progress-text').textContent = percentage.toFixed(1) + '% Complete';
                } catch (error) {
                    console.error('Error updating progress:', error);
                }
            }
        }, 30000);
    </script>
</body>
</html>
        """
        
        with open(templates_dir / 'dashboard.html', 'w') as f:
            f.write(dashboard_html)
        
        self.logger.info("Created dashboard template")
    
    def run(self, debug: bool = True):
        """Run the dashboard server"""
        self.logger.info(f"Starting Review Dashboard on http://localhost:{self.port}")
        print(f"\n🌐 Estate Planning Concierge v4.0 - Review Dashboard")
        print(f"📊 Open http://localhost:{self.port} to start reviewing prompts")
        print(f"🎯 Use this interface to review AI-generated prompts and make final selections")
        
        self.app.run(host='0.0.0.0', port=self.port, debug=debug)


def create_dashboard_server(port: int = 5000):
    """Create and return a dashboard server instance"""
    try:
        dashboard = ReviewDashboard(port=port)
        return dashboard
    except ImportError as e:
        print(f"Cannot create dashboard: {e}")
        print("Install required dependencies: pip install flask flask-cors")
        return None


async def test_review_dashboard():
    """Test the review dashboard with sample data"""
    print("🎛️ Testing Review Dashboard...")
    
    # Create dashboard (but don't run it in test mode)
    dashboard = create_dashboard_server(port=5001)
    
    if dashboard:
        print(f"✅ Review dashboard created successfully!")
        print(f"📱 Dashboard features:")
        print(f"  - Interactive web interface for prompt review")
        print(f"  - Side-by-side prompt comparison")
        print(f"  - Quality score visualization")
        print(f"  - Human decision recording")
        print(f"  - Progress tracking")
        print(f"  - Export capabilities")
        
        print(f"\n🚀 To run the dashboard:")
        print(f"  dashboard = create_dashboard_server()")
        print(f"  dashboard.run()")
        print(f"  # Then open http://localhost:5000")
        
        return True
    else:
        print("❌ Dashboard creation failed")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Run test
        asyncio.run(test_review_dashboard())
    else:
        # Run dashboard server
        dashboard = create_dashboard_server()
        if dashboard:
            dashboard.run()
        else:
            print("Failed to create dashboard. Check dependencies.")