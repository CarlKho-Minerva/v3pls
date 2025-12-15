# Model 14: CRNN Results

## Performance
*   **Accuracy:** 0.5821
*   **Inference Latency:** 3.3218 ms
*   **Architecture:** Conv1D -> MaxPool -> Conv1D -> MaxPool -> LSTM -> Dense

## Classification Report
```
              precision    recall  f1-score   support

      CLENCH       0.53      0.74      0.62        89
       NOISE       0.52      0.44      0.48        89
       RELAX       0.74      0.57      0.64        90

    accuracy                           0.58       268
   macro avg       0.60      0.58      0.58       268
weighted avg       0.60      0.58      0.58       268

```

## Confusion Matrix
```
[[66 18  5]
 [37 39 13]
 [21 18 51]]
```

## Analysis
*   **Regression:** Removing BatchNorm caused a severe drop in accuracy to **58.21%**.
*   **Instability:** The model struggled to converge and triggered early stopping with poor results.
*   **Conclusion:** While the hypothesis was that BatchNorm removes amplitude info, it appears that BatchNorm is essential for stabilizing training on this dataset. Removing it without adding other mechanisms (like Attention) leads to failure.
