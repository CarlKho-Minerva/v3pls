# Section 1: Data Explanation (Clean Version)

## Data Source and Collection Methodology

### Custom Data Collection Infrastructure

Manual data labeling for wearable machine learning is challenging. My initial approach used voice commands for labeling ("walk", "punch", "jump"), which failed due to timestamp misalignment and class imbalance issues, achieving only 30% accuracy.

The solution: **I built two Android applications from scratch** to enable precise, button-based labeling with millisecond-accurate timestamps.

### Three-Device Data Collection Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Pixel Watch  │─UDP──│Android Phone │─UDP──│   MacBook    │
│ (Left Wrist) │      │(Right Hand)  │      │  (Python)    │
└──────────────┘      └──────────────┘      └──────────────┘
  Sensor Data           Button Events         Data Storage
  50Hz IMU              Label + Timestamp     CSV + Labels
```

**Device 1: Pixel Watch (Left Wrist)**
- Continuous 50Hz IMU sensor streaming  
- 9-axis data: 3-axis accelerometer, 3-axis gyroscope, 3-axis rotation (quaternions)
- UDP broadcast via Network Service Discovery (NSD)

**Device 2: Android Phone (Right Hand)**
- 2×3 button grid interface: Walk, Idle, Punch, Jump, Turn Left, Turn Right
- Press-and-hold interaction: press starts recording, release ends it
- Sends timestamped label events via UDP
- Real-time sample count display with balance indicators

**Device 3: MacBook (Python Backend)**
- UDP listener receiving both sensor data and label events
- Synchronizes streams using millisecond-precision timestamps
- Saves labeled CSV files: `{action}_{start_timestamp}_to_{end_timestamp}.csv`

### Why Button-Based Labeling Succeeded

The button approach solved three critical problems:

1. **Precise temporal alignment**: Gesture occurs exactly between button press and release
2. **No timestamp drift**: Direct synchronization via UDP messaging  
3. **Balanced classes**: No default label accumulating excess samples

Voice labeling failed because audio processing introduced 200-500ms latency and defaulted to "walk" when uncertain, creating severe class imbalance.

## Dataset Structure and Format

### Raw Sensor Data Format

Each CSV file contains:
- `timestamp_ms`: Unix timestamp in milliseconds
- `accel_x`, `accel_y`, `accel_z`: Linear acceleration (m/s²) without gravity
- `gyro_x`, `gyro_y`, `gyro_z`: Angular velocity (rad/s)
- `rot_x`, `rot_y`, `rot_z`, `rot_w`: Rotation quaternion components

**Example filename:** `punch_1760861014718_to_1760861016454.csv`

This encodes:
- Action label: `punch`
- Start timestamp: `1760861014718` ms
- End timestamp: `1760861016454` ms  
- Duration: 1736ms (~1.7 seconds)

### Dataset Statistics

**Binary Classification (Locomotion States):**
- Walk: 71 samples @ ~5-10 seconds each
- Idle: 74 samples @ ~5-10 seconds each

**Multiclass Classification (Discrete Gestures):**
- Jump: 100 samples @ ~1-2 seconds each
- Punch: 100 samples @ ~1-2 seconds each
- Turn Left: 100 samples @ ~0.5-1 seconds each
- Turn Right: 100 samples @ ~0.5-1 seconds each
- Idle: 74 samples @ ~5-10 seconds each
- Noise: 100 samples (random non-gesture movements)

**Total dataset:** 719 samples, ~2400 seconds of labeled motion data

### Dual Classifier Strategy

I'm building two independent classifiers rather than one unified model:

**Task 1: Binary Classification**
- Classes: Walk vs. Idle
- Purpose: Determine locomotion state
- Window: 5-10 second durations

**Task 2: Multiclass Classification**  
- Classes: Jump, Punch, Turn Left, Turn Right, Idle, Noise
- Purpose: Recognize discrete gestures
- Window: 0.5-2 second durations

**Rationale:** Locomotion states (walk/idle) and ballistic gestures (punch/jump/turn) have fundamentally different temporal characteristics. Training them separately allows optimizing window sizes and features for each task independently.

The "noise" class enables the model to reject non-gesture movements, preventing false positives during normal daily activity.

## Data Quality Considerations

**Manual quality control:**
- Deleted incomplete recordings (< 200ms)
- Removed double-gesture samples (e.g., accidental double punch)
- Verified timestamp synchronization across devices

**Collection environment:**
- Indoor, controlled conditions
- Single user (myself)
- Pixel Watch worn on left wrist
- Data collected over 2-hour period with varied execution speeds

**Known limitations:**
- Single-user dataset (may not generalize to different users)
- Controlled environment (untested in natural conditions)
- Pre-segmented gestures (deployment requires real-time segmentation)

## Images Required

1. **Figure 1.1**: Screenshot of Android phone button grid interface
2. **Figure 1.2**: Screenshot of Python dashboard showing real-time sensor data
3. **Figure 1.3**: Architecture diagram (three-device setup)
4. **Figure 1.4**: Sample raw accelerometer data from single punch gesture
5. **Figure 1.5**: Class distribution bar chart showing sample counts per class

## References

1. Android Developers. (2024). Sensors Overview. https://developer.android.com/guide/topics/sensors/sensors_overview
2. Lara, O. D., & Labrador, M. A. (2013). A survey on human activity recognition using wearable sensors. IEEE Communications Surveys & Tutorials, 15(3), 1192-1209.
3. Bulling, A., Blanke, U., & Schiele, B. (2014). A tutorial on human activity recognition using body-worn inertial sensors. ACM Computing Surveys, 46(3), 1-33.
