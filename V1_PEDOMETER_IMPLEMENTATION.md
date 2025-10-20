# v1 Pedometer Implementation in Hybrid System

## ✅ What Was Actually Implemented from v1

### 1. **Gravity-Based State Detection**
```python
def determine_state_from_sensors(x, y, z):
    """Determine phone orientation state from gravity"""
    if abs(y) > GRAVITY_THRESHOLD:  # 9.0
        return "COMBAT"  # Phone vertical
    elif abs(x) > GRAVITY_THRESHOLD:
        return "WALKING"  # Phone horizontal
    else:
        return "IDLE"
```

**Purpose**: Detects phone orientation to determine available controls
- Horizontal (X-axis gravity) = Walking mode
- Vertical (Y-axis gravity) = Combat mode
- Neither = Idle/transition

### 2. **State Stability Buffer (Rolling Window)**
```python
def get_stable_state(raw_state, state_buffer):
    """Apply state stability buffer - requires 4/5 consensus"""
    state_buffer.append(raw_state)

    # Requires 4 out of 5 frames to agree before changing state
    walking_count = state_buffer.count("WALKING")
    # ... prevents flickering between states
```

**Purpose**: Prevents rapid state changes from sensor noise
- Uses deque(maxlen=5) for rolling window
- Requires 4/5 consensus to change state
- Provides "sticky" state transitions

### 3. **Dynamic Zero Point (Initial Heading)**
```python
# Set initial heading on first data (v1 dynamic zero point)
if state.initial_gyro_heading is None:
    state.initial_gyro_heading = gyro_y
    print("▶️ Initial heading set (forward direction locked)")

# Later: relative rotation
effective_gyro = gyro_y - state.initial_gyro_heading
```

**Purpose**: Player's starting orientation becomes "forward"
- First gyro reading sets baseline
- All rotation calculated relative to this
- Player doesn't need to face specific direction

### 4. **Gyro Integration for Rotation Tracking**
```python
# Calculate time delta for gyro integration
delta_time = current_time - last_time

# Integrate gyro to get total rotation
effective_gyro = gyro_y - state.initial_gyro_heading
if abs(effective_gyro) > gyro_limit:
    state.total_rotation += effective_gyro * delta_time

# Determine direction
rotation_threshold = 3.14  # ~180 degrees
state.facing_right = state.total_rotation < rotation_threshold
```

**Purpose**: Track cumulative rotation to determine facing direction
- Integrates gyroscope over time
- Filters out noise with threshold
- 180° rotation flips direction

### 5. **Swing Amplitude Detection**
```python
# Check for swing amplitude
swing_threshold = FUEL_WALK_CONFIG["swing_amplitude_threshold"]  # 3.0
currently_walking = abs(z) > swing_threshold
```

**Purpose**: Detects arm swing motion when phone is horizontal
- Z-axis (perpendicular to screen) swings during walking
- Simple threshold-based detection
- Natural pendulum motion

### 6. **Sustained Key Press Management**
```python
def manage_walking_key_press(should_walk, direction_key, state, keyboard):
    """Handle sustained key press for walking (v1 logic)"""
    if should_walk and not state.walking_key_pressed:
        # Start walking - press and hold key
        keyboard.press(direction_key)
        state.walking_key_pressed = True
        return "WALK_KEY_PRESS"
    elif should_walk and state.walking_key_pressed and state.current_walking_key != direction_key:
        # Direction changed - release old key, press new key
        keyboard.release(state.current_walking_key)
        keyboard.press(direction_key)
        return "WALK_DIRECTION_CHANGE"
    elif not should_walk and state.walking_key_pressed:
        # Stop walking - release key
        keyboard.release(state.current_walking_key)
        state.walking_key_pressed = False
        return "WALK_KEY_RELEASE"
```

**Purpose**: Manages keyboard key states for walking
- Press and HOLD arrow key while walking (like game controls)
- Release when stopping
- Seamlessly switches keys when changing direction

