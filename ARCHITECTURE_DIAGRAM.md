# Fuel Walk System Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PIXEL WATCH (Left Wrist)                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Sensors @ 50Hz                                                     │ │
│  │  • Linear Acceleration (x, y, z)                                    │ │
│  │  • Gyroscope (x, y, z)                                              │ │
│  └────────────────────┬───────────────────────────────────────────────┘ │
└─────────────────────────┼───────────────────────────────────────────────┘
                          │ UDP Port 12345
                          ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                     MACBOOK (Python ML Controller)                       │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                      ASYNCIO EVENT LOOP                              ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────┐ ││
│  │  │ Distributor  │  │ Predictor x2 │  │   Actor     │  │Dashboard │ ││
│  │  │ (UDP recv)   │→ │ (ML predict) │→ │ (keyboard)  │  │(display) │ ││
│  │  └──────────────┘  └──────────────┘  └─────────────┘  └──────────┘ ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────────────────┘
                          │ Keyboard Output
                          ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                     SILKSONG GAME (Hollow Knight)                        │
│  • Arrow Keys: Walk left/right                                           │
│  • Z Key: Jump                                                            │
│  • X Key: Attack/Punch                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Detail

```
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 1: SENSOR INPUT                                                      │
│                                                                           │
│  Watch Sensors (50Hz)                                                     │
│     │                                                                     │
│     ├─ Linear Acceleration: {"x": 0.5, "y": -2.3, "z": 0.1}             │
│     └─ Gyroscope: {"x": 0.02, "y": 0.01, "z": -0.05}                    │
│         │                                                                 │
│         └─ UDP Packet → JSON → MacBook                                   │
└───────────────────────────────┬───────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 2: DISTRIBUTOR (async coroutine)                                    │
│                                                                           │
│  Combines: accel + gyro → combined_reading                               │
│     {                                                                     │
│       "accel_x": 0.5, "accel_y": -2.3, "accel_z": 0.1,                  │
│       "gyro_x": 0.02, "gyro_y": 0.01, "gyro_z": -0.05                   │
│     }                                                                     │
│                                                                           │
│  Sends to BOTH queues:                                                   │
│     ├─ sensor_loco_queue.put(reading)   [Queue size: 500]               │
│     └─ sensor_action_queue.put(reading) [Queue size: 200]               │
└─────────────────┬──────────────────────────┬──────────────────────────────┘
                  ↓                          ↓
┌─────────────────────────────┐  ┌───────────────────────────────────────┐
│ STEP 3A: LOCOMOTION PREDICTOR│  │ STEP 3B: ACTION PREDICTOR            │
│                               │  │                                       │
│  Buffer: 250 readings (250ms)│  │  Buffer: 75 readings (75ms)          │
│  Model: multiclass SVM       │  │  Model: multiclass SVM (same!)       │
│  Classes: ALL 7 gestures     │  │  Classes: ALL 7 gestures             │
│                               │  │                                       │
│  Process:                    │  │  Process:                             │
│  1. Extract features (48D)   │  │  1. Extract features (48D)            │
│  2. Scale features           │  │  2. Scale features                    │
│  3. SVM predict_proba()      │  │  3. SVM predict_proba()               │
│  4. Get: walk=0.85           │  │  4. Get: jump=0.92                    │
│                               │  │                                       │
│  Filter:                     │  │  Filter:                              │
│  • Keep: walk, idle          │  │  • Keep: jump, punch, turn_*          │
│  • Drop: jump, punch, turn_* │  │  • Drop: walk, idle, noise            │
│                               │  │                                       │
│  Consensus: Require 2 match  │  │  Consensus: NONE (instant)            │
│                               │  │                                       │
│  Output:                     │  │  Output:                              │
│  └─ result_loco_queue.put()  │  │  └─ result_action_queue.put()        │
│     ("walk", 0.85)            │  │     ("jump", 0.92)                   │
└──────────┬────────────────────┘  └─────────────┬─────────────────────────┘
           │                                     │
           │  [Queue: 10]                        │  [Queue: 10]
           └──────────────┬──────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 4: ACTOR (async coroutine)                                          │
│                                                                           │
│  State Variables:                                                        │
│    • is_walking: bool                                                    │
│    • facing_direction: "left" or "right"                                 │
│    • last_walk_confirmation: timestamp                                   │
│    • pressed_keys: set of currently held keys                            │
│                                                                           │
│  Processing Order (IMPORTANT):                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 1. ACTIONS FIRST (handle_action)                                    │ │
│  │    • Get latest from action_queue                                   │ │
│  │    • Priority: Can interrupt walking                                │ │
│  │    • Example: "jump" → stop walking, press Z                        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 2. LOCOMOTION SECOND (handle_locomotion)                            │ │
│  │    • Get latest from loco_queue                                     │ │
│  │    • Fuel system: "walk" → refresh fuel timer                       │ │
│  │    • Example: "walk" → press RIGHT_ARROW                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ 3. FUEL TIMEOUT MONITOR                                             │ │
│  │    • Check: (now - last_walk_confirmation) > 0.8s?                  │ │
│  │    • If yes: Stop walking, release arrow keys                       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  Keyboard Output:                                                        │
│    └─ pynput.Controller().press/release()                               │
└───────────────────────────────┬───────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 5: KEYBOARD OUTPUT                                                   │
│                                                                           │
│  Examples:                                                               │
│  • Walk right:  press(Key.right)                                         │
│  • Jump:        press('z'), release('z')                                 │
│  • Turn left:   release(Key.right), press(Key.left)                      │
│  • Punch:       press('x'), release('x')                                 │
└──────────────────────────────────────────────────────────────────────────┘
```

