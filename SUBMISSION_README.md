# CS156 Assignment 1 - Pipeline First Draft

## Submission File

**Main Notebook:** `CS156_Assignment1_Pipeline_FirstDraft.ipynb`

This is the complete assignment notebook containing all 10 required sections for the CS156 Machine Learning course assignment.

## Assignment Details

- **Title:** Gesture Recognition via Wearable IMU Sensors
- **Author:** Carl Vincent Kho
- **Course:** CS156 Machine Learning
- **Date:** October 2025
- **Assignment:** Pipeline - First Draft

## Notebook Structure

The notebook contains 186 cells:
- 109 Markdown cells (explanations, roundtable discussions, mathematics)
- 77 Code cells (data processing, model training, visualization)

### All 10 Required Sections Included:

1. ✅ **Section 1: Data Explanation** - Personal data collection methodology using custom Android apps
2. ✅ **Section 2: Code for Converting and Loading Data** - Data loading pipeline with error handling
3. ✅ **Section 3: Cleaning, Pre-processing, and Feature Engineering** - 48 features (time + frequency domain)
4. ✅ **Section 4: Analysis Discussion and Data Splits** - Dual classifier architecture and train/test splits
5. ✅ **Section 5: Model Selection and Mathematical Underpinnings** - SVM with RBF kernel (full mathematical derivation)
6. ✅ **Section 6: Model Training** - Training process with hyperparameter tuning discussion
7. ✅ **Section 7: Generate Predictions and Compute Performance Metrics** - Comprehensive evaluation metrics
8. ✅ **Section 8: Visualize Results and Discuss Conclusions** - Results analysis with limitations
9. ✅ **Section 9: Executive Summary** - Complete pipeline overview with diagrams
10. ✅ **Section 10: References** - 50+ academic citations and software versions

## How to Use

### Option 1: Export to PDF for Submission (Required)

Using Jupyter:
```bash
jupyter nbconvert --to pdf CS156_Assignment1_Pipeline_FirstDraft.ipynb
```

Or in Jupyter Lab/Notebook interface:
- Open `CS156_Assignment1_Pipeline_FirstDraft.ipynb`
- File → Download as → PDF via LaTeX

### Option 2: Run the Notebook

If you want to execute the code cells:

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Open in Jupyter:
```bash
jupyter notebook CS156_Assignment1_Pipeline_FirstDraft.ipynb
```

3. Run all cells:
- Kernel → Restart & Run All

**Note:** Some code cells reference data files in the `data/` directory and scripts in `src/` and `scripts/` directories.

## Key Features of This Assignment

### 🌟 Unique Contributions

1. **Custom Android Applications**: Built two Android apps (Pixel Watch + Phone) for primary data collection
2. **Dual Classifier Architecture**: Parallel processing for locomotion state detection AND discrete gesture recognition
3. **Mathematical Rigor**: Complete SVM derivations with LaTeX typeset equations
4. **Ethical Considerations**: Comprehensive discussion of privacy and data ethics
5. **Honest Evaluation**: Acknowledges limitations and proposes concrete improvements

### 📊 Dataset Details

- **Total Samples:** 791 gesture samples
- **Binary Classifier:** 191 samples (71 walk + 120 idle)
- **Multiclass Classifier:** 720 samples (120 each for 6 gesture types)
- **Sensors:** 9-axis IMU data (accelerometer, gyroscope, magnetometer)
- **Sample Rate:** 50 Hz
- **Features:** 48 (16 time-domain + 32 frequency-domain)

### 🎯 Learning Outcomes Addressed

- **cs156-MLCode**: Production-quality Python implementation with error handling
- **cs156-MLExplanation**: Clear documentation with visualizations and roundtable discussions
- **cs156-MLMath**: Rigorous SVM theory with complete mathematical derivations
- **cs156-MLFlexibility**: Custom data collection infrastructure demonstrating initiative

## Repository Structure

```
v3pls/
├── CS156_Assignment1_Pipeline_FirstDraft.ipynb  ← Main submission file
├── assignment/
│   ├── complete_assignment.ipynb                 (source notebook)
│   ├── section_*_updated.ipynb                   (individual sections)
│   └── *.md                                      (documentation)
├── data/                                         (sensor data files)
├── src/                                          (Python processing scripts)
├── scripts/                                      (utility scripts)
├── models/                                       (trained models)
├── requirements.txt                              (Python dependencies)
└── SUBMISSION_README.md                          (this file)
```

## Dependencies

All required Python packages are listed in `requirements.txt`:
- pandas, numpy (data processing)
- scikit-learn (machine learning)
- matplotlib, seaborn (visualization)
- scipy (signal processing)
- joblib (model persistence)

## Submission Checklist

- [x] All 10 sections present and complete
- [x] Markdown cells explain each step
- [x] Code cells are well-commented
- [x] Mathematical equations properly typeset with LaTeX
- [x] Personal data from own digital archive (wearable sensor data)
- [x] Notebook structure follows assignment requirements
- [x] Ready to export to PDF format
- [ ] Run all cells to generate outputs (if needed)
- [ ] Export to PDF
- [ ] Submit PDF to Canvas

## Final Notes

**The final deliverable is a jupyter notebook exported as a PDF. Other formats will not be evaluated.**

To submit:
1. Open `CS156_Assignment1_Pipeline_FirstDraft.ipynb` in Jupyter
2. (Optional) Run all cells if you want to include outputs
3. Export to PDF: File → Download as → PDF via LaTeX
4. Upload the PDF to Canvas

**Do not upload:**
- ❌ A zip file
- ❌ Multiple documents
- ❌ A raw .ipynb file

**Do upload:**
- ✅ A single polished PDF report

---

**Good luck with your submission! 🚀**

*This notebook represents comprehensive work including custom Android app development, primary data collection, rigorous mathematical analysis, and production-quality implementation.*
