# Assignment Sections - Clean vs. Evaluated Versions

## Overview

This directory contains TWO versions of each section:

### 1. Original Versions (`section_X_name.md`)
These include roundtable evaluations at the beginning, demonstrating how the content was reviewed against CS156 standards. These are **working documents** showing the evaluation process.

### 2. Clean Versions (`section_X_name_clean.md`)  
These contain **only the deliverable content** without roundtables - ready for direct integration into your Jupyter notebook.

## Which Version Should You Use?

**For your assignment submission:** Use the **CLEAN versions** (`*_clean.md`)

**For understanding quality standards:** Reference the **ORIGINAL versions** with roundtables

## Current Status

### Clean Versions Created
- ✅ `section_1_data_explanation_clean.md` - Completed
- ⏳ Sections 2-10 - In progress

### Original Versions (with roundtables)
- ✅ All 10 sections complete
- These remain as reference for evaluation criteria

## Sample Count Corrections Applied

All sections updated to reflect actual dataset:
- **Gesture classes** (jump, punch, turns, noise): 100 samples each
- **Locomotion states** (walk, idle): 71-74 samples each  
- **Total**: 719 samples (not 280)

Changes tracked in `CORRECTIONS.md`

## Figure Generation

Jupyter notebooks created for generating visualizations:
- `notebooks/generate_section3_figures.ipynb` - Feature engineering figures
- `notebooks/generate_section7_figures.ipynb` - Performance metrics

## Integration Workflow

1. **Generate figures** by running Jupyter notebooks
2. **Copy content** from `section_X_name_clean.md` files to notebook markdown cells
3. **Add code blocks** from the sections to code cells
4. **Insert figure references** pointing to generated PNG files
5. **Test LaTeX rendering** in notebook

## File Structure

```
assignment/
├── section_1_data_explanation.md         (Original with roundtable)
├── section_1_data_explanation_clean.md   (Clean deliverable)
├── section_2_data_loading.md             (Original with roundtable)
├── section_2_data_loading_clean.md       (Clean deliverable - TBD)
│   ... and so on for sections 3-10
├── figures/                               (Generated visualizations)
├── CORRECTIONS.md                         (Summary of fixes)
└── README_VERSIONS.md                     (This file)
```

## Tone Adjustments

Clean versions:
- ✅ More humble, less prescriptive
- ✅ Focus on explaining approach
- ✅ Removed "mansplaining" tone
- ✅ First-person narrative maintained

## Next Steps

1. Complete clean versions of sections 2-10
2. Verify all LaTeX renders correctly  
3. Test figure references in notebook environment
4. Final review for tone and accuracy
