# Pareto-Optimal Model Selection for Low-Cost, Single-Lead EMG Control in Embedded Systems

[![arXiv](https://img.shields.io/badge/arXiv-2312.xxxxx-b31b1b.svg)](https://arxiv.org/abs/2312.xxxxx)
> **Note:** arXiv Preprint ID Pending Submission

This repository contains the dataset, source code, and training logs for the paper **"Pareto-Optimal Model Selection for Low-Cost, Single-Lead EMG Control in Embedded Systems"**.

## Abstract

Consumer-grade biosensors offer a cost-effective alternative to medical-grade electromyography (EMG) systems, reducing hardware costs from thousands of dollars to ~$13. However, these low-cost sensors introduce significant signal instability and motion artifacts. Deploying machine learning models on resource-constrained edge devices like the ESP32 presents a challenge: balancing classification accuracy with strict latency (<100ms) and memory (<320KB) constraints.

Using a single-subject dataset comprising **1,540 seconds of raw data (1.54M data points, ~1,300 one-second windows)**, I evaluate **18 model architectures** ranging from statistical heuristics to deep transfer learning (ResNet50) and custom hybrid networks (MaxCRNN). While my custom **MaxCRNN** (Inception + Bi-LSTM + Attention) achieved the highest safety (**99% Precision**) and robustness, I identify **Random Forest (74% accuracy)** as the Pareto-optimal solution for *embedded* control on legacy microcontrollers.

## Project Overview

I investigate the feasibility of using a **~$13 AD8232 Heart Rate Monitor** as an EMG sensor for a hands-free cyclist turn signal. The goal is to detect a specific "Clench" gesture (Flexor Digitorum Profundus) while rejecting noise from biking vibrations.

I benchmark **18 Machine Learning Architectures** across a "Ladder of Abstraction":
1. **Heuristics:** Amplitude Thresholding, Rolling Variance
2. **Classical ML:** Logistic Regression, KNN, SVM, Random Forest, XGBoost
3. **Deep Learning:** MLP, 1D CNN (with/without augmentation)
4. **Transfer Learning:** MobileNetV2, ResNet50 (on Mel-Spectrograms)
5. **Ensembles:** Mega Ensemble (Soft Voting)
6. **Custom Architectures:** CRNN variants, MaxCRNN (Inception + Bi-LSTM + Attention)

## Key Results

| Model | Accuracy | F1 (Clench) | Latency | Deployment |
| :--- | :---: | :---: | :---: | :--- |
| **MaxCRNN (Model 18)** | **83.21%** | **0.99** | 0.15ms* | No (GPU Required) |
| Mega Ensemble | 77.99% | 0.88 | >500ms | No (Latency) |
| 1D CNN (+ Augmentation) | 78.36% | 0.87 | 0.83ms | Yes |
| ResNet50 | 76.12% | 0.87 | >100ms | No (Latency) |
| MobileNetV2 | 75.00% | 0.86 | 9.8ms | No (RAM) |
| **Random Forest** | **74.25%** | **0.81** | **0.01ms** | **Yes (Pareto Optimal)** |
| XGBoost | 73.51% | 0.83 | 0.01ms | Yes |

*MaxCRNN latency measured on NVIDIA A100 GPU; all other latencies measured on ESP32 (240MHz Xtensa LX6).

## Key Contributions

1. A **comprehensive benchmark** of 18 architectures spanning heuristics, classical ML, deep learning, and transfer learning for single-lead EMG classification under hardware constraints.
2. A novel **MaxCRNN architecture** (Inception + Bi-LSTM + Attention) achieving state-of-the-art 99% precision on the safety-critical "CLENCH" class.
3. Empirical demonstration that **Random Forest with statistical features** is Pareto-optimal for ESP32 deployment, outperforming deep learning under the "Small Data" regime.
4. A reproducible **open-source dataset and codebase** for low-cost EMG research.

## Repository Structure

```
.
├── arXiv_submission_clean/    # LaTeX source and figures
│   ├── Kho_2025.tex           # Main paper
│   ├── arxiv.sty              # arXiv style file
│   └── *.png                  # All figures (confusion matrices, visualizations)
├── data/                      # Raw EMG dataset
│   ├── 2025_11_09-Session*/   # 5 recording sessions (~1.54M data points total)
│   ├── utils.py               # Data loading and feature extraction
│   └── requirements.txt
└── models/                    # Training scripts for all 18 architectures
    ├── 01_threshold/          # Heuristic baseline
    ├── 06_random_forest/      # Pareto-optimal for ESP32
    ├── 18_crnn_maxed_data_augmented/  # MaxCRNN (best accuracy)
    └── ...
```

## Getting Started

### Prerequisites
```bash
pip install -r data/requirements.txt
```

### Reproducing Results

Train the Random Forest model (Pareto-optimal for ESP32):
```bash
cd models/06_random_forest
python train.py
```

Train the MaxCRNN model (highest accuracy):
```bash
cd models/18_crnn_maxed_data_augmented
python train.py
```

### Compiling the Paper
```bash
cd arXiv_submission_clean
pdflatex Kho_2025.tex
```

## Citation

If you use this dataset or code, please cite:
```bibtex
@article{kho2025emg,
  title={Pareto-Optimal Model Selection for Low-Cost, Single-Lead EMG Control in Embedded Systems},
  author={Kho, Carl Vincent Ladres},
  journal={arXiv preprint arXiv:2312.xxxxx},
  year={2025}
}
```

## Author

**Carl Vincent Ladres Kho**
Minerva University
kho@uni.minerva.edu