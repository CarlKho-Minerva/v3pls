# Parallel Threading for Actions While Walking - Technical Guide

## Overview

This guide explains how the Silksong controller achieves **concurrent gesture processing** using Python's `asyncio` library, enabling actions to be performed while walking without blocking.

## Architecture

### Concurrent Task Model

```python
asyncio.gather(
    distributor(sensor_queues, state),      # Task 1: UDP receiver
    predictor(loco_queue, ...),             # Task 2: Walk/idle detection
    predictor(action_queue, ...),           # Task 3: Action detection
    actor(loco_queue, action_queue, state), # Task 4: Keyboard controller
    dashboard(state, queues)                # Task 5: Live display
)
```

All 5 tasks run **concurrently** (not sequentially), allowing:
- Sensor data to flow continuously
- ML predictions to process in parallel
- Keyboard actions to execute immediately
- UI to update without blocking

## Threading vs Async: Why Asyncio?

### Traditional Threading Issues
```python
# PROBLEMATIC: True threading
thread1 = Thread(target=predictor_walk)
thread2 = Thread(target=predictor_action)
thread3 = Thread(target=actor)

# Issues:
# - Race conditions on shared state
# - GIL (Global Interpreter Lock) limits parallelism
# - Thread context switching overhead
# - Harder to debug and reason about
```

### Asyncio Solution
```python
# BETTER: Cooperative multitasking
async def predictor_walk():
    while True:
        # Do work...
        await asyncio.sleep(0)  # Yield control

async def predictor_action():
    while True:
        # Do work...
        await asyncio.sleep(0)  # Yield control

# Benefits:
# - No race conditions (single-threaded event loop)
# - Explicit yield points (await)
# - Lower overhead than threads
# - Deterministic execution order
```

## Data Flow: Sensor to Keyboard

```
┌────────────────────────────────────────────────────────────────┐
│ 1. SENSOR INPUT (Watch → UDP)                                   │
│    Linear Acceleration + Gyroscope @ 50Hz                       │
└────────────────┬───────────────────────────────────────────────┘
                 ↓
┌────────────────┴───────────────────────────────────────────────┐
│ 2. DISTRIBUTOR (async UDP receiver)                             │
│    Combines accel + gyro into sensor readings                   │
│    Sends to BOTH queues simultaneously                          │
├──────────────────────────────┬──────────────────────────────────┤
│   sensor_loco_queue (500)    │   sensor_action_queue (200)     │
└──────────────┬───────────────┴──────────────┬──────────────────┘
               ↓                                ↓
┌──────────────┴──────────────┐  ┌────────────┴─────────────────┐
│ 3. PREDICTOR (Locomotion)    │  │ 3. PREDICTOR (Action)        │
│    Window: 250ms (stable)    │  │    Window: 75ms (responsive) │
│    Buffer: 250 readings      │  │    Buffer: 75 readings       │
│    Model: multiclass SVM     │  │    Model: multiclass SVM     │
│    Looks for: walk, idle     │  │    Looks for: jump, punch,   │
│    Consensus: 2 predictions  │  │                turn_*, idle  │
│    Output: result_loco_queue │  │    Consensus: NONE (instant) │
└──────────────┬──────────────┘  └────────────┬─────────────────┘
               ↓                                ↓
               │  result_loco_queue (10)        │  result_action_queue (10)
               └──────────────┬─────────────────┘
                              ↓
┌────────────────────────────┴────────────────────────────────────┐
│ 4. ACTOR (Keyboard Controller)                                   │
│    PRIORITY ORDER:                                               │
│    1. Process action_queue FIRST (can interrupt walking)         │
│    2. Process loco_queue SECOND (maintains walk state)           │
│    3. Monitor fuel timeout (auto-stop walking)                   │
│                                                                  │
│    Outputs: pynput.keyboard.Controller                           │
└────────────────────────────┬────────────────────────────────────┘
                              ↓
┌────────────────────────────┴────────────────────────────────────┐
│ 5. KEYBOARD OUTPUT                                               │
│    Arrow keys (left/right) for walking                           │
│    Z key for jump                                                │
│    X key for attack/punch                                        │
└──────────────────────────────────────────────────────────────────┘
```

## Parallel Processing in Detail

### Scenario: Jumping While Walking

Let's trace what happens when you jump while walking:

#### Time: T=0ms (Walking steadily)
```
Locomotion Queue: [("walk", 0.85), ("walk", 0.82)]
Action Queue: []
Actor State: is_walking=True, facing_direction="right"
Keyboard: RIGHT_ARROW pressed
```

#### Time: T=100ms (Jump gesture detected)
```
Sensor Input: High acceleration + rotation (jump motion detected)
↓
Action Predictor: Processes 75ms window
  → Confidence: jump=0.92 (above threshold!)
  → Puts to action_queue IMMEDIATELY (no consensus needed)
```

#### Time: T=110ms (Actor processes jump)
```python
# Actor loop runs every 20ms
await handle_action(action_queue, ...)
  ↓
  latest_gesture = "jump"  # Get from action_queue
  ↓
  is_walking = False  # STOP WALKING FIRST
  keyboard.release(Key.right)  # Release right arrow
  ↓
  keyboard.press('z')  # Press jump key
  keyboard.release('z')
  ↓
  state = "Jump!"
```

#### Time: T=120ms (Locomotion still processing)
```
Locomotion Queue: [("walk", 0.78)]
↓
Actor processes locomotion AFTER action
↓
But is_walking=False now (action interrupted it)
↓
Walk prediction ignored (not in walking state)
```

