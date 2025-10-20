# Fuel Walk System - Multiclass Classifier Implementation

## Overview

The **Fuel Walk System** replaces the previous dual-classifier approach (binary + multiclass) with a unified **single multiclass classifier** that handles all gestures including walk detection. This system is inspired by game mechanics where walking requires continuous "fuel" (confirmation) to maintain momentum.

## What Changed?

### Before: Dual Classifier System
- **Binary Classifier**: Dedicated to walk vs idle detection (250ms window)
- **Multiclass Classifier**: Handled all actions (jump, punch, turns, idle, noise) (75ms window)
- Two separate models, two separate training pipelines
- Walk detection was independent from action detection

### After: Fuel Walk System
- **Single Multiclass Classifier**: Handles ALL gestures including walk, idle, jump, punch, turns, and noise
- Same model used by both locomotion and action predictors (different window sizes)
- Walk detection competes with all other actions in the same prediction space
- Walk requires continuous confirmation to maintain (fuel system)

## How It Works

### 1. Unified Prediction Model

```python
# All gestures handled by ONE classifier
MULTI_CLASSES = ["walk", "jump", "punch", "turn_left", "turn_right", "idle", "noise"]

# Both predictors use the same model
locomotion_predictor: window=250ms, looks for "walk"/"idle" only
action_predictor: window=75ms, looks for "jump"/"punch"/"turn_*"
```

### 2. Fuel Walk Mechanism

The walk state requires continuous confirmation, similar to holding down a button in a game:

```python
WALK_TIMEOUT = 0.8  # seconds

# Walking continues ONLY if:
# 1. Multiclass predictor outputs "walk" with high confidence
# 2. Walk confirmation arrives within 0.8 seconds
# 3. No action gesture interrupts (jump/punch stops walking)

# Walking auto-stops if:
# - No walk confirmation for 0.8 seconds (fuel depleted)
# - "idle" prediction arrives (intentional stop)
# - "jump" or "punch" action detected (actions interrupt walk)
```

### 3. Parallel Threading for Actions While Walking

The system uses **asyncio** for concurrent gesture processing:

```python
async def actor(locomotion_queue, action_queue, state):
    """
    Processes both queues in parallel:
    1. Action queue checked FIRST (higher priority)
    2. Locomotion queue checked SECOND
    3. Walk timeout monitored continuously
    
    This allows actions to interrupt walking instantly while
    walk state is maintained with fuel confirmation system.
    """
    while True:
        # Process actions first (can stop walking and change direction)
        facing_direction, is_walking = await handle_action(...)
        
        # Then process locomotion (based on new state)
        is_walking, facing_direction, walk_confirmed = await handle_locomotion(...)
        
        # Monitor fuel timeout
        if is_walking and (now - last_walk_confirmation) > WALK_TIMEOUT:
            is_walking = False  # Fuel depleted, stop walking
```

### 4. Action Priority System

Actions are processed with different priorities:

| Gesture | Priority | Behavior | Affects Walking? |
|---------|----------|----------|------------------|
| `turn_left/right` | HIGH | Instant direction change | Changes walk direction if walking |
| `jump` | HIGH | Instant action | **STOPS walking** |
| `punch` | HIGH | Instant action | **STOPS walking** |
| `walk` | MEDIUM | Requires consensus (2 predictions) | Starts/confirms walking |
| `idle` | MEDIUM | Requires consensus (2 predictions) | Stops walking |
| `noise` | LOW | Filtered out | No effect |

## Benefits of Fuel Walk System