## Fuel Walk System State Machine

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         LOCOMOTION STATE MACHINE                          │
└──────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────┐
                    │     IDLE      │
                    │  (not walking)│
                    └───────┬───────┘
                            │
                    "walk" prediction
                    (confidence > 0.50)
                    (2 consecutive)
                            │
                            ↓
                    ┌───────────────┐
              ┌─────│   WALKING     │─────┐
              │     │  (arrow held) │     │
              │     └───────────────┘     │
              │             │             │
              │             │             │
   "walk"     │             │             │  "idle"
   prediction │             │             │  prediction
   (fuel      │             │             │  OR
   refresh)   │             │             │  0.8s timeout
              │             │             │  OR
              │             │             │  jump/punch
              │             ↓             │  action
              └─────────────┼─────────────┘
                            │
                    ┌───────────────┐
                    │   STOPPING    │
                    │(release arrow)│
                    └───────┬───────┘
                            │
                            ↓
                    ┌───────────────┐
                    │     IDLE      │
                    └───────────────┘
```

## Action Interrupt Flow

```
Scenario: Jump While Walking

Time T=0ms:
┌────────────────────────────────────────────────────────────────────┐
│ State: WALKING                                                      │
│ • is_walking = True                                                 │
│ • facing_direction = "right"                                        │
│ • pressed_keys = {"right"}                                          │
│ • Keyboard: Key.right is HELD                                       │
└────────────────────────────────────────────────────────────────────┘

Time T=100ms: Jump gesture detected
┌────────────────────────────────────────────────────────────────────┐
│ Sensor Input: High upward acceleration + rotation                   │
│    ↓                                                                │
│ Action Predictor:                                                   │
│    • Window: 75ms of data                                           │
│    • Prediction: "jump" with confidence 0.92                        │
│    • Action: result_action_queue.put(("jump", 0.92))               │
└────────────────────────────────────────────────────────────────────┘

Time T=120ms: Actor processes jump
┌────────────────────────────────────────────────────────────────────┐
│ Actor Loop (handle_action):                                         │
│                                                                     │
│ 1. Get from action_queue: ("jump", 0.92)                           │
│                                                                     │
│ 2. Check: is_walking = True → Must stop walking first!             │
│    • is_walking = False                                             │
│    • keyboard.release(Key.right)                                    │
│    • pressed_keys.remove("right")                                   │
│                                                                     │
│ 3. Execute jump:                                                    │
│    • keyboard.press('z')                                            │
│    • keyboard.release('z')                                          │
│    • state = "Jump!"                                                │
└────────────────────────────────────────────────────────────────────┘

