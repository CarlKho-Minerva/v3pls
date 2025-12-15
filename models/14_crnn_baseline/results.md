# Model 14: CRNN Results

## Performance
*   **Accuracy:** 0.8694
*   **Inference Latency:** 11.6349 ms
*   **Architecture:** Conv1D -> MaxPool -> Conv1D -> MaxPool -> LSTM -> Dense

## Classification Report
```
              precision    recall  f1-score   support

      CLENCH       0.98      0.91      0.94        89
       NOISE       0.82      0.80      0.81        89
       RELAX       0.83      0.90      0.86        90

    accuracy                           0.87       268
   macro avg       0.87      0.87      0.87       268
weighted avg       0.87      0.87      0.87       268

```

## Confusion Matrix
```
[[81  7  1]
 [ 2 71 16]
 [ 0  9 81]]
```

## Analysis
*   **Unexpected Success:** The Baseline model (with BatchNorm) achieved **86.94% accuracy**, outperforming previous short runs.
*   **Safety:** It achieved **98% Precision on CLENCH**, making it very safe for control.
*   **Confusion:** There is still some confusion between `NOISE` and `RELAX` (25 errors total), but significantly less than observed in shorter training runs.
*   **Conclusion:** BatchNorm may not be as harmful as hypothesized if the model is allowed to converge (202 epochs).
