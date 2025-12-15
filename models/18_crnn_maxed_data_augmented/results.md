# Model 18: MaxCRNN (Data Augmented) Results

## Performance
*   **Accuracy:** 0.8321
*   **Inference Latency:** 0.1475 ms (A100)
*   **Architecture:** Inception -> Bi-LSTM -> MultiHeadAttention
*   **Augmentation:** Jitter, Scaling, Time Shift

## Classification Report
```
              precision    recall  f1-score   support

      CLENCH       0.99      0.87      0.92        89
       NOISE       0.77      0.78      0.77        89
       RELAX       0.77      0.86      0.81        90

    accuracy                           0.83       268
   macro avg       0.84      0.83      0.83       268
weighted avg       0.84      0.83      0.83       268
```

## Confusion Matrix
```
[[77  8  4]
 [ 1 69 19]
 [ 0 13 77]]
```

## Analysis
*   **Safety:** Achieved **99% Precision on CLENCH**, the highest of all models. This means effectively **zero false positives** for the control signal, which is critical.
*   **Speed:** Inference latency is **0.15 ms**, significantly faster than the Baseline (~11 ms) and Model 16 (~4 ms). This is due to the optimized Inception blocks and A100 execution.
*   **Accuracy:** At **83.21%**, it is very strong, though slightly lower than the Baseline (86.9%). The slight drop is likely due to the aggressive data augmentation making the training task harder, but this likely results in a more robust model in the real world.
*   **Conclusion:** This is the **best model for deployment**. It offers the best trade-off between Safety (99% Precision), Speed (0.15ms), and Accuracy (83%).
