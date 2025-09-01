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
        else:
            return strip_yaml_comments(content)
    except:
        return ""

def main():
    output_lines = []
    output_lines.append("ESTATE PLANNING CONCIERGE v4.0 - CODE AUDIT FILE")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    python_files = [
        'asset_generation/openrouter_orchestrator.py',
        'asset_generation/asset_generator.py',
        'asset_generation/sync_yaml_comprehensive.py',
        'asset_generation/prompt_templates.py',
        'asset_generation/emotional_elements.py',
        'asset_generation/visual_hierarchy.py',
        'asset_generation/quality_scorer.py',
        'asset_generation/sample_generator.py',
        'asset_generation/review_dashboard.py',
        'asset_generation/review_server.py',
        'asset_generation/git_operations.py',
        'asset_generation/test_generate_samples.py',
        'asset_generation/run_orchestration_test.py',
        'asset_generation/validate_structured_implementation.py',
    ]
    
    for py_file in python_files:
        if os.path.exists(py_file):
            output_lines.append(f"\n{'='*80}")
            output_lines.append(f"{os.path.basename(py_file)}")
            output_lines.append(f"{'='*80}\n")
            content = process_file(py_file, 'python')
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
    
    with open('estate_planning_v4_code_audit.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"Audit file created: estate_planning_v4_code_audit.txt")
    print(f"Total lines: {len(output_lines)}")

if __name__ == "__main__":
    main()