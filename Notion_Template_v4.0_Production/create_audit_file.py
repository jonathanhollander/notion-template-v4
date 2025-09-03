#!/usr/bin/env python3

import os
import re
from pathlib import Path

def strip_python_comments(code):
    code = re.sub(r'"""[\s\S]*?"""', '', code)
    code = re.sub(r"'''[\s\S]*?'''", '', code)
    lines = []
    for line in code.split('\n'):
        if line.strip() and not line.strip().startswith('#'):
            comment_pos = line.find('#')
            if comment_pos > 0:
                line = line[:comment_pos].rstrip()
            if line.strip():
                lines.append(line.rstrip())
    return '\n'.join(lines)

def strip_yaml_comments(code):
    lines = []
    for line in code.split('\n'):
        if line.strip() and not line.strip().startswith('#'):
            comment_pos = line.find('#')
            if comment_pos > 0:
                line = line[:comment_pos].rstrip()
            if line.strip():
                lines.append(line.rstrip())
    return '\n'.join(lines)

def process_file(filepath, file_type='python'):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if file_type == 'python':
            return strip_python_comments(content)
        elif file_type == 'yaml':
            return strip_yaml_comments(content)
        elif file_type == 'text' or file_type == 'html':
            return content  # Don't strip comments from text/HTML files
        else:
            return strip_yaml_comments(content)
    except:
        return ""

def main():
    output_lines = []
    output_lines.append("ESTATE PLANNING CONCIERGE v4.0 - WEB UI GENERATION SYSTEM AUDIT")
    output_lines.append("Complete Web-Based Asset Generation with Background Jobs & Real-Time Monitoring")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    python_files = [
        # CORE: Main Asset Generator (Current Production)
        'asset_generation/asset_generator.py',
        
        # CORE: Sample Generator for Testing
        'asset_generation/sample_generator.py',
        
        # NEW: Web Interface Generation Manager (Background Jobs)
        'asset_generation/generation_manager.py',
        
        # NEW: Human Review Web Dashboard (Flask)
        'asset_generation/review_dashboard.py',
        
        # NEW: Production WSGI Deployment
        'asset_generation/wsgi.py',
        
        # Database Layer - Web-Ready Sync & Async
        'asset_generation/utils/database_manager.py',
        'asset_generation/utils/sync_database_manager.py',
        'asset_generation/utils/session_manager.py',
        'asset_generation/utils/cache_manager.py',
        'asset_generation/utils/progress_tracker.py',
        'asset_generation/utils/smart_retry.py',
        'asset_generation/utils/structured_logger.py',
        
        # Service Layer - Asset Generation & Workflow
        'asset_generation/services/asset_service.py',
        'asset_generation/services/batch_service.py',
        'asset_generation/services/prompt_competition_service.py',
        'asset_generation/services/approval_workflow_service.py',
        
        # AI Quality Scoring System
        'asset_generation/quality_scorer.py',
        
        # Prompt Template System
        'asset_generation/prompt_templates.py',
        
        # Legacy Files (if they exist)
        'asset_generation/asset_generator_v2.py',
        'asset_generation/prompts/__init__.py',
        'asset_generation/test_orchestration.py',
    ]
    
    for py_file in python_files:
        if os.path.exists(py_file):
            output_lines.append(f"\n{'='*80}")
            output_lines.append(f"{os.path.basename(py_file)}")
            output_lines.append(f"{'='*80}\n")
            content = process_file(py_file, 'python')
            if content:
                output_lines.append(content)
    
    # Add configuration files critical for web deployment
    config_files = [
        'asset_generation/requirements.txt',
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            output_lines.append(f"\n{'='*80}")
            output_lines.append(f"{os.path.basename(config_file)} - DEPENDENCIES")
            output_lines.append(f"{'='*80}\n")
            content = process_file(config_file, 'text')
            if content:
                output_lines.append(content)

    # Add HTML template files for web dashboard
    html_files = [
        'asset_generation/templates/dashboard.html',
    ]
    
    for html_file in html_files:
        if os.path.exists(html_file):
            output_lines.append(f"\n{'='*80}")
            output_lines.append(f"{os.path.basename(html_file)} - WEB DASHBOARD TEMPLATE")
            output_lines.append(f"{'='*80}\n")
            content = process_file(html_file, 'html')
            if content:
                output_lines.append(content)
    
    yaml_files = []
    yaml_dir = 'split_yaml'
    if os.path.exists(yaml_dir):
        for yaml_file in sorted(Path(yaml_dir).glob('*.yaml')):
            yaml_files.append(str(yaml_file))
    
    for yaml_file in yaml_files:
        output_lines.append(f"\n{'='*80}")
        output_lines.append(f"{os.path.basename(yaml_file)}")
        output_lines.append(f"{'='*80}\n")
        content = process_file(yaml_file, 'yaml')
        if content:
            output_lines.append(content)
    
    master_prompt = 'asset_generation/meta_prompts/master_prompt.txt'
    if os.path.exists(master_prompt):
        output_lines.append(f"\n{'='*80}")
        output_lines.append(f"master_prompt.txt")
        output_lines.append(f"{'='*80}\n")
        content = process_file(master_prompt, 'text')
        if content:
            output_lines.append(content)
    
    output_filename = 'estate_planning_v4_web_ui_generation_audit.txt'
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"Web UI Generation System Audit file created: {output_filename}")
    print(f"Total lines: {len(output_lines)}")
    print(f"Includes: Complete Web-Based Generation + Background Jobs + Flask Dashboard + Real-Time Monitoring")
    
    # Calculate file size
    file_size = os.path.getsize(output_filename)
    print(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    # Count Python files included
    python_count = sum(1 for f in [
        'asset_generation/asset_generator_v2.py',
        'asset_generation/utils/database_manager.py',
        'asset_generation/services/prompt_competition_service.py',
        'asset_generation/services/approval_workflow_service.py',
        'asset_generation/quality_scorer.py',
        'asset_generation/review_dashboard.py'
    ] if os.path.exists(f))
    
    print(f"Python files included: {python_count}")
    print(f"Key components: Flask Web Server + Background Job Manager + Real-Time Progress + Database Integration + WSGI Production Deployment")

if __name__ == "__main__":
    main()