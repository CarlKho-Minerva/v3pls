#!/usr/bin/env python3
"""
Sync markdown content to existing IPYNB files.
Updates the markdown cells in notebooks to match the current markdown files.
"""

import json
import re
from pathlib import Path

def markdown_to_cells(md_content):
    """
    Split markdown content into cells (markdown and code blocks).
    Returns list of (cell_type, content) tuples.
    """
    cells = []
    parts = re.split(r'```(?:python)?\n', md_content)
    
    for i, part in enumerate(parts):
        if i == 0:
            # First part is always markdown
            if part.strip():
                cells.append(('markdown', part))
        else:
            # Odd indices are code, even are markdown
            if '```' in part:
                code, *rest = part.split('```', 1)
                if code.strip():
                    cells.append(('code', code))
                if rest and rest[0].strip():
                    cells.append(('markdown', rest[0]))
            else:
                # No closing backticks, treat as code
                if part.strip():
                    cells.append(('code', part))
    
    return cells

def update_notebook(md_path, ipynb_path):
    """Update notebook cells with markdown content."""
    print(f"Processing {md_path.name}...")
    
    # Read markdown
    with open(md_path, 'r') as f:
        md_content = f.read()
    
    # Read existing notebook
    with open(ipynb_path, 'r') as f:
        notebook = json.load(f)
    
    # Convert markdown to cells
    new_cells = []
    cell_list = markdown_to_cells(md_content)
    
    for cell_type, content in cell_list:
        if cell_type == 'markdown':
            new_cells.append({
                'cell_type': 'markdown',
                'metadata': {},
                'source': content.split('\n')
            })
        else:
            new_cells.append({
                'cell_type': 'code',
                'execution_count': None,
                'metadata': {},
                'outputs': [],
                'source': content.split('\n')
            })
    
    # Update notebook
    notebook['cells'] = new_cells
    
    # Write back
    with open(ipynb_path, 'w') as f:
        json.dump(notebook, f, indent=1)
    
    print(f"  ✅ Updated {len(new_cells)} cells")

def main():
    assignment_dir = Path('assignment')
    
    # List of sections to update
    sections = [
        'section_1_data_explanation',
        'section_2_data_loading',
        'section_3_feature_engineering',
        'section_4_analysis_splits',
        'section_5_model_selection',
        'section_6_model_training',
        'section_7_performance_metrics',
        'section_8_results_conclusions',
        'section_9_executive_summary',
        'section_10_references',
    ]
    
    for section in sections:
        md_path = assignment_dir / f'{section}.md'
        ipynb_path = assignment_dir / f'{section}.ipynb'
        
        if md_path.exists() and ipynb_path.exists():
            update_notebook(md_path, ipynb_path)
        else:
            print(f"⚠️  Skipping {section} (files not found)")

if __name__ == '__main__':
    main()
    print("\n✅ Notebook sync complete!")
