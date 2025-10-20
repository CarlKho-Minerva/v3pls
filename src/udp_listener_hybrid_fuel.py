#!/usr/bin/env python3
"""
Hybrid Silksong ML Controller - Fuel Walk + Multiclass Actions

ARCHITECTURE:
- Fuel Walk System: Pedometer-based (amplitude + gyro thresholds from v1)
- Action Classification: Multiclass SVM (punch, jump, turn_left, turn_right, idle, noise)
- Parallel Processing: asyncio for concurrent walk monitoring + action detection
- Game-Ready: Actions can execute WHILE walking (like the actual game)

KEY FEATURES:
1. Walking uses simple physics (swing amplitude + gyro rotation detection)
2. Actions use ML classifier (more complex gestures need intelligence)
3. Both systems run in parallel threads for responsiveness
4. Turn gestures change walk direction without stopping
5. Jump/Punch can trigger while walking (stops walk momentarily)
"""
import socket
import json
import time
import os
import asyncio
import math
from collections import deque
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from scipy.fft import rfft
from scipy.stats import skew, kurtosis
from pynput.keyboard import Controller, Key
from zeroconf import ServiceInfo
from zeroconf.asyncio import AsyncZeroconf

# ============================================================
# 🎛️  SYSTEM TOGGLES
# ============================================================
ENABLE_FUEL_WALK = True  # v1 pedometer-based walking
ENABLE_ACTIONS = True  # ML-based action detection
ENABLE_KEYBOARD_OUTPUT = True  # Actually send keypresses
# ============================================================

# --- Feature Extraction (copied from original) ---
def extract_features_from_dataframe(df):
    """Extract features from sensor DataFrame"""
    features = {}
    for axis in ["accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z"]:
        signal = df[axis].dropna()
        if len(signal) == 0:
            continue

        # Time domain
        features[f"{axis}_mean"] = signal.mean()
        features[f"{axis}_std"] = signal.std()
        features[f"{axis}_max"] = signal.max()
        features[f"{axis}_min"] = signal.min()
        features[f"{axis}_range"] = signal.max() - signal.min()
        features[f"{axis}_median"] = signal.median()
        features[f"{axis}_skew"] = skew(signal)
        features[f"{axis}_kurtosis"] = kurtosis(signal)

        # Frequency domain
        fft_vals = np.abs(rfft(signal.values))
        features[f"{axis}_fft_mean"] = fft_vals.mean()
        features[f"{axis}_fft_max"] = fft_vals.max()
        features[f"{axis}_fft_std"] = fft_vals.std()

    return features


# --- Configuration ---
import sys
sys.path.append(str(Path(__file__).parent))
import network_utils

config = network_utils.setup_config()
LISTEN_IP, LISTEN_PORT = (
    config["network"]["listen_ip"],
    config["network"]["listen_port"],
)

# Fuel walk config (from v1 calibration style)
FUEL_WALK_CONFIG = config.get("fuel_walk", {
    "swing_amplitude_threshold": 3.0,
    "gyro_noise_limit": 0.5,
    "rotation_threshold_radians": 3.14
})

KEY_MAP = {"left": Key.left, "right": Key.right, "jump": "z", "attack": "x"}
ML_CONFIDENCE_THRESHOLD = 0.50

# ============================================================
# 🎮 SHARED STATE
# ============================================================
class ControllerState:
    def __init__(self):
        # Walk state (fuel system from v1)
        self.is_walking = False
        self.facing_right = True
        self.walking_key_pressed = False
        self.current_walking_key = None
        self.initial_gyro_heading = None
        self.total_rotation = 0.0
        self.last_fuel_check_time = time.time()

        # Action state
        self.actor_state = "Idle"
        self.last_action_time = 0

        # Network state
        self.watch_connected = False
        self.last_watch_data_time = 0
        self.sensor_data_rate = 0.0

        # Display
        self.last_action_pred = ("-", 0.0)


