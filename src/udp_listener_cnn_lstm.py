#!/usr/bin/env python3
"""
Silksong ML Controller with CNN-LSTM Support (ASYNC STREAMING VERSION)

This version adds support for CNN-LSTM models alongside the existing SVM models.
Toggle between model types using the USE_CNN_LSTM flag.

- CNN-LSTM: Deep learning approach with temporal feature extraction
- SVM: Traditional ML with hand-crafted features
"""
import socket
import json
import time
import os
import asyncio
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
# 🎛️  SYSTEM TOGGLES - Control what systems are active
# ============================================================
ENABLE_LOCOMOTION = False  # Turn OFF to test actions only
ENABLE_ACTIONS = True  # Jump, Punch, Turns
ENABLE_KEYBOARD_OUTPUT = True  # Set False to just see predictions
USE_CNN_LSTM = True  # Set True to use CNN-LSTM models, False for SVM
# ============================================================


# --- Import local modules ---
def extract_features_from_dataframe(df):
    """
    Extract features from a DataFrame containing sensor readings.
    Used by SVM models.
    """
    features = {}
    for axis in ["accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z"]:
        signal = df[axis].dropna()
        if len(signal) > 0:
            features[f"{axis}_mean"] = signal.mean()
            features[f"{axis}_std"] = signal.std()
            features[f"{axis}_min"] = signal.min()
            features[f"{axis}_max"] = signal.max()
            features[f"{axis}_skew"] = skew(signal)
            features[f"{axis}_kurtosis"] = kurtosis(signal)
            if len(signal) > 2:
                fft_vals = np.abs(rfft(signal.to_numpy()))[: len(signal) // 2]
                if len(fft_vals) > 0:
                    features[f"{axis}_fft_max"] = fft_vals.max()
                    features[f"{axis}_fft_mean"] = fft_vals.mean()
    return features


import network_utils

# Import CNN-LSTM predictor if available
try:
    from cnn_lstm_predictor import CNNLSTMPredictor, load_cnn_lstm_models
    CNN_LSTM_AVAILABLE = True
except ImportError:
    CNN_LSTM_AVAILABLE = False
    print("⚠️  CNN-LSTM predictor not available. Install TensorFlow to use CNN-LSTM models.")


# --- ANSI Colors ---
class Colors:
    GREEN, RED, YELLOW, BLUE, CYAN, RESET, BOLD = (
        "\033[92m",
        "\033[91m",
        "\033[93m",
        "\033[94m",
        "\033[96m",
        "\033[0m",
        "\033[1m",
    )


# --- Shared State for Dashboard ---
class SharedState:
    def __init__(self):
        self.watch_connected = False
        self.last_watch_data_time = 0
        self.sensor_data_rate = 0.0
        self.last_locomotion_pred = ("-", 0.0)
        self.last_action_pred = ("-", 0.0)
        self.current_actor_state = "Idle"
        self.model_type = "CNN-LSTM" if USE_CNN_LSTM else "SVM"


# --- Configuration & Setup ---
config = network_utils.setup_config()
LISTEN_IP, LISTEN_PORT = (
    config["network"]["listen_ip"],
    config["network"]["listen_port"],
)
KEY_MAP = {"left": Key.left, "right": Key.right, "jump": "z", "attack": "x"}
ML_CONFIDENCE_THRESHOLD = 0.50
CONSENSUS_WINDOW = 2

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
BINARY_CLASSES = ["walk", "idle"]
MULTI_CLASSES = ["jump", "punch", "turn_left", "turn_right", "idle", "noise"]

# --- Model Loading ---
print(f"\n{'='*60}")
print(f"Loading Models: {'CNN-LSTM' if USE_CNN_LSTM else 'SVM'}")
print(f"{'='*60}\n")

if USE_CNN_LSTM and CNN_LSTM_AVAILABLE:
    # Load CNN-LSTM models
    try:
        cnn_lstm_binary, cnn_lstm_multiclass = load_cnn_lstm_models(MODELS_DIR)
        if not cnn_lstm_binary or not cnn_lstm_multiclass:
            print("⚠️  CNN-LSTM models not found. Falling back to SVM.")
            USE_CNN_LSTM = False
    except Exception as e:
        print(f"❌ Error loading CNN-LSTM models: {e}")
        print("Falling back to SVM models.")
        USE_CNN_LSTM = False

if not USE_CNN_LSTM or not CNN_LSTM_AVAILABLE:
    # Load SVM models
    print("Loading SVM models...")
    models_binary = joblib.load(MODELS_DIR / "gesture_classifier_binary.pkl")
    scaler_binary = joblib.load(MODELS_DIR / "feature_scaler_binary.pkl")
    features_binary = joblib.load(MODELS_DIR / "feature_names_binary.pkl")
    models_multiclass = joblib.load(MODELS_DIR / "gesture_classifier_multiclass.pkl")
    scaler_multiclass = joblib.load(MODELS_DIR / "feature_scaler_multiclass.pkl")
    features_multiclass = joblib.load(MODELS_DIR / "feature_names_multiclass.pkl")
    print("✅ SVM models loaded\n")


# --- Worker Coroutines ---
async def distributor(sensor_queues, state):
    """Async distributor that streams sensor data to queues"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((LISTEN_IP, LISTEN_PORT))
    sock.setblocking(False)

    rate_tracker = deque(maxlen=100)
    latest_accel = {"x": 0, "y": 0, "z": 0}
    latest_gyro = {"x": 0, "y": 0, "z": 0}

    while True:
        try:
            data, _ = sock.recvfrom(2048)
            msg = json.loads(data.decode())
            sensor_type, values = msg.get("sensor"), msg.get("values", {})

            if sensor_type == "linear_acceleration":
                latest_accel = values
            elif sensor_type == "gyroscope":
                latest_gyro = values
            else:
                await asyncio.sleep(0)
                continue

            combined_reading = {
                "accel_x": latest_accel.get("x", 0),
                "accel_y": latest_accel.get("y", 0),
                "accel_z": latest_accel.get("z", 0),
                "gyro_x": latest_gyro.get("x", 0),
                "gyro_y": latest_gyro.get("y", 0),
                "gyro_z": latest_gyro.get("z", 0),
            }

            # Stream to all queues without blocking
            for q in sensor_queues:
                if q.qsize() < q.maxsize:
                    await q.put(combined_reading)

            now = time.time()
            rate_tracker.append(now)
            state.last_watch_data_time = now
            if len(rate_tracker) > 1:
                state.sensor_data_rate = len(rate_tracker) / (
                    rate_tracker[-1] - rate_tracker[0]
                )
        except BlockingIOError:
            await asyncio.sleep(0.001)
        except (json.JSONDecodeError, KeyError):
            await asyncio.sleep(0)
            continue


async def predictor_cnn_lstm(
    sensor_queue,
    result_queue,
    predictor,
    state,
    pred_type,
):
    """Async predictor using CNN-LSTM models"""
    prediction_history = deque(maxlen=CONSENSUS_WINDOW)

    while True:
        try:
            reading = await asyncio.wait_for(sensor_queue.get(), timeout=1.0)
            
            # Add reading to predictor buffer
            predictor.add_reading(reading)
            
            # Only predict when buffer is full
            if predictor.is_ready():
                gesture, confidence, probs = predictor.predict()
                
                if pred_type == "loco":
                    state.last_locomotion_pred = (gesture, confidence)
                else:
                    state.last_action_pred = (gesture, confidence)
                
                if confidence >= ML_CONFIDENCE_THRESHOLD:
                    # INSTANT ACTIONS: punch/jump/turns execute immediately!
                    if pred_type == "action" and gesture in [
                        "punch",
                        "jump",
                        "turn_left",
                        "turn_right",
                    ]:
                        if result_queue.qsize() < result_queue.maxsize:
                            await result_queue.put((gesture, confidence))
                        prediction_history.clear()
                    elif pred_type == "loco":
                        # Locomotion requires consensus for stability
                        prediction_history.append(gesture)
                        if (
                            len(prediction_history) == CONSENSUS_WINDOW
                            and len(set(prediction_history)) == 1
                        ):
                            if result_queue.qsize() < result_queue.maxsize:
                                await result_queue.put((gesture, confidence))
                            prediction_history.clear()
        except asyncio.TimeoutError:
            await asyncio.sleep(0)
            continue


async def predictor_svm(
    sensor_queue,
    result_queue,
    model,
    scaler,
    feature_names,
    classes,
    window_size,
    state,
    pred_type,
):
    """Async predictor using SVM models"""
    buffer = deque(maxlen=window_size)
    prediction_history = deque(maxlen=CONSENSUS_WINDOW)

    while True:
        try:
            reading = await asyncio.wait_for(sensor_queue.get(), timeout=1.0)
            buffer.append(reading)

            if len(buffer) == window_size:
                features_dict = extract_features_from_dataframe(
                    pd.DataFrame(list(buffer))
                )
                features_vec = np.array(
                    [features_dict.get(name, 0) for name in feature_names]
                ).reshape(1, -1)
                features_scaled = scaler.transform(features_vec)
                probs = model.predict_proba(features_scaled)[0]
                confidence, gesture_idx = probs.max(), probs.argmax()
                gesture = classes[gesture_idx]

                if pred_type == "loco":
                    state.last_locomotion_pred = (gesture, confidence)
                else:
                    state.last_action_pred = (gesture, confidence)

                if confidence >= ML_CONFIDENCE_THRESHOLD:
                    if pred_type == "action" and gesture in [
                        "punch",
                        "jump",
                        "turn_left",
                        "turn_right",
                    ]:
                        if result_queue.qsize() < result_queue.maxsize:
                            await result_queue.put((gesture, confidence))
                        prediction_history.clear()
                    elif pred_type == "loco":
                        prediction_history.append(gesture)
                        if (
                            len(prediction_history) == CONSENSUS_WINDOW
                            and len(set(prediction_history)) == 1
                        ):
                            if result_queue.qsize() < result_queue.maxsize:
                                await result_queue.put((gesture, confidence))
                            prediction_history.clear()
        except asyncio.TimeoutError:
            await asyncio.sleep(0)
            continue


async def actor(locomotion_queue, action_queue, state):
    """Async actor that streams actions to keyboard"""
    keyboard = Controller()
    is_walking = False
    facing_direction = "right"
    last_action_time = {}
    last_walk_confirmation = time.time()
    WALK_TIMEOUT = 0.8
    pressed_keys = set()

    try:
        while True:
            now = time.time()

            facing_direction, is_walking = await handle_action(
                action_queue,
                keyboard,
                facing_direction,
                is_walking,
                last_action_time,
                state,
                pressed_keys,
            )

            is_walking, facing_direction, walk_confirmed = await handle_locomotion(
                locomotion_queue,
                keyboard,
                is_walking,
                facing_direction,
                state,
                pressed_keys,
            )

            if walk_confirmed:
                last_walk_confirmation = now

            if is_walking and (now - last_walk_confirmation) > WALK_TIMEOUT:
                is_walking = False
                for direction in ["left", "right"]:
                    if direction in pressed_keys:
                        keyboard.release(KEY_MAP[direction])
                        pressed_keys.discard(direction)
                state.current_actor_state = "Idle (timeout)"
                print(f"{Colors.YELLOW}⏱️  Walk timeout - auto-stopping{Colors.RESET}")

            await asyncio.sleep(0.02)
    finally:
        for key in pressed_keys:
            try:
                keyboard.release(KEY_MAP.get(key, key))
            except Exception:
                pass


async def handle_locomotion(
    locomotion_queue, keyboard, is_walking, facing_direction, state, pressed_keys
):
    """Handle locomotion commands from queue"""
    walk_confirmed = False

    if not ENABLE_LOCOMOTION:
        while True:
            try:
                locomotion_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        return is_walking, facing_direction, walk_confirmed

    latest_gesture = None
    while True:
        try:
            latest_gesture, _ = locomotion_queue.get_nowait()
        except asyncio.QueueEmpty:
            break

    if latest_gesture:
        state_changed = False

        if (latest_gesture == "noise" or latest_gesture == "idle") and is_walking:
            is_walking = False
            for direction in ["left", "right"]:
                if direction in pressed_keys:
                    keyboard.release(KEY_MAP[direction])
                    pressed_keys.discard(direction)
            state_changed = True
        elif latest_gesture == "walk" and not is_walking:
            is_walking = True
            key = KEY_MAP[facing_direction]
            keyboard.press(key)
            pressed_keys.add(facing_direction)
            state_changed = True
            walk_confirmed = True
        elif latest_gesture == "walk" and is_walking:
            walk_confirmed = True

        if state_changed:
            state.current_actor_state = (
                f"Walking {facing_direction}" if is_walking else "Idle"
            )

    return is_walking, facing_direction, walk_confirmed


async def handle_action(
    action_queue,
    keyboard,
    facing_direction,
    is_walking,
    last_action_time,
    state,
    pressed_keys,
):
    """Handle action commands from queue"""
    latest_gesture = None
    latest_confidence = 0.0
    while True:
        try:
            latest_gesture, latest_confidence = action_queue.get_nowait()
        except asyncio.QueueEmpty:
            break

    if not ENABLE_ACTIONS:
        return facing_direction, is_walking

    if latest_gesture:
        if latest_gesture == "noise":
            return facing_direction, is_walking

        now = time.time()

        if latest_gesture in ["turn_left", "turn_right"]:
            new_direction = latest_gesture.split("_")[1]
            if facing_direction != new_direction:
                old_direction = facing_direction
                facing_direction = new_direction

                print(
                    f"{Colors.CYAN}🔄 Turned to face {facing_direction}!{Colors.RESET}"
                )

                if is_walking:
                    if old_direction in pressed_keys:
                        keyboard.release(KEY_MAP[old_direction])
                        pressed_keys.discard(old_direction)
                    keyboard.press(KEY_MAP[facing_direction])
                    pressed_keys.add(facing_direction)
                    state.current_actor_state = f"Walking {facing_direction}"
                else:
                    state.current_actor_state = f"Facing {facing_direction}"

        elif latest_gesture in ["jump", "punch"]:
            cooldown = last_action_time.get(latest_gesture, 0)
            cooldown_time = 0.1 if latest_gesture == "punch" else 0.2

            if now - cooldown > cooldown_time:
                if is_walking:
                    is_walking = False
                    for direction in ["left", "right"]:
                        if direction in pressed_keys:
                            keyboard.release(KEY_MAP[direction])
                            pressed_keys.discard(direction)
                    print(
                        f"{Colors.CYAN}🛑 Stopped walking to perform action{Colors.RESET}"
                    )

                if latest_gesture == "jump":
                    if ENABLE_KEYBOARD_OUTPUT:
                        keyboard.press(KEY_MAP["jump"])
                        keyboard.release(KEY_MAP["jump"])
                    print(f"{Colors.GREEN}⬆️  JUMP!{Colors.RESET}")
                elif latest_gesture == "punch":
                    if ENABLE_KEYBOARD_OUTPUT:
                        keyboard.press(KEY_MAP["attack"])
                        keyboard.release(KEY_MAP["attack"])
                    print(f"{Colors.RED}👊 PUNCH!{Colors.RESET}")

                last_action_time[latest_gesture] = now
                state.current_actor_state = f"{latest_gesture.capitalize()}!"
            else:
                remaining = cooldown_time - (now - cooldown)
                print(
                    f"{Colors.YELLOW}⏳ {latest_gesture} on cooldown ({remaining*1000:.0f}ms){Colors.RESET}"
                )

    return facing_direction, is_walking


async def dashboard(state, queues):
    """Async dashboard display"""
    while True:
        state.watch_connected = (time.time() - state.last_watch_data_time) < 2.0
        os.system("cls" if os.name == "nt" else "clear")
        print(
            f"{Colors.BOLD}{Colors.CYAN}{'='*60}\n      Silksong ML Controller - Live Dashboard\n{'='*60}{Colors.RESET}"
        )
        watch_status = (
            f"{Colors.GREEN}✓ CONNECTED{Colors.RESET}"
            if state.watch_connected
            else f"{Colors.RED}✗ DISCONNECTED{Colors.RESET}"
        )
        print(
            f"\n{Colors.BOLD}Watch Status: {watch_status}  |  Data Rate: {state.sensor_data_rate:.1f} Hz"
        )
        print(f"Model: {Colors.CYAN}{state.model_type}{Colors.RESET}")
        
        loco_pred, loco_conf = state.last_locomotion_pred
        act_pred, act_conf = state.last_action_pred
        print(f"\n{Colors.BOLD}--- LATEST PREDICTION (Live) ---{Colors.RESET}")
        print(
            f"Locomotion : {Colors.YELLOW}{loco_pred.upper():<12}{Colors.RESET} (Conf: {loco_conf:.0%})"
        )
        print(
            f"Action     : {Colors.YELLOW}{act_pred.upper():<12}{Colors.RESET} (Conf: {act_conf:.0%})"
        )
        print(f"\n{Colors.BOLD}--- CONTROLLER STATE ---{Colors.RESET}")
        print(f"Actor State: {Colors.GREEN}{state.current_actor_state}{Colors.RESET}")

        print(f"\n{Colors.BOLD}--- SYSTEM TOGGLES ---{Colors.RESET}")
        loco_status = f"{Colors.GREEN}ON{Colors.RESET}" if ENABLE_LOCOMOTION else f"{Colors.RED}OFF{Colors.RESET}"
        action_status = f"{Colors.GREEN}ON{Colors.RESET}" if ENABLE_ACTIONS else f"{Colors.RED}OFF{Colors.RESET}"
        kb_status = f"{Colors.GREEN}ON{Colors.RESET}" if ENABLE_KEYBOARD_OUTPUT else f"{Colors.RED}OFF{Colors.RESET}"
        print(f"Locomotion: {loco_status}  |  Actions: {action_status}  |  Keyboard: {kb_status}")

        print(f"\n{Colors.BOLD}--- INTERNAL QUEUES ---{Colors.RESET}")
        print(
            f"Locomotion Results: {queues['result_loco'].qsize()}  |  Action Results: {queues['result_action'].qsize()}"
        )
        print(f"\n{Colors.BOLD}Press Ctrl+C to stop.{Colors.RESET}")
        await asyncio.sleep(0.2)


async def main_async():
    shared_state = SharedState()

    queues = {
        "sensor_loco": asyncio.Queue(500),
        "sensor_action": asyncio.Queue(200),
        "result_loco": asyncio.Queue(10),
        "result_action": asyncio.Queue(10),
    }

    aiozc = AsyncZeroconf()
    service_info = ServiceInfo(
        "_silksong._udp.local.",
        "SilksongController._silksong._udp.local.",
        addresses=[socket.inet_aton(LISTEN_IP)],
        port=LISTEN_PORT,
    )

    try:
        await aiozc.async_register_service(service_info)
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Service registration skipped: {e}{Colors.RESET}")

    try:
        # Create predictor tasks based on model type
        if USE_CNN_LSTM and CNN_LSTM_AVAILABLE:
            tasks = [
                distributor([queues["sensor_loco"], queues["sensor_action"]], shared_state),
                predictor_cnn_lstm(
                    queues["sensor_loco"],
                    queues["result_loco"],
                    cnn_lstm_binary,
                    shared_state,
                    "loco",
                ),
                predictor_cnn_lstm(
                    queues["sensor_action"],
                    queues["result_action"],
                    cnn_lstm_multiclass,
                    shared_state,
                    "action",
                ),
                actor(queues["result_loco"], queues["result_action"], shared_state),
                dashboard(shared_state, queues),
            ]
        else:
            tasks = [
                distributor([queues["sensor_loco"], queues["sensor_action"]], shared_state),
                predictor_svm(
                    queues["sensor_loco"],
                    queues["result_loco"],
                    models_binary,
                    scaler_binary,
                    features_binary,
                    BINARY_CLASSES,
                    250,
                    shared_state,
                    "loco",
                ),
                predictor_svm(
                    queues["sensor_action"],
                    queues["result_action"],
                    models_multiclass,
                    scaler_multiclass,
                    features_multiclass,
                    MULTI_CLASSES,
                    75,
                    shared_state,
                    "action",
                ),
                actor(queues["result_loco"], queues["result_action"], shared_state),
                dashboard(shared_state, queues),
            ]

        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        await aiozc.async_unregister_service(service_info)
        await aiozc.async_close()
        print("✅ Controller stopped.")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
