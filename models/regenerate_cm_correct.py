import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# --- SETTINGS TO MATCH "OG" STYLE ---
# This mimics the look of the LogReg plot provided
def plot_og_style_matrix(cm, title, filename):
    plt.figure(figsize=(5, 4))

    # Define labels
    labels = ['CLENCH', 'NOISE', 'RELAX']

    # Create Heatmap (Seaborn style)
    # cmap='Blues' matches the LogReg plot color scheme
    # annot=True puts the numbers in the boxes
    # fmt='d' ensures they are integers
    # cbar=True adds the color bar on the right
    ax = sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                     xticklabels=labels, yticklabels=labels,
                     annot_kws={"size": 12}) # Adjust font size of numbers

    # Style the labels
    plt.title(f'CM: {title}', fontsize=12, fontweight='bold', pad=10)
    plt.ylabel('True', fontsize=12)
    plt.xlabel('Predicted', fontsize=12)

    # Save with tight layout to prevent cutting off labels
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {filename}")

# --- 1. CORRECT DATA FOR MODEL 1 (THRESHOLD) ---
# Retrieved from your original PDF Figure 13
# (Row 1: Clench, Row 2: Noise, Row 3: Relax)
cm_threshold = np.array([
    [59, 0, 30],
    [71, 0, 18],
    [26, 0, 64]
])

# --- 2. CORRECT DATA FOR MODEL 2 (VARIANCE) ---
# Retrieved from your original PDF Figure 15
cm_variance = np.array([
    [59, 0, 30],
    [77, 0, 12],
    [31, 0, 59]
])

# Output directory
arxiv_dir = "/Users/cvk/Downloads/CODELocalProjects/CP-PHASE3_sEMGMuscle-arXiv_25TPE/arXiv_submission_clean"

# --- GENERATE PLOTS ---
plot_og_style_matrix(cm_threshold, "Threshold", f"{arxiv_dir}/cm_01_threshold.png")
plot_og_style_matrix(cm_variance, "Variance", f"{arxiv_dir}/cm_02_variance.png")

print("\nDone! Both CMs regenerated with CORRECT data and OG Seaborn style.")