# ============================================================
# 🚶 FUEL WALK SYSTEM (v1 Pedometer Logic - ACTUAL IMPLEMENTATION)
# ============================================================

# Constants from v1
GRAVITY_CONSTANT = 9.81
GRAVITY_THRESHOLD = 9.0  # For state detection

def determine_state_from_sensors(x, y, z):
    """Determine phone orientation state from gravity"""
    if abs(y) > GRAVITY_THRESHOLD:
        return "COMBAT"  # Phone vertical
    elif abs(x) > GRAVITY_THRESHOLD:
        return "WALKING"  # Phone horizontal
    else:
        return "IDLE"

def get_stable_state(raw_state, state_buffer):
    """Apply state stability buffer - requires 4/5 consensus"""
    state_buffer.append(raw_state)

    walking_count = state_buffer.count("WALKING")
    combat_count = state_buffer.count("COMBAT")
    idle_count = state_buffer.count("IDLE")

    if walking_count >= 4:
        return "WALKING"
    elif combat_count >= 4:
        return "COMBAT"
    elif idle_count >= 4:
        return "IDLE"
    else:
        return None  # No consensus

def manage_walking_key_press(should_walk, direction_key, state, keyboard):
    """Handle sustained key press for walking (v1 logic)"""
    if should_walk and not state.walking_key_pressed:
        # Start walking - press and hold key
        if ENABLE_KEYBOARD_OUTPUT:
            keyboard.press(direction_key)
        state.walking_key_pressed = True
        state.current_walking_key = direction_key
        return "WALK_KEY_PRESS"
    elif should_walk and state.walking_key_pressed and state.current_walking_key != direction_key:
        # Direction changed - release old key, press new key
        if ENABLE_KEYBOARD_OUTPUT:
            keyboard.release(state.current_walking_key)
            keyboard.press(direction_key)
        state.current_walking_key = direction_key
        return "WALK_DIRECTION_CHANGE"
    elif not should_walk and state.walking_key_pressed:
        # Stop walking - release key
        if ENABLE_KEYBOARD_OUTPUT:
            keyboard.release(state.current_walking_key)
        state.walking_key_pressed = False
        state.current_walking_key = None
        return "WALK_KEY_RELEASE"

    return None