### 7. **Fuel System (Continuous Confirmation)**
```python
if current_phone_state == "WALKING" and ENABLE_FUEL_WALK:
    # Check for swing amplitude
    currently_walking = abs(z) > swing_threshold

    # Manage sustained key press
    key_action = manage_walking_key_press(
        currently_walking, direction_key, state, keyboard
    )

    if key_action == "WALK_KEY_RELEASE":
        state.is_walking = False
        print(f"\n⏹️  Walk stopped (fuel depleted)")
```

**Purpose**: Walking requires continuous swing motion
- Stop swinging = fuel depletes = walking stops
- Similar to holding down a button in games
- Natural feel - stop moving arm, character stops

### 8. **State-Aware Control Modes**
```python
if current_phone_state == "WALKING" and ENABLE_FUEL_WALK:
    # Walking controls active
    # Swing detection + direction tracking

elif current_phone_state == "COMBAT":
    # Stop walking if active
    if state.walking_key_pressed:
        keyboard.release(state.current_walking_key)
        state.walking_key_pressed = False
        print(f"\n🛑 Walk stopped (entered COMBAT state)")
```

**Purpose**: Different phone orientations enable different controls
- Horizontal = walking available
- Vertical = combat mode (stops walking)
- Seamless transitions based on how you hold phone

## 🎯 What's Different from Pure v1

### Added: ML Action Classification
v1 used threshold-based detection for ALL actions (punch, jump, etc.)

**Hybrid System**: Uses ML for complex actions
- `jump`, `punch`, `turn_left`, `turn_right` detected by SVM
- More accurate than simple thresholds
- Trainable for individual users

### Added: Parallel Threading
v1 was single-threaded blocking

**Hybrid System**: Uses asyncio for concurrency
```python
await asyncio.gather(
    distributor(),      # UDP receiver
    fuel_walk_monitor(), # v1 pedometer
    action_classifier(), # ML predictions
    actor(),            # Keyboard execution
    dashboard()         # Live display
)
```

### Kept: All v1 Walking Logic
- ✅ Gravity-based state detection
- ✅ State stability buffer
- ✅ Dynamic zero point
- ✅ Gyro integration
- ✅ Swing amplitude detection
- ✅ Sustained key press
- ✅ Fuel system concept

## 📊 Configuration

All v1 thresholds are configurable in `config.json`:

```json
{
  "fuel_walk": {
    "swing_amplitude_threshold": 3.0,      // Z-axis swing to detect walking
    "gyro_noise_limit": 0.5,               // Gyro threshold to filter noise
    "rotation_threshold_radians": 3.14     // ~180° for direction flip
  }
}
```

## 🎮 How It Works in Practice

1. **Hold phone horizontal** (screen facing you)
2. **Swing arm naturally** - Z-axis > 3.0 triggers walking
3. **Rotate body** - Gyro integration tracks cumulative rotation
4. **At ~180°** - Direction flips (left ↔ right)
5. **Stop swinging** - Fuel depletes, walking stops
6. **Tilt to vertical** - Enters combat mode, walking disabled

**While Walking:**
- ML detects jumps/punches from complex motion patterns
- Jump/punch stop walking temporarily
- Turns change direction without stopping

## ✅ Summary

**The hybrid system DOES implement the v1 pedometer**, but with enhancements:

| Feature | v1 | Hybrid |
|---------|----|----|
| Walking detection | ✅ Pedometer | ✅ Same pedometer |
| State machine | ✅ Gravity-based | ✅ Same |
| Rotation tracking | ✅ Gyro integration | ✅ Same |
| Fuel system | ✅ Continuous confirmation | ✅ Same |
| Action detection | ⚠️ Thresholds only | ✅ ML classifier |
| Threading | ❌ Blocking | ✅ Async parallel |
| Training pipeline | ❌ None | ✅ SVM training |

**Result**: Best of both worlds - reliable v1 walking + intelligent ML actions! 🎮✨
