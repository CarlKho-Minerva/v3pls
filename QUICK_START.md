# Quick Start: Hybrid Fuel Walk System

## ✅ What You Now Have

**v1 Pedometer Walking** + **ML Action Detection** + **Parallel Threading**

- ✅ Walking: Physics-based (swing amplitude + gyro rotation)
- ✅ Actions: ML-based (jump, punch, turns)
- ✅ Architecture: Async parallel processing
- ✅ All v1 features: State machine, fuel system, dynamic zero point

## 🚀 Running the System

### 1. Start the Hybrid Controller

```bash
# Kill any existing listener
lsof -ti:12345 | xargs kill -9 2>/dev/null

# Start hybrid system
.venv/bin/python src/udp_listener_hybrid_fuel.py
```

**Expected Output:**
```
✅ Multiclass models loaded
📡 Listening on 192.168.10.130:12345
🚶 Fuel Walk Monitor started (v1 pedometer)
🎯 Action Classifier started
🎬 Actor started

============================================================
      Hybrid Silksong Controller - FUEL WALK + ML ACTIONS
============================================================
[✗ DISCONNECTED] [0 Hz] | Walk: 🧍 IDLE (→) | Action: - (0%) | State: Idle
```

### 2. Train ML Models (if not done yet)

```bash
# Train the multiclass classifier (actions only, NO walk)
.venv/bin/python notebooks/SVM_Local_Training.py
```

**Classes trained:**
- `jump` - Sharp upward motion
- `punch` - Forward thrust
- `turn_left` - Body rotation left
- `turn_right` - Body rotation right
- `idle` - No significant motion
- `noise` - Random jitter (filtered out)

**NOT trained:** `walk` - handled by v1 pedometer!

### 3. Connect Android App

1. Open Android app
2. Enter your Mac's IP: `192.168.10.130`
3. Tap "Start"

**You should see:**
```
[✓ CONNECTED] [30 Hz] | Walk: 🧍 IDLE (→) | Action: - (0%) | State: Idle
```

## 🎮 Controls

### Walking (v1 Pedometer - No ML)

| Motion | Detection | Result |
|--------|-----------|--------|
| Hold phone horizontal | X-axis gravity > 9.0 | Enables walking |
| Swing arm naturally | Z-axis amplitude > 3.0 | Starts walking |
| Rotate body 180° | Gyro integration | Changes direction |
| Stop swinging | Z-axis < 3.0 | Fuel depletes, stops |
| Tilt to vertical | Y-axis gravity > 9.0 | Enters combat, stops walk |

### Actions (ML Classifier)

| Gesture | ML Class | Effect |
|---------|----------|--------|
| Sharp upward motion | `jump` | Stops walk, jumps |
| Forward punch | `punch` | Stops walk, attacks |
| Body turn left | `turn_left` | Changes walk direction |
| Body turn right | `turn_right` | Changes walk direction |

## 🔧 Configuration

### `config.json`

```json
{
  "network": {
    "listen_ip": "192.168.10.130",  // Auto-detected
    "listen_port": 12345
  },
  "fuel_walk": {
    "swing_amplitude_threshold": 3.0,      // Z-axis swing sensitivity
    "gyro_noise_limit": 0.5,               // Gyro filtering
    "rotation_threshold_radians": 3.14     // 180° for direction flip
  },
  "keyboard_mappings": {
    "left": "Key.left",
    "right": "Key.right",
    "jump": "z",
    "attack": "x"
  }
}
```

### `udp_listener_hybrid_fuel.py` Toggles

```python
# At top of file
ENABLE_FUEL_WALK = True           # v1 pedometer walking
ENABLE_ACTIONS = True             # ML action detection
ENABLE_KEYBOARD_OUTPUT = True     # Actually send keypresses
ML_CONFIDENCE_THRESHOLD = 0.50    # Action detection threshold
```

## 🎯 Key Features from v1

1. **Gravity-Based State Detection**
   - Horizontal = Walking available
   - Vertical = Combat mode
   - Idle = Transition

2. **State Stability Buffer**
   - 5-frame rolling window
   - Requires 4/5 consensus
   - Prevents flicker

3. **Dynamic Zero Point**
   - First gyro reading = "forward"
   - No need to face specific direction
   - Natural adaptation

4. **Fuel System**
   - Walking requires continuous swing
   - Stop swinging = auto-stop
   - Game-like feel

5. **Sustained Key Press**
   - Press and HOLD arrow keys
   - Release when stopping
   - Smooth direction changes

## 🐛 Troubleshooting

### "Address already in use"
```bash
lsof -ti:12345 | xargs kill -9
```

### Walk not starting
- Check phone orientation (hold horizontal)
- Verify Z-axis swing > 3.0 in sensor data
- Try lowering threshold in config.json

### Actions not detecting
- Retrain models: `.venv/bin/python notebooks/SVM_Local_Training.py`
- Lower confidence threshold: `ML_CONFIDENCE_THRESHOLD = 0.40`
- Collect more training data

### Walk won't stop
- Check Z-axis drops below 3.0 when still
- Verify fuel depletion logic in monitor
- Try higher threshold: `swing_amplitude_threshold = 3.5`

## 📊 System Status Display

```
[✓ CONNECTED] [30 Hz] | Walk: 🚶 WALKING (→) | Action: jump (85%) | State: Jump!
 ^            ^         ^                       ^                    ^
 |            |         |                       |                    |
 Watch        Sensor    Walk state              Last ML prediction   Actor state
 connection   rate      (pedometer)             (classifier)         (keyboard)
```

## 🎓 Architecture Diagram

```
UDP Sensor Data (30Hz)
        │
        ├──────────────────┬────────────────────┐
        ▼                  ▼                    ▼
Fuel Walk Monitor    Action Classifier      Dashboard
(v1 Pedometer)       (Multiclass SVM)       (Live Status)
        │                  │
        │                  │
        └────────┬─────────┘
                 ▼
              Actor
           (Keyboard)
```

**All systems run in parallel via asyncio!**

## 📝 Summary

**You now have a game-ready controller that:**
- ✅ Uses proven v1 pedometer for walking (reliable, fast)
- ✅ Uses ML for complex actions (accurate, trainable)
- ✅ Runs both systems in parallel (responsive, no blocking)
- ✅ Maintains all v1 features (state machine, fuel, dynamic zero)

**To play Silksong:**
1. Start controller: `.venv/bin/python src/udp_listener_hybrid_fuel.py`
2. Connect Android app
3. Hold phone horizontal and swing to walk
4. Tilt vertical for combat
5. Jump/punch gestures detected by ML
6. Enjoy! 🎮✨