async def fuel_walk_monitor(sensor_queue: asyncio.Queue, state: ControllerState, keyboard: Controller):
    """
    v1 Pedometer Implementation with State Machine

    Based on original udp_listener.py from SilksongController:
    - Gravity-based state detection (WALKING/COMBAT/IDLE)
    - Rolling state buffer for stability
    - Gyro integration for rotation tracking
    - Swing amplitude for walk detection
    - Sustained key press management
    """
    print("🚶 Fuel Walk Monitor started (v1 pedometer)")

    state_buffer = deque(maxlen=5)  # Rolling buffer for state stability
    last_time = time.time()
    current_phone_state = "IDLE"

    while True:
        try:
            sensor_data = await asyncio.wait_for(sensor_queue.get(), timeout=0.05)

            x, y, z = sensor_data["accel_x"], sensor_data["accel_y"], sensor_data["accel_z"]
            gyro_y = sensor_data.get("gyro_y", 0.0)
            timestamp = sensor_data["timestamp"]

            # Set initial heading on first data (v1 dynamic zero point)
            if state.initial_gyro_heading is None:
                state.initial_gyro_heading = gyro_y
                print("▶️ Initial heading set (forward direction locked)")

            # Calculate time delta for gyro integration
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time

            # --- STATE DETECTION (v1 stability buffer) ---
            raw_state = determine_state_from_sensors(x, y, z)
            stable_state = get_stable_state(raw_state, state_buffer)

            if stable_state is not None:
                current_phone_state = stable_state

            # --- ROTATION TRACKING (v1 relative rotation) ---
            effective_gyro = gyro_y - state.initial_gyro_heading
            gyro_limit = FUEL_WALK_CONFIG["gyro_noise_limit"]

            if abs(effective_gyro) > gyro_limit:
                state.total_rotation += effective_gyro * delta_time

            # Calculate facing direction
            rotation_threshold = FUEL_WALK_CONFIG["rotation_threshold_radians"]
            state.facing_right = state.total_rotation < rotation_threshold

            # --- WALKING DETECTION (v1 fuel system) ---
            if current_phone_state == "WALKING" and ENABLE_FUEL_WALK:
                # Check for swing amplitude
                swing_threshold = FUEL_WALK_CONFIG["swing_amplitude_threshold"]
                currently_walking = abs(z) > swing_threshold

                # Determine direction based on rotation
                direction_key = Key.right if state.facing_right else Key.left

                # Manage sustained key press (v1 logic)
                key_action = manage_walking_key_press(
                    currently_walking, direction_key, state, keyboard
                )

                if key_action == "WALK_KEY_PRESS":
                    state.is_walking = True
                    print(f"\n🚶 Walk started: {'RIGHT' if state.facing_right else 'LEFT'}")
                elif key_action == "WALK_DIRECTION_CHANGE":
                    print(f"\n🔄 Direction changed: {'RIGHT' if state.facing_right else 'LEFT'}")
                elif key_action == "WALK_KEY_RELEASE":
                    state.is_walking = False
                    print(f"\n⏹️  Walk stopped (fuel depleted)")

            elif current_phone_state == "COMBAT":
                # Phone vertical - stop walking if active
                if state.walking_key_pressed:
                    if ENABLE_KEYBOARD_OUTPUT:
                        keyboard.release(state.current_walking_key)
                    state.walking_key_pressed = False
                    state.is_walking = False
                    print(f"\n� Walk stopped (entered COMBAT state)")

            elif current_phone_state == "IDLE":
                # Phone in transition - maintain current walk state
                pass

            state.last_fuel_check_time = timestamp

        except asyncio.TimeoutError:
            continue
        except Exception as e:
            print(f"\n⚠️  Fuel Walk Error: {e}")
            await asyncio.sleep(0.01)


# ============================================================
# 🎯 ACTION CLASSIFIER (Multiclass SVM)
# ============================================================
async def action_classifier(sensor_queue: asyncio.Queue, action_queue: asyncio.Queue, models: dict, state: ControllerState):
    """
    Classifies actions (punch, jump, turn_left, turn_right, idle, noise) using ML.
    Uses 75ms sliding window for quick action detection.
    """
    print("🎯 Action Classifier started")

    WINDOW_SIZE_MS = 75
    buffer = deque(maxlen=100)

    clf = models["classifier"]
    scaler = models["scaler"]
    feature_names = models["feature_names"]

    while True:
        try:
            sensor_data = await asyncio.wait_for(sensor_queue.get(), timeout=0.05)
            buffer.append(sensor_data)

            # Need enough data for window
            if len(buffer) < 5:
                continue

            # Extract window
            now = sensor_data["timestamp"]
            window_start = now - (WINDOW_SIZE_MS / 1000.0)
            window_data = [s for s in buffer if s["timestamp"] >= window_start]

            if len(window_data) < 3:
                continue

            # Extract features
            df = pd.DataFrame(window_data)
            features = extract_features_from_dataframe(df)

            if not features:
                continue

            # Prepare for prediction
            feature_vector = [features.get(fname, 0.0) for fname in feature_names]
            X = scaler.transform([feature_vector])

            # Predict
            proba = clf.predict_proba(X)[0]
            predicted_class = clf.classes_[np.argmax(proba)]
            confidence = proba.max()

            # Filter low confidence and noise
            if confidence < ML_CONFIDENCE_THRESHOLD or predicted_class == "noise":
                continue

            # Queue action for actor
            await action_queue.put({
                "action": predicted_class,
                "confidence": confidence,
                "timestamp": now
            })

            state.last_action_pred = (predicted_class, confidence)

        except asyncio.TimeoutError:
            continue
        except Exception as e:
            print(f"\n⚠️  Action Classifier Error: {e}")
            await asyncio.sleep(0.01)


