# Model 17: MaxCRNN Results

## Performance
*   **Accuracy:** 0.7948
*   **Inference Latency:** 0.1468 ms
*   **Architecture:** Inception -> Bi-LSTM -> MultiHeadAttention

## Classification Report
```
              precision    recall  f1-score   support

      CLENCH       0.95      0.88      0.91        89
       NOISE       0.76      0.64      0.70        89
       RELAX       0.70      0.87      0.78        90

    accuracy                           0.79       268
   macro avg       0.80      0.79      0.79       268
weighted avg       0.80      0.79      0.79       268

```

## Confusion Matrix
```
[[78  6  5]
 [ 4 57 28]
 [ 0 12 78]]
```
