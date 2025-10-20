#!/usr/bin/env python3
"""Helper script to count samples per class in training data."""

from pathlib import Path
import json

def count_samples(data_dir):
    """Count CSV files per class in organized training data."""
    results = {}
    
    # Binary classification
    binary_dir = Path(data_dir) / "binary_classification"
    if binary_dir.exists():
        results["binary"] = {}
        for class_dir in binary_dir.iterdir():
            if class_dir.is_dir():
                count = len(list(class_dir.glob("*.csv")))
                results["binary"][class_dir.name] = count
    
    # Multiclass classification
    multi_dir = Path(data_dir) / "multiclass_classification"
    if multi_dir.exists():
        results["multiclass"] = {}
        for class_dir in multi_dir.iterdir():
            if class_dir.is_dir():
                count = len(list(class_dir.glob("*.csv")))
                results["multiclass"][class_dir.name] = count
    
    return results

if __name__ == "__main__":
    data_dir = Path(__file__).parent.parent / "data" / "organized_training"
    counts = count_samples(data_dir)
    
    print("Sample Counts:")
    print("="*50)
    print("\nBinary Classification:")
    for cls, count in sorted(counts.get("binary", {}).items()):
        print(f"  {cls}: {count} samples")
    
    print("\nMulticlass Classification:")
    for cls, count in sorted(counts.get("multiclass", {}).items()):
        print(f"  {cls}: {count} samples")
    
    print("\n" + "="*50)
    total = sum(counts.get("binary", {}).values()) + sum(counts.get("multiclass", {}).values())
    print(f"Total samples: {total}")
    
    # Save to JSON for programmatic use
    output_file = Path(__file__).parent.parent / "data" / "sample_counts.json"
    with open(output_file, 'w') as f:
        json.dump(counts, f, indent=2)
    print(f"\nSaved counts to: {output_file}")