# ============================================================
# 🎬 ACTOR (Executes Actions While Walking)
# ============================================================
async def actor(action_queue: asyncio.Queue, state: ControllerState, keyboard: Controller):
    """
    Executes actions from ML classifier while maintaining walk state.

    Priority:
    - Turn gestures: Change walk direction (don't stop walking)
    - Jump/Punch: Execute action (temporarily stop walking)
    - Idle: Ignored (walk system handles stopping)
    """
    print("🎬 Actor started")

    ACTION_COOLDOWN = 0.3

    while True:
        try:
            action_data = await asyncio.wait_for(action_queue.get(), timeout=0.05)

            action = action_data["action"]
            confidence = action_data["confidence"]
            now = action_data["timestamp"]

            # Cooldown check
            if (now - state.last_action_time) < ACTION_COOLDOWN:
                continue

            if not ENABLE_ACTIONS:
                continue

            # Handle turns (change direction, don't stop walking)
            if action == "turn_left":
                state.facing_right = False
                state.total_rotation = FUEL_WALK_CONFIG["rotation_threshold_radians"] + 0.1

                if state.is_walking and state.walking_key_pressed and ENABLE_KEYBOARD_OUTPUT:
                    keyboard.release(state.current_walking_key)
                    keyboard.press(Key.left)
                    state.current_walking_key = Key.left

                state.actor_state = "Turn Left"
                print(f"\n↩️  TURN LEFT (conf: {confidence:.0%})")
                state.last_action_time = now

            elif action == "turn_right":
                state.facing_right = True
                state.total_rotation = 0.0

                if state.is_walking and state.walking_key_pressed and ENABLE_KEYBOARD_OUTPUT:
                    keyboard.release(state.current_walking_key)
                    keyboard.press(Key.right)
                    state.current_walking_key = Key.right

                state.actor_state = "Turn Right"
                print(f"\n↪️  TURN RIGHT (conf: {confidence:.0%})")
                state.last_action_time = now

            # Handle jump (stop walking temporarily)
            elif action == "jump":
                # Stop walking
                if state.is_walking and state.walking_key_pressed and ENABLE_KEYBOARD_OUTPUT:
                    keyboard.release(state.current_walking_key)
                    state.walking_key_pressed = False
                    state.is_walking = False

                # Execute jump
                if ENABLE_KEYBOARD_OUTPUT:
                    keyboard.press(KEY_MAP["jump"])
                    await asyncio.sleep(0.1)
                    keyboard.release(KEY_MAP["jump"])

                state.actor_state = "Jump!"
                print(f"\n⬆️  JUMP (conf: {confidence:.0%})")
                state.last_action_time = now

            # Handle punch (stop walking temporarily)
            elif action == "punch":
                # Stop walking
                if state.is_walking and state.walking_key_pressed and ENABLE_KEYBOARD_OUTPUT:
                    keyboard.release(state.current_walking_key)
                    state.walking_key_pressed = False
                    state.is_walking = False

                # Execute punch
                if ENABLE_KEYBOARD_OUTPUT:
                    keyboard.press(KEY_MAP["attack"])
                    await asyncio.sleep(0.1)
                    keyboard.release(KEY_MAP["attack"])

                state.actor_state = "Punch!"
                print(f"\n👊 PUNCH (conf: {confidence:.0%})")
                state.last_action_time = now

        except asyncio.TimeoutError:
            continue
        except Exception as e:
            print(f"\n⚠️  Actor Error: {e}")
            await asyncio.sleep(0.01)


