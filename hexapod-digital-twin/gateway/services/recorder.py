"""
gateway/services/recorder.py

High-performance telemetry recording and replay system:
- In-memory circular/append buffer for live telemetry frames
- Export to JSON and CSV formats
- Replay engine with variable speed (0.5x, 1.0x, 2.0x) and timeline control
"""

from __future__ import annotations

import csv
import json
import os
import time
from typing import Optional, List, Dict, Any

from gateway.models.twin_state import DigitalTwinState


class TelemetryRecorder:
    def __init__(self, recording_dir: str = "recordings", max_records: int = 50000) -> None:
        self.recording_dir = recording_dir
        self.max_records = max_records
        self._recording: bool = False
        self._records: List[Dict[str, Any]] = []
        self._replay_frames: List[Dict[str, Any]] = []
        self._replay_index: int = 0
        self._replay_speed: float = 1.0
        self._replay_active: bool = False
        os.makedirs(self.recording_dir, exist_ok=True)

    def start_recording(self) -> None:
        """Start capturing incoming telemetry frames."""
        self._recording = True
        self._records.clear()

    def stop_recording(self) -> int:
        """Stop capturing and return the number of recorded frames."""
        self._recording = False
        return len(self._records)

    def is_recording(self) -> bool:
        return self._recording

    def record_frame(self, state: DigitalTwinState) -> None:
        """Record a single digital twin state snapshot if recording is enabled."""
        if not self._recording:
            return
        if len(self._records) >= self.max_records:
            return

        snapshot = {
            "timestamp": state.timestamp,
            "pitch": state.orientation.pitch,
            "roll": state.orientation.roll,
            "yaw": state.orientation.yaw,
            "ax": state.imu.raw.ax,
            "ay": state.imu.raw.ay,
            "az": state.imu.raw.az,
            "gx": state.imu.raw.gx,
            "gy": state.imu.raw.gy,
            "gz": state.imu.raw.gz,
            "physical_servo": state.physicalServo.angle,
            "virtual_servos": state.virtualServos,
            "simulated_servos": state.simulatedServos,
            "mode": state.mode,
        }
        self._records.append(snapshot)

    def export_json(self, filename: Optional[str] = None) -> str:
        """Save current records to a JSON file."""
        if not filename:
            filename = f"telemetry_{int(time.time())}.json"
        filepath = os.path.join(self.recording_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._records, f, indent=2)
        return filepath

    def export_csv(self, filename: Optional[str] = None) -> str:
        """Save current records to a CSV file."""
        if not filename:
            filename = f"telemetry_{int(time.time())}.csv"
        filepath = os.path.join(self.recording_dir, filename)
        if not self._records:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                f.write("timestamp,pitch,roll,yaw,ax,ay,az,gx,gy,gz,physical_servo\n")
            return filepath

        fieldnames = [
            "timestamp", "pitch", "roll", "yaw",
            "ax", "ay", "az", "gx", "gy", "gz",
            "physical_servo"
        ]
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in self._records:
                writer.writerow(r)
        return filepath

    def load_replay(self, filepath: str) -> bool:
        """Load a JSON telemetry recording for replay."""
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self._replay_frames = json.load(f)
            self._replay_index = 0
            self._replay_active = False
            return True
        except Exception:
            return False

    def replay_play(self) -> None:
        self._replay_active = True

    def replay_pause(self) -> None:
        self._replay_active = False

    def replay_restart(self) -> None:
        self._replay_index = 0

    def set_replay_speed(self, speed: float) -> None:
        self._replay_speed = max(0.25, min(5.0, speed))

    def replay_tick(self) -> Optional[Dict[str, Any]]:
        """Advance replay timeline and return current frame snapshot."""
        if not self._replay_active or not self._replay_frames:
            return None
        if self._replay_index >= len(self._replay_frames):
            self._replay_active = False
            return None

        frame = self._replay_frames[self._replay_index]
        self._replay_index += int(max(1, round(self._replay_speed)))
        return frame
