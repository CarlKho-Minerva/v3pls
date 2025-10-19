#!/usr/bin/env python3
"""
Silksong ML Controller with Real-time Dashboard (FINAL, STATE-AWARE ACTOR)

- Implements correct stateful logic for walking direction.
- Turn gestures now set a direction state instead of being treated as actions.
- Action queue correctly filters idle predictions.
- Robust, non-blocking, and ready for gameplay.
"""
import socket
import json
import time
import os
import threading
from queue import Queue, Empty
from collections import deque
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from pynput.keyboard import Controller, Key
from zeroconf import ServiceInfo, Zeroconf
import sys

# --- Import local modules ---
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared_utils"))
import network_utils


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
        self.lock = threading.Lock()
        self.watch_connected = False
        self.last_watch_data_time = 0
        self.sensor_data_rate = 0.0
        self.last_locomotion_pred = ("-", 0.0)
        self.last_action_pred = ("-", 0.0)
        self.current_actor_state = "Idle"


# --- Configuration & Setup ---
config = network_utils.setup_config()
LISTEN_IP, LISTEN_PORT = (
    config["network"]["listen_ip"],
    config["network"]["listen_port"],
)
KEY_MAP = {"left": Key.left, "right": Key.right, "jump": "z", "attack": "x"}
ML_CONFIDENCE_THRESHOLD = 0.60  # Slightly increased for more reliable actions

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
BINARY_CLASSES, MULTI_CLASSES = ["walk", "idle"], [
    "jump",
    "punch",
    "turn_left",
    "turn_right",
    "idle",
]

# --- Model Loading ---
models_binary = joblib.load(MODELS_DIR / "gesture_classifier_binary.pkl")
scaler_binary = joblib.load(MODELS_DIR / "feature_scaler_binary.pkl")
features_binary = joblib.load(MODELS_DIR / "feature_names_binary.pkl")
models_multiclass = joblib.load(MODELS_DIR / "gesture_classifier_multiclass.pkl")
scaler_multiclass = joblib.load(MODELS_DIR / "feature_scaler_multiclass.pkl")
features_multiclass = joblib.load(MODELS_DIR / "feature_names_multiclass.pkl")


