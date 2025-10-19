#!/usr/bin/env python3
"""Update all section files with correct sample counts."""

from pathlib import Path
import re

def update_section_file(file_path, replacements):
    """Update a section file with correct sample counts."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    assignment_dir = Path(__file__).parent.parent / "assignment"
    
    # Common replacements across all sections
    replacements = [
        # Sample counts
        ("40 samples per class", "~72-100 samples per class"),
        ("40 samples per gesture", "100 samples per gesture"),
        ("280 labeled samples", "719 labeled samples"),
        ("280 samples", "719 samples"),
        
        # Specific class counts
        ("Walk: 40 samples", "Walk: 71 samples"),
        ("Idle: 40 samples", "Idle: 74 samples"),
        ("Punch: 40 samples", "Punch: 100 samples"),
        ("Jump: 40 samples", "Jump: 100 samples"),
        ("Turn Left: 40 samples", "Turn Left: 100 samples"),
        ("Turn Right: 40 samples", "Turn Right: 100 samples"),
        ("Noise (locomotion): 30 samples", "Noise: 100 samples"),
        ("Noise (action): 30 samples", ""),
        
        # Dataset size references
        ("With 40 samples per class", "With ~72-100 samples per class"),
        ("40 training samples per class", "~70-100 training samples per class"),
    ]
    
    section_files = list(assignment_dir.glob("section_*.md"))
    updated = []
    
    for section_file in sorted(section_files):
        if update_section_file(section_file, replacements):
            updated.append(section_file.name)
            print(f"✓ Updated: {section_file.name}")
        else:
            print(f"  No changes: {section_file.name}")
    
    if updated:
        print(f"\nUpdated {len(updated)} section files")
    else:
        print("\nNo files needed updating")

if __name__ == "__main__":
    main()