#### Time: T=300ms (Landing, back to walking)
```
Sensor Input: Walking motion resumes
↓
Locomotion Predictor: [("walk", 0.83), ("walk", 0.86)]
  → Consensus achieved (2 consecutive walk predictions)
  → Puts to loco_queue
↓
Actor processes:
  is_walking = False → True
  keyboard.press(Key.right)
  state = "Walking right"
```

### Key Points

1. **Non-blocking queues**: `asyncio.Queue` allows producers and consumers to run independently
2. **Priority via processing order**: Actions checked BEFORE locomotion in actor loop
3. **State sharing**: All coroutines access shared `state` object (safe because single-threaded)
4. **Explicit yields**: `await asyncio.sleep(0.02)` gives control back to event loop

## Queue Sizes Explained

```python
sensor_loco_queue = Queue(500)    # Large buffer for walk detection
sensor_action_queue = Queue(200)  # Medium buffer for action detection
result_loco_queue = Queue(10)     # Small buffer (consensus slows output)
result_action_queue = Queue(10)   # Small buffer (instant output)
```

### Why Different Sizes?

- **Sensor queues (500/200)**: Buffer raw sensor data to prevent drops during ML processing
- **Result queues (10)**: ML predictions are slower than sensor input, small queue is sufficient
- **Locomotion larger**: Walk detection uses 250ms window = needs more buffered data

## Async Patterns Used

### Pattern 1: Non-blocking Queue Operations
```python
# Producer (predictor)
await result_queue.put((gesture, confidence))

# Consumer (actor)
try:
    gesture, conf = action_queue.get_nowait()  # Don't block if empty
except asyncio.QueueEmpty:
    pass  # No action available, continue
```

### Pattern 2: Clearing Stale Data
```python
# Only process LATEST prediction (real-time control)
latest_gesture = None
while True:
    try:
        latest_gesture, conf = queue.get_nowait()
    except asyncio.QueueEmpty:
        break  # Drained queue, use latest

if latest_gesture:
    # Process only most recent
```

### Pattern 3: Yield Points
```python
async def predictor():
    while True:
        reading = await sensor_queue.get()  # Explicit yield point
        # ... ML processing ...
        await result_queue.put(prediction)  # Explicit yield point
        # No blocking operations between yields!
```

## Performance Characteristics

### Timing Breakdown (Typical)
```
Sensor Rate: 50 Hz (20ms interval)
UDP Receive: <1ms latency
Queue Put: <0.1ms
ML Inference: 5-10ms (SVM prediction)
Queue Get: <0.1ms
Keyboard Output: <1ms

Total Latency (sensor → keyboard): 25-40ms
```

### Why So Fast?
- Asyncio has lower overhead than threads (~100x less context switch time)
- SVM inference is very fast (linear model after kernel transformation)
- No blocking I/O (UDP is fire-and-forget)
- Single-threaded = no lock contention

### Bottlenecks
1. **ML Inference**: The slowest part (5-10ms per prediction)
   - Mitigated by: Running 2 predictors concurrently
2. **Sensor Rate**: Limited by watch hardware (50 Hz)
   - Acceptable for gesture recognition
3. **Queue Overflow**: If ML is too slow, sensor queues fill
   - Mitigated by: Large queue sizes (500/200)

## Comparison: Sequential vs Concurrent

### Sequential Processing (BAD)
```python
while True:
    sensor_data = receive_udp()  # 1ms
    walk_prediction = ml_predict(sensor_data)  # 10ms
    action_prediction = ml_predict(sensor_data)  # 10ms
    execute_keyboard(walk_prediction, action_prediction)  # 1ms
    # Total: 22ms per iteration
    # Can only process 45 sensors/sec (misses data!)
```

### Concurrent Processing (GOOD)
```python
# All run simultaneously
await asyncio.gather(
    receive_udp(),     # Continuous
    ml_predict_walk(), # Continuous
    ml_predict_action(), # Continuous
    execute_keyboard()   # Continuous
)
# All run at full speed
# Can process 50 sensors/sec (no data loss!)
```

## Debugging Concurrent Code

### Enable Debug Mode
```python
# Show queue sizes in dashboard
print(f"Loco queue: {queues['result_loco'].qsize()}")
print(f"Action queue: {queues['result_action'].qsize()}")
```

### Common Issues

**Queue Overflow**
```python
if sensor_queue.qsize() > 400:
    print("⚠️  Sensor queue filling up!")
    # ML predictor is too slow
```

**Dropped Predictions**
```python
if result_queue.qsize() == result_queue.maxsize:
    print("⚠️  Result queue full, dropping prediction")
    # Actor is too slow
```

**Latency Spikes**
```python
start_time = time.time()
prediction = await ml_predict(...)
elapsed = time.time() - start_time
if elapsed > 0.015:  # 15ms threshold
    print(f"⚠️  Slow prediction: {elapsed*1000:.1f}ms")
```

## Best Practices

1. **Keep async functions fast**: No long computations without yield points
2. **Use queue sizes wisely**: Balance memory vs dropped data
3. **Process latest data**: Clear stale predictions from queues
4. **Explicit priorities**: Process critical queues first
5. **Monitor queue depths**: Detect performance issues early

## Summary

The fuel walk system achieves parallel action processing through:

1. **Asyncio event loop**: Single-threaded cooperative multitasking
2. **Multiple concurrent coroutines**: Sensor input, ML prediction, keyboard output
3. **Non-blocking queues**: Producer-consumer pattern without locks
4. **Priority processing**: Actions before locomotion in actor loop
5. **State management**: Shared state object with implicit synchronization

This architecture allows **sub-40ms latency** from sensor to keyboard while handling complex gesture interactions like jumping while walking.
