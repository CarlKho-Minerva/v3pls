# Assignment Corrections and Updates

## Summary of Changes

Based on feedback, I've made the following corrections:

### 1. Sample Count Corrections

**Actual dataset (verified via count_samples.py):**

**Binary Classification:**
- Walk: 71 samples
- Idle: 74 samples

**Multiclass Classification:**
- Jump: 100 samples
- Punch: 100 samples
- Turn Left: 100 samples
- Turn Right: 100 samples
- Idle: 74 samples  
- Noise: 100 samples

**Total: 719 samples** (not 280 as originally stated)

### 2. Roundtable Discussions

The roundtable evaluations have been removed from the final section documents. They were used internally to ensure quality but are not part of the deliverable content.

### 3. Figure Generation Notebooks Created

Two Jupyter notebooks have been added to generate required figures:

- `notebooks/generate_section3_figures.ipynb` - Feature engineering visualizations
- `notebooks/generate_section7_figures.ipynb` - Performance metrics visualizations

### 4. Tone Adjustments

The writing has been revised to be more humble and less prescriptive, focusing on explaining the approach rather than telling the reader what to do.

### 5. LaTeX Rendering

All mathematical notation uses proper LaTeX formatting that will render correctly in Jupyter notebooks:

- Feature formulas: $\mu = \frac{1}{n}\sum_{i=1}^{n} x_i$
- SVM equations: $\min_{\mathbf{w}, b} \frac{1}{2}\|\mathbf{w}\|^2 + C\sum_{i=1}^{n}\xi_i$
- RBF kernel: $K(\mathbf{x}_i, \mathbf{x}_j) = \exp(-\gamma\|\mathbf{x}_i - \mathbf{x}_j\|^2)$

## Files Added

- `scripts/count_samples.py` - Helper script to verify sample counts
- `notebooks/generate_section3_figures.ipynb` - Figure generation for feature engineering
- `notebooks/generate_section7_figures.ipynb` - Figure generation for metrics
- `data/sample_counts.json` - Programmatic access to actual sample counts

## Next Steps

To integrate these sections into your assignment:

1. **Run figure generation notebooks** to create visualizations
2. **Update section markdown files** with actual sample counts (see corrections below)
3. **Copy content to Jupyter notebook** markdown cells
4. **Test LaTeX rendering** in notebook environment

## Key Corrections Needed in Existing Sections

### Section 1 (Lines 92-100)
**Current:**
```markdown
- Walk: 40 samples @ ~5-10 seconds each
- Idle: 40 samples @ ~5-10 seconds each
- Punch: 40 samples @ ~1-2 seconds each
```

**Should be:**
```markdown
- Walk: 71 samples @ ~5-10 seconds each
- Idle: 74 samples @ ~5-10 seconds each
- Punch: 100 samples @ ~1-2 seconds each
- Jump: 100 samples @ ~1-2 seconds each
- Turn Left: 100 samples @ ~0.5-1 seconds each
- Turn Right: 100 samples @ ~0.5-1 seconds each
- Noise: 100 samples
```

### Section 4 (Train/Test Split)
**Current:** References 40 samples per class
**Should be:** 100 samples per gesture class, ~72 for walk/idle

### Section 9 (Executive Summary)
**Current:** States "280 labeled samples"
**Should be:** "719 labeled samples"

## Helper Script Usage

```bash
# Count actual samples in dataset
python scripts/count_samples.py

# Output shows:
# Binary: walk (71), idle (74)
# Multiclass: jump, punch, turn_left, turn_right, noise (100 each), idle (74)
```
