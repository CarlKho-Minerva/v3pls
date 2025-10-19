#!/usr/bin/env python3
"""
Silksong ML Controller with Real-time Dashboard (FINAL - SYNCHRONIZED)

- NEW: Distributor now performs timestamp-based synchronization to ensure
  that each data point sent to predictors contains perfectly matched
  accelerometer and gyroscope readings from the same time window. This
  fixes the race condition and matches the training data structure.
- Pure multi-threading architecture.
- Correctly imports shared utilities.
- State-aware parallel Actor for responsive controls.
- Live dashboard for real-time monitoring.
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

# --- Correctly add shared_utils to the path ---
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shared_utils"))
)
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
ML_CONFIDENCE_THRESHOLD = 0.60

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

# --- Worker Threads ---


class Distributor(threading.Thread):
    """
    Receives raw sensor packets and distributes perfectly synchronized
    (accel + gyro) readings to the predictor queues.
    """

    def __init__(self, stop_event, queues, state):
        super().__init__(daemon=True)
        self.stop_event, self.queues, self.state = stop_event, queues, state
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((LISTEN_IP, LISTEN_PORT))
        self.sock.settimeout(1.0)
        self.rate_tracker = deque(maxlen=100)

        # --- NEW SYNCHRONIZATION LOGIC ---
        self.micro_buffer = {}  # Key: timestamp, Value: {'accel':..., 'gyro':...}
        self.TIME_WINDOW_NS = 20 * 1_000_000  # 20ms window

    def run(self):
        while not self.stop_event.is_set():
            try:
                data, _ = self.sock.recvfrom(2048)
                msg = json.loads(data.decode())

                sensor_type = msg.get("sensor")
                values = msg.get("values", {})
                timestamp_ns = msg.get("timestamp_ns")

                if not timestamp_ns:
                    continue

                # Group by time window
                window_key = (timestamp_ns // self.TIME_WINDOW_NS) * self.TIME_WINDOW_NS

                if window_key not in self.micro_buffer:
                    self.micro_buffer[window_key] = {}

                if sensor_type == "linear_acceleration":
                    self.micro_buffer[window_key]["accel"] = values
                elif sensor_type == "gyroscope":
                    self.micro_buffer[window_key]["gyro"] = values

                # Check if we have a complete, synchronized reading
                if (
                    "accel" in self.micro_buffer[window_key]
                    and "gyro" in self.micro_buffer[window_key]
                ):
                    accel_data = self.micro_buffer[window_key]["accel"]
                    gyro_data = self.micro_buffer[window_key]["gyro"]

                    combined_reading = {
                        "accel_x": accel_data.get("x", 0),
                        "accel_y": accel_data.get("y", 0),
                        "accel_z": accel_data.get("z", 0),
                        "gyro_x": gyro_data.get("x", 0),
                        "gyro_y": gyro_data.get("y", 0),
                        "gyro_z": gyro_data.get("z", 0),
                    }

                    for q in self.queues:
                        if not q.full():
                            q.put(combined_reading)

                    # Update dashboard stats
                    now = time.time()
                    self.rate_tracker.append(now)
                    with self.state.lock:
                        self.state.last_watch_data_time = now
                        if len(self.rate_tracker) > 1:
                            self.state.sensor_data_rate = len(self.rate_tracker) / (
                                self.rate_tracker[-1] - self.rate_tracker[0]
                            )

                    # Clean up old buffer entries
                    del self.micro_buffer[window_key]
                    if len(self.micro_buffer) > 100:
                        oldest_key = min(self.micro_buffer.keys())
                        del self.micro_buffer[oldest_key]

            except (socket.timeout, json.JSONDecodeError, KeyError):
                continue


# The rest of the classes (Predictor, Actor, Dashboard) remain the same


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
        super().__init__(daemon=True)
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
        super().__init__(daemon=True)
        self.stop_event, self.loco_q, self.action_q, self.state = (
            stop_event,
            locomotion_queue,
            action_queue,
            state,
        )
        self.keyboard = Controller()
        self.movement_state, self.currently_held_key = "idle", None
        self.last_discrete_action_time = {}
        self.DISCRETE_ACTION_COOLDOWN = 0.5

    def run(self):
        while not self.stop_event.is_set():
            self.process_locomotion_queue()
            self.process_action_queue()
            self.update_held_keys()
            with self.state.lock:
                self.state.current_actor_state = self.movement_state.replace(
                    "_", " "
                ).title()
            time.sleep(0.02)
        if self.currently_held_key:
            self.keyboard.release(self.currently_held_key)

    def process_locomotion_queue(self):
        try:
            gesture, _ = self.loco_q.get_nowait()
            if gesture == "walk" and self.movement_state == "idle":
                self.movement_state = f"walking_{self.get_facing_direction()}"
            elif gesture == "idle":
                self.movement_state = "idle"
        except Empty:
            pass

    def process_action_queue(self):
        try:
            gesture, _ = self.action_q.get_nowait()
            now = time.time()
            if gesture in ["turn_left", "turn_right"]:
                direction = gesture.split("_")[1]
                if self.movement_state.startswith("walking"):
                    self.movement_state = f"walking_{direction}"
                return
            if gesture in ["jump", "punch"]:
                if (
                    now - self.last_discrete_action_time.get(gesture, 0)
                    < self.DISCRETE_ACTION_COOLDOWN
                ):
                    return
                self.last_discrete_action_time[gesture] = now
                key = KEY_MAP["jump"] if gesture == "jump" else KEY_MAP["attack"]
                threading.Thread(
                    target=self.press_and_release, args=(key, 0.1), daemon=True
                ).start()
        except Empty:
            pass

    def update_held_keys(self):
        desired_key = None
        if self.movement_state == "walking_left":
            desired_key = KEY_MAP["left"]
        elif self.movement_state == "walking_right":
            desired_key = KEY_MAP["right"]
        if self.currently_held_key != desired_key:
            if self.currently_held_key:
                self.keyboard.release(self.currently_held_key)
            if desired_key:
                self.keyboard.press(desired_key)
            self.currently_held_key = desired_key

    def get_facing_direction(self):
        if self.movement_state.endswith("left"):
            return "left"
        return "right"

    def press_and_release(self, key, duration):
        self.keyboard.press(key)
        time.sleep(duration)
        self.keyboard.release(key)


class Dashboard(threading.Thread):
    def __init__(self, stop_event, state, queues):
        super().__init__(daemon=True)
        self.stop_event, self.state, self.queues = stop_event, state, queues

    def run(self):
        while not self.stop_event.is_set():
            with self.state.lock:
                self.state.watch_connected = (
                    time.time() - self.state.last_watch_data_time
                ) < 2.0
                os.system("cls" if os.name == "nt" else "clear")
                print(
                    f"{Colors.BOLD}{Colors.CYAN}{'='*60}\n      Silksong ML Controller - Live Dashboard (SYNC)\n{'='*60}{Colors.RESET}"
                )
                watch_status = (
                    f"{Colors.GREEN}✓ CONNECTED{Colors.RESET}"
                    if self.state.watch_connected
                    else f"{Colors.RED}✗ DISCONNECTED{Colors.RESET}"
                )
                print(
                    f"\n{Colors.BOLD}Watch Status: {watch_status}  |  Synced Data Rate: {self.state.sensor_data_rate:.1f} Hz"
                )
                loco_pred, loco_conf = self.state.last_locomotion_pred
                act_pred, act_conf = self.state.last_action_pred
                print(f"\n{Colors.BOLD}--- LATEST PREDICTION (Live) ---{Colors.RESET}")
                print(
                    f"Locomotion : {Colors.YELLOW}{loco_pred.upper():<12}{Colors.RESET} (Conf: {loco_conf:.0%})"
                )
                print(
                    f"Action     : {Colors.YELLOW}{act_pred.upper():<12}{Colors.RESET} (Conf: {act_conf:.0%})"
                )
                print(f"\n{Colors.BOLD}--- CONTROLLER STATE ---{Colors.RESET}")
                print(
                    f"Actor State: {Colors.GREEN}{self.state.current_actor_state}{Colors.RESET}"
                )
                print(f"\n{Colors.BOLD}--- INTERNAL QUEUES ---{Colors.RESET}")
                print(
                    f"Locomotion Results: {self.queues['result_loco'].qsize()}  |  Action Results: {self.queues['result_action'].qsize()}"
                )
                print(f"\n{Colors.BOLD}Press Ctrl+C to stop.{Colors.RESET}")
            time.sleep(0.2)


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
        Dashboard(stop_event, shared_state, queues),
    ]
    for t in threads:
        t.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        stop_event.set()
        for t in threads:
            t.join(timeout=1.0)
        zeroconf.unregister_service(service_info)
        zeroconf.close()
        print("✅ Controller stopped.")


if __name__ == "__main__":
    main()