### 1. **Gameplay Readiness**
- Walk behaves like game mechanics (hold to move, release to stop)
- Actions interrupt walking naturally (can't attack while walking)
- Turns work while walking (change direction smoothly)

### 2. **Simplified Training**
- Only ONE model to train (multiclass)
- Walk data integrated with other actions
- Better handles ambiguous movements

### 3. **Better Competition Between Gestures**
- Walk competes with actions in same prediction space
- Reduces false positives (walk won't trigger during punch)
- More natural gesture transitions

### 4. **Robust Parallel Processing**
- Actions process immediately (no wait for consensus)
- Walk requires stability (consensus + fuel)
- Both systems run concurrently without blocking

## Code Changes Summary

### `notebooks/SVM_Local_Training.py`
```python
# BEFORE: Train both binary and multiclass
train_binary_classifier(walk, idle)
train_multiclass_classifier(jump, punch, turns, idle, noise)

# AFTER: Train only multiclass with walk included
train_multiclass_classifier(walk, jump, punch, turns, idle, noise)
```

### `src/udp_listener_dashboard asyncio.py`
```python
# BEFORE: Load both models
models_binary = joblib.load("gesture_classifier_binary.pkl")
models_multiclass = joblib.load("gesture_classifier_multiclass.pkl")

# AFTER: Load only multiclass
models_multiclass = joblib.load("gesture_classifier_multiclass.pkl")

# Both predictors use same model (different windows)
locomotion_predictor(model=models_multiclass, window=250ms)
action_predictor(model=models_multiclass, window=75ms)
```

## Testing the System

### Prerequisites
1. Train the multiclass classifier with walk data:
```bash
python notebooks/SVM_Local_Training.py
```

2. Ensure these files exist:
- `models/gesture_classifier_multiclass.pkl`
- `models/feature_scaler_multiclass.pkl`
- `models/feature_names_multiclass.pkl`

### Running the Controller
```bash
cd src
python "udp_listener_dashboard asyncio.py"
```

### Expected Behavior

#### Walking
- Start walking gesture → Character starts walking
- Continue walking → Character keeps walking (fuel maintained)
- Stop walking motion → Character stops after 0.8s (fuel depleted)
- Switch to idle → Character stops immediately

#### Actions While Walking
- Jump while walking → Walk STOPS, character jumps
- Punch while walking → Walk STOPS, character punches
- Turn left while walking → Walk CONTINUES in new direction
- Turn right while walking → Walk CONTINUES in new direction

## Debugging

### Enable/Disable Systems
```python
# In udp_listener_dashboard asyncio.py
ENABLE_LOCOMOTION = True   # Fuel walk system
ENABLE_ACTIONS = True      # Jump, Punch, Turns
ENABLE_KEYBOARD_OUTPUT = True  # Actually send keypresses
```

### Dashboard Shows
- **Locomotion**: Current walk/idle prediction with confidence
- **Action**: Current action prediction with confidence
- **Actor State**: Current character state (Walking right, Idle, Jump!, etc.)
- **Queue Status**: Number of predictions waiting to be processed

### Common Issues

**Problem**: Walk doesn't start
- Check: Is "walk" confidence > 0.50?
- Check: Are you getting 2 consecutive "walk" predictions?
- Check: Is ENABLE_LOCOMOTION = True?

**Problem**: Walk never stops
- Check: Is fuel timeout working? (should be 0.8s)
- Check: Are "idle" predictions being generated?
- Check: Is walk confirmation arriving too frequently?

**Problem**: Actions don't interrupt walking
- Check: Are actions being processed BEFORE locomotion in actor loop?
- Check: Is handle_action() setting is_walking = False?
- Check: Are action confidences > 0.50?

## Future Enhancements

1. **Variable Fuel Timeout**: Adjust based on gesture confidence
2. **Walk Speed**: Use confidence to modulate walking speed
3. **Stamina System**: Limit continuous walking duration
4. **Sprint Detection**: High-intensity walk = sprint mode
5. **Walk Momentum**: Gradual acceleration/deceleration

## Technical Notes

### Why Different Window Sizes?
- **Locomotion (250ms)**: Walk requires stability, longer window smooths predictions
- **Action (75ms)**: Actions need responsiveness, shorter window detects quick motions

### Why Consensus for Walk but not Actions?
- **Walk**: Sustained state, needs stability to prevent jitter
- **Actions**: Instant events, need immediate response

### Async/Threading Model
```
┌─────────────────────────────────────────────────────┐
│              Main Async Loop                         │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Distributor  │  │ Predictor x2 │  │  Actor    │ │
│  │ (UDP recv)   │→ │ (ML inference)│→ │ (keyboard)│ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│         ↓                  ↓                ↓        │
│    sensor_queue       result_queue     is_walking   │
│                                                      │
│  All run concurrently via asyncio.gather()          │
└─────────────────────────────────────────────────────┘
```

## References

- Original dual classifier system: `v3pls` commit history
- Asyncio patterns: `udp_listener_dashboard asyncio.py`
- Training pipeline: `notebooks/SVM_Local_Training.py`
- Gesture classes: `src/organize_training_data.py`
