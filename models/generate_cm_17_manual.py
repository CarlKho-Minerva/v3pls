import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Confusion Matrix from results.md
cm = np.array([[78,  6,  5],
               [ 4, 57, 28],
               [ 0, 12, 78]])

classes = ['CLENCH', 'NOISE', 'RELAX']

output_path = "/Users/carl/Downloads/CODELocalProjects/v2-emg-muscle/arXiv_submission_clean/cm_17_maxcrnn.png"

plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
plt.title('Confusion Matrix: 17_crnn_maxed (No Aug)')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.savefig(output_path)
print(f"Saved {output_path}")
