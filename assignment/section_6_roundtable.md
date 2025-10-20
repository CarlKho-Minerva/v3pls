# Section 6 Roundtable: Model Training

**Moderator:** "Training implementation - does the code do what it claims?"

**ML Engineer:** "I'm checking: proper use of sklearn API, hyperparameters, training procedure."

**Reproducibility Advocate:** "Can someone else run this and get the same results?"

**Prof. Watson:** "And are the choices justified and documented?"

---

## Expert Opinions

**ML Engineer:**
- ✓ Correct SVC initialization
- ✓ Appropriate kernel and hyperparameters
- ✓ Training on scaled features
- ✓ Separate models for binary and multiclass

**Reproducibility Advocate:**
- ✓ Random seeds for reproducibility
- ✓ Clear documentation of training procedure
- ⚠ Could add model serialization (joblib save)

**Prof. Watson's Verdict:**
"Solid implementation. The code is clean and well-documented."

**Score Projection:** 3-4/5 on cs156-MLCode
