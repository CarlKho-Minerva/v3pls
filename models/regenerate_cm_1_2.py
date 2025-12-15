#!/usr/bin/env python3
"""
Regenerate confusion matrix images for Models 1 and 2 based on ground truth data.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Ground truth from results.md files
classes = ['CLENCH', 'NOISE', 'RELAX']

# Model 1: Threshold - from 01_threshold/results.md
cm1 = np.array([
    [ 0, 89,  0],
    [ 0, 89,  0],
    [ 0, 67, 23]
])

# Model 2: Variance - from 02_variance/results.md
cm2 = np.array([
    [ 0, 89,  0],
    [ 0, 89,  0],
    [ 0, 90,  0]
])

def save_cm(cm, model_name, output_path):
    """Generate and save a confusion matrix heatmap."""
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes, yticklabels=classes,
                annot_kws={'size': 14})
    plt.title(f'{model_name}', fontsize=14, fontweight='bold')
    plt.ylabel('True Label', fontsize=12)
    plt.xlabel('Predicted Label', fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

# Generate images
arxiv_dir = "/Users/cvk/Downloads/CODELocalProjects/CP-PHASE3_sEMGMuscle-arXiv_25TPE/arXiv_submission_clean"

save_cm(cm1, "Model 1: Threshold CM", f"{arxiv_dir}/cm_01_threshold.png")
save_cm(cm2, "Model 2: Variance CM", f"{arxiv_dir}/cm_02_variance.png")

print("\nDone! Both confusion matrices regenerated with correct ground truth data.")