def extract_features_from_dataframe(df):
    """
    Extract features from a DataFrame containing sensor readings.

    Args:
        df: DataFrame with columns: accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z

    Returns:
        Dictionary of extracted features
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


# --- Worker Threads ---
class Distributor(threading.Thread):
    def __init__(self, stop_event, queues, state):
        super().__init__()
        self.stop_event, self.queues, self.state = stop_event, queues, state
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((LISTEN_IP, LISTEN_PORT))
        self.sock.settimeout(1.0)
        self.rate_tracker = deque(maxlen=100)
        self.latest_accel = {"x": 0, "y": 0, "z": 0}
        self.latest_gyro = {"x": 0, "y": 0, "z": 0}

    def run(self):
        while not self.stop_event.is_set():
            try:
                data, _ = self.sock.recvfrom(2048)
                msg = json.loads(data.decode())
                sensor_type, values = msg.get("sensor"), msg.get("values", {})
                if sensor_type == "linear_acceleration":
                    self.latest_accel = values
                elif sensor_type == "gyroscope":
                    self.latest_gyro = values
                else:
                    continue
                combined_reading = {
                    "accel_x": self.latest_accel.get("x", 0),
                    "accel_y": self.latest_accel.get("y", 0),
                    "accel_z": self.latest_accel.get("z", 0),
                    "gyro_x": self.latest_gyro.get("x", 0),
                    "gyro_y": self.latest_gyro.get("y", 0),
                    "gyro_z": self.latest_gyro.get("z", 0),
                }
                for q in self.queues:
                    if not q.full():
                        q.put(combined_reading)
                now = time.time()
                self.rate_tracker.append(now)
                with self.state.lock:
                    self.state.last_watch_data_time = now
                    if len(self.rate_tracker) > 1:
                        self.state.sensor_data_rate = len(self.rate_tracker) / (
                            self.rate_tracker[-1] - self.rate_tracker[0]
                        )
            except (socket.timeout, json.JSONDecodeError, KeyError):
                continue


class Predictor(threading.Thread):
    def __init__(
        self,
        stop_event,
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
        super().__init__()
        self.stop_event, self.sensor_queue, self.result_queue = (
            stop_event,
            sensor_queue,
            result_queue,
        )
        self.model, self.scaler, self.feature_names = model, scaler, feature_names
        self.classes, self.window_size, self.state, self.pred_type = (
            classes,
            window_size,
            state,
            pred_type,
        )
        self.buffer = deque(maxlen=window_size)
        self.prediction_history = deque(maxlen=3)

    def run(self):
        while not self.stop_event.is_set():
            try:
                self.buffer.append(self.sensor_queue.get(timeout=1.0))
                if len(self.buffer) == self.window_size:
                    features_dict = extract_features_from_dataframe(
                        pd.DataFrame(list(self.buffer))
                    )
                    features_vec = np.array(
                        [features_dict.get(name, 0) for name in self.feature_names]
                    ).reshape(1, -1)
                    features_scaled = self.scaler.transform(features_vec)
                    probs = self.model.predict_proba(features_scaled)[0]
                    confidence, gesture_idx = probs.max(), probs.argmax()
                    gesture = self.classes[gesture_idx]
                    with self.state.lock:
                        if self.pred_type == "loco":
                            self.state.last_locomotion_pred = (gesture, confidence)
                        else:
                            self.state.last_action_pred = (gesture, confidence)
                    if confidence >= ML_CONFIDENCE_THRESHOLD:
                        self.prediction_history.append(gesture)
                        if (
                            len(self.prediction_history) == 3
                            and len(set(self.prediction_history)) == 1
                        ):
                            if not self.result_queue.full():
                                self.result_queue.put((gesture, confidence))
                            self.prediction_history.clear()
            except Empty:
                continue


class Actor(threading.Thread):
    def __init__(self, stop_event, locomotion_queue, action_queue, state):
        super().__init__()
        self.stop_event, self.loco_q, self.action_q, self.state = (
            stop_event,
            locomotion_queue,
            action_queue,
            state,
        )
        self.keyboard = Controller()
        self.is_walking = False
        self.facing_direction = "right"  # Start by facing right
        self.last_action_time = {}

    def run(self):
        while not self.stop_event.is_set():
            # IMPORTANT: Process actions FIRST to update direction state
            self.handle_action()
            # THEN, process locomotion based on the (potentially new) direction
            self.handle_locomotion()
            time.sleep(0.02)
        # Cleanup
        self.keyboard.release(Key.left)
        self.keyboard.release(Key.right)

    def handle_locomotion(self):
        try:
            gesture, _ = self.loco_q.get_nowait()
            state_changed = False
            if gesture == "walk" and not self.is_walking:
                self.is_walking = True
                self.keyboard.press(KEY_MAP[self.facing_direction])
                state_changed = True
            elif gesture == "idle" and self.is_walking:
                self.is_walking = False
                self.keyboard.release(KEY_MAP["left"])
                self.keyboard.release(KEY_MAP["right"])
                state_changed = True

            if state_changed:
                with self.state.lock:
                    self.state.current_actor_state = (
                        f"Walking {self.facing_direction}"
                        if self.is_walking
                        else "Idle"
                    )
        except Empty:
            pass

    def handle_action(self):
        try:
            gesture, confidence = self.action_q.get_nowait()
            now = time.time()

            # --- NEW LOGIC STARTS HERE ---

            # 1. Handle STATE changes (turns) immediately. No cooldown.
            if gesture in ["turn_left", "turn_right"]:
                new_direction = gesture.split("_")[1]
                if self.facing_direction != new_direction:
                    if self.is_walking:
                        self.keyboard.release(KEY_MAP[self.facing_direction])
                        self.keyboard.press(KEY_MAP[new_direction])
                    self.facing_direction = new_direction
                    with self.state.lock:
                        self.state.current_actor_state = (
                            f"Walking {self.facing_direction}"
                            if self.is_walking
                            else f"Facing {self.facing_direction}"
                        )
                return  # We are done, exit the function.

            # 2. Filter out 'idle' predictions from the action queue.
            if gesture == "idle":
                return

            # 3. Apply a DEBOUNCE/COOLDOWN for discrete actions (jump, punch).
            # This prevents erratic, rapid-fire actions.
            action_cooldown = 0.5  # Cooldown of 0.5 seconds
            if now - self.last_action_time.get(gesture, 0) < action_cooldown:
                return  # Action is on cooldown, ignore it.

            # If not on cooldown, execute and update the timestamp.
            self.last_action_time[gesture] = now

            if gesture == "jump":
                self.keyboard.press(KEY_MAP["jump"])
                time.sleep(0.05)
                self.keyboard.release(KEY_MAP["jump"])
            elif gesture == "punch":
                self.keyboard.press(KEY_MAP["attack"])
                time.sleep(0.05)
                self.keyboard.release(KEY_MAP["attack"])

        except Empty:
            pass


def main():
    shared_state = SharedState()
    stop_event = threading.Event()
    queues = {
        "sensor_loco": Queue(500),
        "sensor_action": Queue(200),
        "result_loco": Queue(10),
        "result_action": Queue(10),
    }
    zeroconf = Zeroconf()
    service_info = ServiceInfo(
        "_silksong._udp.local.",
        f"SilksongController._silksong._udp.local.",
        addresses=[socket.inet_aton(LISTEN_IP)],
        port=LISTEN_PORT,
    )
    zeroconf.register_service(service_info)
    threads = [
        Distributor(
            stop_event, [queues["sensor_loco"], queues["sensor_action"]], shared_state
        ),
        Predictor(
            stop_event,
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
        Predictor(
            stop_event,
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
        Actor(stop_event, queues["result_loco"], queues["result_action"], shared_state),
    ]
    for t in threads:
        t.start()
    try:
        while True:
            with shared_state.lock:
                shared_state.watch_connected = (
                    time.time() - shared_state.last_watch_data_time
                ) < 2.0
                os.system("cls" if os.name == "nt" else "clear")
                print(
                    f"{Colors.BOLD}{Colors.CYAN}{'='*60}\n      Silksong ML Controller - Live Dashboard\n{'='*60}{Colors.RESET}"
                )
                watch_status = (
                    f"{Colors.GREEN}✓ CONNECTED{Colors.RESET}"
                    if shared_state.watch_connected
                    else f"{Colors.RED}✗ DISCONNECTED{Colors.RESET}"
                )
                print(
                    f"\n{Colors.BOLD}Watch Status: {watch_status}  |  Data Rate: {shared_state.sensor_data_rate:.1f} Hz"
                )
                loco_pred, loco_conf = shared_state.last_locomotion_pred
                act_pred, act_conf = shared_state.last_action_pred
                print(f"\n{Colors.BOLD}--- LATEST PREDICTION (Live) ---{Colors.RESET}")
                print(
                    f"Locomotion : {Colors.YELLOW}{loco_pred.upper():<12}{Colors.RESET} (Conf: {loco_conf:.0%})"
                )
                print(
                    f"Action     : {Colors.YELLOW}{act_pred.upper():<12}{Colors.RESET} (Conf: {act_conf:.0%})"
                )
                print(f"\n{Colors.BOLD}--- CONTROLLER STATE ---{Colors.RESET}")
                print(
                    f"Actor State: {Colors.GREEN}{shared_state.current_actor_state}{Colors.RESET}"
                )
                print(f"\n{Colors.BOLD}--- INTERNAL QUEUES ---{Colors.RESET}")
                print(
                    f"Locomotion Results: {queues['result_loco'].qsize()}  |  Action Results: {queues['result_action'].qsize()}"
                )
                print(f"\n{Colors.BOLD}Press Ctrl+C to stop.{Colors.RESET}")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        stop_event.set()
        [t.join() for t in threads]
        zeroconf.unregister_service(service_info)
        zeroconf.close()
        print("✅ Controller stopped.")


if __name__ == "__main__":
    main()