# ============================================================
# 📡 UDP DISTRIBUTOR
# ============================================================
async def distributor(walk_queue: asyncio.Queue, action_queue: asyncio.Queue, state: ControllerState):
    """
    Receives UDP sensor data and distributes to both:
    1. Fuel walk monitor (raw data)
    2. Action classifier (raw data)
    """
    print(f"📡 Listening on {LISTEN_IP}:{LISTEN_PORT}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_IP, LISTEN_PORT))
    sock.setblocking(False)

    packet_count = 0
    last_rate_calc = time.time()

    while True:
        try:
            data, addr = await asyncio.get_event_loop().sock_recvfrom(sock, 1024)
            message = data.decode().strip()

            if message.startswith("SENSOR:"):
                parts = message.replace("SENSOR:", "").split(',')

                if len(parts) >= 6:
                    sensor_data = {
                        "accel_x": float(parts[0]),
                        "accel_y": float(parts[1]),
                        "accel_z": float(parts[2]),
                        "gyro_x": float(parts[3]),
                        "gyro_y": float(parts[4]),
                        "gyro_z": float(parts[5]),
                        "timestamp": time.time()
                    }

                    # Distribute to both systems
                    await walk_queue.put(sensor_data)
                    await action_queue.put(sensor_data)

                    # Update connection state
                    packet_count += 1
                    now = time.time()

                    if not state.watch_connected:
                        state.watch_connected = True
                        print("\n✅ Watch connected!")

                    state.last_watch_data_time = now

                    # Calculate data rate
                    if (now - last_rate_calc) >= 1.0:
                        state.sensor_data_rate = packet_count
                        packet_count = 0
                        last_rate_calc = now

        except Exception as e:
            await asyncio.sleep(0.01)


# ============================================================
# 📊 DASHBOARD
# ============================================================
async def dashboard(state: ControllerState):
    """Display live status"""
    print("\n" + "="*60)
    print("      Hybrid Silksong Controller - FUEL WALK + ML ACTIONS")
    print("="*60)

    while True:
        watch_status = "✓ CONNECTED" if state.watch_connected else "✗ DISCONNECTED"
        walk_status = f"{'🚶 WALKING' if state.is_walking else '🧍 IDLE'} ({'→' if state.facing_right else '←'})"

        print(f"\r[{watch_status}] [{state.sensor_data_rate:.0f} Hz] | " +
              f"Walk: {walk_status} | " +
              f"Action: {state.last_action_pred[0]} ({state.last_action_pred[1]:.0%}) | " +
              f"State: {state.actor_state}", end="", flush=True)

        await asyncio.sleep(0.1)


# ============================================================
# 🚀 MAIN
# ============================================================
async def main_async():
    # Load multiclass model
    models_path = Path(__file__).parent.parent / "models"

    try:
        models = {
            "classifier": joblib.load(models_path / "gesture_classifier_multiclass.pkl"),
            "scaler": joblib.load(models_path / "feature_scaler_multiclass.pkl"),
            "feature_names": joblib.load(models_path / "feature_names_multiclass.pkl")
        }
        print("✅ Multiclass models loaded")
    except Exception as e:
        print(f"❌ Failed to load models: {e}")
        print("Run notebooks/SVM_Local_Training.py first!")
        return

    # Initialize
    state = ControllerState()
    keyboard = Controller()

    # Create queues
    walk_sensor_queue = asyncio.Queue(maxsize=50)
    action_sensor_queue = asyncio.Queue(maxsize=50)
    action_result_queue = asyncio.Queue(maxsize=20)

    # Start all tasks
    try:
        await asyncio.gather(
            distributor(walk_sensor_queue, action_sensor_queue, state),
            fuel_walk_monitor(walk_sensor_queue, state, keyboard),
            action_classifier(action_sensor_queue, action_result_queue, models, state),
            actor(action_result_queue, state, keyboard),
            dashboard(state)
        )
    except KeyboardInterrupt:
        print("\n\n✅ Controller stopped.")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
