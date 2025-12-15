# Model 9b: 1D CNN with Data Augmentation

## Experiment Purpose
This experiment addresses the reviewer critique: *"Did the CNN fail because of small data,
or because you didn't augment the data like you did for the complex model?"*

## Training Configuration
- **Epochs:** 1000 (with Early Stopping, patience=50)
- **Data Augmentation:** Yes (Jitter, Scaling, Time Shift)
- **Batch Size:** 32
- **Learning Rate:** 0.001
- **Added:** BatchNormalization layers for training stability

## Results
| Metric | Original CNN (Model 9) | CNN + Augmentation |
|--------|------------------------|-------------------|
| Accuracy | 49.63% | 78.36% |
| Epochs | 30 | 128 (early stop; best @ 78) |
| Augmentation | No | Yes |

## Performance
*   **Accuracy:** 0.7836
*   **Inference Latency:** 0.8335 ms

## Classification Report
```
              precision    recall  f1-score   support

      CLENCH       0.96      0.80      0.87        89
       NOISE       0.64      0.81      0.72        89
       RELAX       0.82      0.74      0.78        90

    accuracy                           0.78       268
   macro avg       0.81      0.78      0.79       268
weighted avg       0.81      0.78      0.79       268

```

## Confusion Matrix
```
[[71 17  1]
 [ 3 72 14]
 [ 0 23 67]]
```

## Conclusion
**Improvement:** Data Augmentation + longer training improved CNN performance.
