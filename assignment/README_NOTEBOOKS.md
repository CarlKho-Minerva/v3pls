# Assignment Notebooks

This directory contains Jupyter notebooks converted from the original markdown sections.

## Individual Section Notebooks

Each of the 10 assignment sections has been converted to an individual Jupyter notebook:

1. **section_1_data_explanation.ipynb** - Data collection methodology and dataset description
2. **section_2_data_loading.ipynb** - Code for loading and processing sensor data
3. **section_3_feature_engineering.ipynb** - Feature extraction from IMU data
4. **section_4_analysis_splits.ipynb** - Train/test split strategy
5. **section_5_model_selection.ipynb** - SVM model selection and kernel choice
6. **section_6_model_training.ipynb** - Model training and hyperparameter tuning
7. **section_7_performance_metrics.ipynb** - Evaluation metrics and confusion matrices
8. **section_8_results_conclusions.ipynb** - Results analysis and conclusions
9. **section_9_executive_summary.ipynb** - Executive summary of the pipeline
10. **section_10_references.ipynb** - Complete bibliography

## Complete Assignment Notebook

**complete_assignment.ipynb** - A merged notebook containing all 10 sections in a cohesive narrative (147 cells total: 83 markdown, 64 code)

## Notebook Structure

Each notebook contains:
- **Markdown cells**: Narrative text, explanations, roundtable discussions, and LaTeX equations
- **Code cells**: Python code blocks for data processing, model training, and visualization

## Usage

To view the notebooks:
```bash
jupyter notebook assignment/
```

To convert a notebook to PDF (for submission):
```bash
jupyter nbconvert --to pdf assignment/complete_assignment.ipynb
```

## Conversion

The notebooks were created from markdown files using a custom conversion script that:
- Preserves markdown formatting and LaTeX equations
- Converts code blocks (```python) to executable code cells
- Maintains the academic narrative structure
- Keeps all technical content intact

## Data and Code Dependencies

Some code cells may require:
- Sensor data files in the `data/` directory
- Python scripts in the `scripts/` and `src/` directories
- Required packages listed in `requirements.txt`

Install dependencies:
```bash
pip install -r requirements.txt
```
