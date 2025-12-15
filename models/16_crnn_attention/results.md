# Model 14: CRNN Results

## Performance
*   **Accuracy:** 0.8060
*   **Inference Latency:** 4.0550 ms
*   **Architecture:** Conv1D -> MaxPool -> Conv1D -> MaxPool -> LSTM -> Dense

## Classification Report
```
              precision    recall  f1-score   support

      CLENCH       0.94      0.84      0.89        89
       NOISE       0.73      0.72      0.72        89
       RELAX       0.77      0.86      0.81        90

    accuracy                           0.81       268
   macro avg       0.81      0.81      0.81       268
weighted avg       0.81      0.81      0.81       268

```

## Confusion Matrix
```
[[75 11  3]
 [ 5 64 20]
 [ 0 13 77]]
```

## Analysis
*   **Recovery:** Adding Attention (and Bi-LSTM) recovered most of the performance lost by removing BatchNorm (80.6% vs 58%), proving the value of the architecture.
*   **Comparison:** However, it did not beat the Baseline model (86.9%) in this longer training run.
*   **Trade-off:** This model converged much faster (81 epochs) than the Baseline (202 epochs), but the Baseline ultimately achieved higher accuracy and precision.
*   **Conclusion:** For the final "Maxed" model, we should probably re-introduce BatchNorm or LayerNorm to get the best of both worlds.