Time T=300ms: Landing, can resume walking
┌────────────────────────────────────────────────────────────────────┐
│ Sensor Input: Walking motion resumes                                │
│    ↓                                                                │
│ Locomotion Predictor:                                               │
│    • Prediction: "walk" (0.83), "walk" (0.86) → consensus!         │
│    • Action: result_loco_queue.put(("walk", 0.86))                 │
│    ↓                                                                │
│ Actor Loop (handle_locomotion):                                     │
│    • is_walking = False → True                                      │
│    • keyboard.press(Key.right)                                      │
│    • pressed_keys.add("right")                                      │
│    • state = "Walking right"                                        │
└────────────────────────────────────────────────────────────────────┘
```

## Consensus vs Instant Processing

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        LOCOMOTION (Consensus)                             │
│                                                                           │
│  Why: Walking is a SUSTAINED STATE                                       │
│       Need stability to prevent jitter                                    │
│                                                                           │
│  How:                                                                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                                  │
│  │ Predict │  │ Predict │  │  Check  │                                  │
│  │  walk   │→ │  walk   │→ │ 2 match?│→ Send to actor                   │
│  │ (0.83)  │  │ (0.86)  │  │   YES   │                                  │
│  └─────────┘  └─────────┘  └─────────┘                                  │
│                                                                           │
│  Buffer: deque(maxlen=2)                                                 │
│  Time: ~40ms delay (2 predictions × 20ms)                                │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                         ACTIONS (Instant)                                 │
│                                                                           │
│  Why: Actions are INSTANT EVENTS                                         │
│       Need immediate response for gameplay                                │
│                                                                           │
│  How:                                                                     │
│  ┌─────────┐                                                              │
│  │ Predict │                                                              │
│  │  jump   │───────────────────→ Send to actor immediately               │
│  │ (0.92)  │                                                              │
│  └─────────┘                                                              │
│                                                                           │
│  Buffer: None (single prediction)                                        │
│  Time: ~20ms delay (1 prediction)                                        │
└──────────────────────────────────────────────────────────────────────────┘
```

## Performance Metrics

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          LATENCY BREAKDOWN                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Sensor Reading → UDP Packet:     1-2ms                                  │
│  Network Transit:                 5-10ms (LAN)                           │
│  UDP Receive → Queue:             <1ms                                   │
│  Queue → Predictor:               <1ms                                   │
│  Feature Extraction:              2-3ms                                   │
│  SVM Inference:                   5-10ms                                 │
│  Queue → Actor:                   <1ms                                   │
│  Keyboard Output:                 <1ms                                   │
│  ────────────────────────────────────────                                │
│  TOTAL (Actions):                 15-30ms                                │
│  TOTAL (Locomotion):              35-50ms (consensus delay)              │
│                                                                           │
├──────────────────────────────────────────────────────────────────────────┤
│                         THROUGHPUT METRICS                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Sensor Rate:                     50 Hz (readings/sec)                   │
│  Prediction Rate (Loco):          4-5 Hz (predictions/sec)               │
│  Prediction Rate (Action):        13-15 Hz (predictions/sec)             │
│  Keyboard Event Rate:             Variable (depends on gestures)         │
│                                                                           │
│  Queue Sizes:                                                            │
│    • sensor_loco_queue:           500 (10 seconds @ 50Hz)                │
│    • sensor_action_queue:         200 (4 seconds @ 50Hz)                 │
│    • result_loco_queue:           10 (2 seconds @ 5Hz)                   │
│    • result_action_queue:         10 (0.7 seconds @ 15Hz)                │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## System Comparison

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      BEFORE: Dual Classifier System                       │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────┐  ┌─────────────────────────┐                            │
│  │   Sensor   │  │    Binary Classifier    │                            │
│  │   Data     │──│   (walk vs idle only)   │── Locomotion               │
│  │            │  └─────────────────────────┘                            │
│  │            │                                                          │
│  │            │  ┌─────────────────────────┐                            │
│  │            │  │  Multiclass Classifier  │                            │
│  │            │──│  (jump, punch, turn_*,  │── Actions                  │
│  │            │  │   idle, noise only)     │                            │
│  └────────────┘  └─────────────────────────┘                            │
│                                                                           │
│  Models: 2 separate PKL files                                            │
│  Training: 2 separate pipelines                                          │
│  Classes: walk/idle separate from actions                                │
│  Problem: Walk doesn't compete with actions                              │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                   AFTER: Fuel Walk System (Unified)                       │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────┐  ┌─────────────────────────┐                            │
│  │   Sensor   │  │  Multiclass Classifier  │                            │
│  │   Data     │──│  (ALL 7 gestures:       │──┬── Locomotion (walk/idle)│
│  │            │  │   walk, jump, punch,    │  │                         │
│  │            │  │   turn_*, idle, noise)  │──┴── Actions (jump/punch/  │
│  └────────────┘  └─────────────────────────┘       turn_*)              │
│                                                                           │
│  Models: 1 unified PKL file                                              │
│  Training: 1 unified pipeline                                            │
│  Classes: All gestures in same prediction space                          │
│  Benefit: Walk competes with actions naturally                           │
│  Feature: Fuel timeout for walk control                                  │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## Conclusion

The Fuel Walk System achieves:
- **Unified prediction** using single multiclass SVM
- **Parallel processing** via asyncio concurrency
- **Action priority** through processing order
- **Fuel mechanism** for natural walk control
- **Sub-40ms latency** for gameplay responsiveness
