
from __future__ import annotations

import csv
import threading
import time
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from audio_engine import AdaptiveAudioEngine
from focus_model import FocusModel
from sensor_hub import SensorHub


class AdaptiveSoundscapesApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Adaptive Soundscapes for Productivity")
        self.root.geometry("980x700")
        self.root.minsize(900, 640)

        self.sensor_hub = SensorHub()
        self.model = FocusModel()
        self.audio = AdaptiveAudioEngine()

        self.running = False
        self.loop_thread = None
        self.session_log = []

        self.task_mode = tk.StringVar(value="Focus")
        self.use_webcam = tk.BooleanVar(value=True)
        self.use_audio = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="Idle")

        self.focus_var = tk.DoubleVar(value=0)
        self.stress_var = tk.DoubleVar(value=0)
        self.engagement_var = tk.DoubleVar(value=0)
        self.rec_var = tk.StringVar(value="-")
        self.reason_var = tk.StringVar(value="-")

        self.typing_var = tk.StringVar(value="0.00")
        self.var_typing_var = tk.StringVar(value="0.00")
        self.mouse_speed_var = tk.StringVar(value="0.00")
        self.click_rate_var = tk.StringVar(value="0.00")
        self.face_var = tk.StringVar(value="0")
        self.gaze_var = tk.StringVar(value="0")
        self.blink_var = tk.StringVar(value="0")
        self.head_var = tk.StringVar(value="0")

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=16)
        top.pack(fill="x")

        ttk.Label(top, text="Adaptive Soundscapes for Productivity", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            top,
            text="Reads live input signals and adapts ambient audio in real time.",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 0))

        controls = ttk.LabelFrame(self.root, text="Controls", padding=14)
        controls.pack(fill="x", padx=16, pady=10)

        ttk.Label(controls, text="Task mode").grid(row=0, column=0, sticky="w")
        mode_box = ttk.Combobox(controls, textvariable=self.task_mode, values=["Focus", "Coding", "Reading", "Relax"], state="readonly", width=14)
        mode_box.grid(row=0, column=1, padx=8, sticky="w")
        mode_box.bind("<<ComboboxSelected>>", lambda e: self.model.set_task_mode(self.task_mode.get()))

        ttk.Checkbutton(controls, text="Use webcam", variable=self.use_webcam).grid(row=0, column=2, padx=16, sticky="w")
        ttk.Checkbutton(controls, text="Enable audio", variable=self.use_audio).grid(row=0, column=3, padx=16, sticky="w")

        ttk.Button(controls, text="Start Monitoring", command=self.start).grid(row=0, column=4, padx=6)
        ttk.Button(controls, text="Stop Monitoring", command=self.stop).grid(row=0, column=5, padx=6)
        ttk.Button(controls, text="Save Session Log", command=self.save_log).grid(row=0, column=6, padx=6)

        ttk.Label(controls, textvariable=self.status_text, font=("Segoe UI", 10, "bold")).grid(row=1, column=0, columnspan=7, sticky="w", pady=(10, 0))

        grid = ttk.Frame(self.root, padding=(16, 6))
        grid.pack(fill="both", expand=True)

        left = ttk.Frame(grid)
        left.pack(side="left", fill="both", expand=True)

        right = ttk.Frame(grid)
        right.pack(side="right", fill="both", expand=True)

        scores = ttk.LabelFrame(left, text="Computed State", padding=14)
        scores.pack(fill="x", pady=6)

        self._add_progress(scores, "Focus", self.focus_var, 0)
        self._add_progress(scores, "Stress", self.stress_var, 1)
        self._add_progress(scores, "Engagement", self.engagement_var, 2)

        ttk.Label(scores, text="Sound profile").grid(row=3, column=0, sticky="w", pady=(10, 0))
        ttk.Label(scores, textvariable=self.rec_var, font=("Segoe UI", 11, "bold")).grid(row=3, column=1, sticky="w", pady=(10, 0))
        ttk.Label(scores, text="Reason").grid(row=4, column=0, sticky="w", pady=(6, 0))
        ttk.Label(scores, textvariable=self.reason_var, wraplength=280).grid(row=4, column=1, sticky="w", pady=(6, 0))

        raw = ttk.LabelFrame(left, text="Raw Live Inputs", padding=14)
        raw.pack(fill="x", pady=6)
        self._kv(raw, "Typing rate (keys/sec)", self.typing_var, 0)
        self._kv(raw, "Typing variability", self.var_typing_var, 1)
        self._kv(raw, "Mouse speed", self.mouse_speed_var, 2)
        self._kv(raw, "Click rate", self.click_rate_var, 3)
        self._kv(raw, "Face present", self.face_var, 4)
        self._kv(raw, "Gaze centered", self.gaze_var, 5)
        self._kv(raw, "Blink rate", self.blink_var, 6)
        self._kv(raw, "Head stability", self.head_var, 7)

        expl = ttk.LabelFrame(right, text="How It Works", padding=14)
        expl.pack(fill="x", pady=6)
        ttk.Label(
            expl,
            text=(
                "This app watches keyboard rhythm, mouse activity, and optional webcam signals.\n\n"
                "It estimates whether you are focused, overloaded, or drifting, then changes the ambient sound profile to match."
            ),
            wraplength=360,
            justify="left",
        ).pack(anchor="w")

        log_frame = ttk.LabelFrame(right, text="Live Session Events", padding=10)
        log_frame.pack(fill="both", expand=True, pady=6)

        self.log_box = tk.Text(log_frame, height=20, wrap="word", state="disabled")
        self.log_box.pack(fill="both", expand=True)

    def _add_progress(self, parent, label, var, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=6)
        bar = ttk.Progressbar(parent, variable=var, maximum=100, length=240)
        bar.grid(row=row, column=1, sticky="w", padx=8)
        ttk.Label(parent, textvariable=var).grid(row=row, column=2, sticky="w")

    def _kv(self, parent, label, var, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Label(parent, textvariable=var, font=("Segoe UI", 10, "bold")).grid(row=row, column=1, sticky="w", padx=10)

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.model.set_task_mode(self.task_mode.get())
        self.sensor_hub.start(use_webcam=self.use_webcam.get())
        if self.use_audio.get():
            print("APP IS TRYING TO START AUDIO")
            try:
                self.audio.start()
            except Exception as exc:
                self._append_log(f"Audio start failed: {exc}")
                self.use_audio.set(False)

        self.status_text.set("Running")
        self._append_log("Monitoring started.")
        self.loop_thread = threading.Thread(target=self._loop, daemon=True)
        self.loop_thread.start()

    def stop(self) -> None:
        if not self.running:
            return
        self.running = False
        self.sensor_hub.stop()
        self.audio.stop()
        self.status_text.set("Stopped")
        self._append_log("Monitoring stopped.")

    def _loop(self) -> None:
        last_profile = None
        while self.running:
            snap = self.sensor_hub.snapshot()
            state = self.model.compute(snap.metrics)

            if self.use_audio.get() and self.audio.is_running():
                self.audio.set_recommendation(state.recommendation, state.focus, state.stress)

            self.session_log.append({
                "timestamp": snap.timestamp,
                **snap.metrics,
                "focus": state.focus,
                "stress": state.stress,
                "engagement": state.engagement,
                "recommendation": state.recommendation,
                "reason": state.reason,
            })

            self.root.after(0, self._update_ui, snap.metrics, state)

            if state.recommendation != last_profile:
                self.root.after(0, self._append_log, f"Profile -> {state.recommendation.upper()} | {state.reason}")
                last_profile = state.recommendation

            time.sleep(0.5)

    def _update_ui(self, metrics, state) -> None:
        self.focus_var.set(round(state.focus, 1))
        self.stress_var.set(round(state.stress, 1))
        self.engagement_var.set(round(state.engagement, 1))
        self.rec_var.set(state.recommendation.upper())
        self.reason_var.set(state.reason)

        self.typing_var.set(f"{metrics.get('typing_rate', 0):.2f}")
        self.var_typing_var.set(f"{metrics.get('typing_variability', 0):.2f}")
        self.mouse_speed_var.set(f"{metrics.get('mouse_speed', 0):.2f}")
        self.click_rate_var.set(f"{metrics.get('mouse_click_rate', 0):.2f}")
        self.face_var.set(f"{metrics.get('face_present', 0):.0f}")
        self.gaze_var.set(f"{metrics.get('gaze_centered', 0):.1f}")
        self.blink_var.set(f"{metrics.get('blink_rate', 0):.1f}")
        self.head_var.set(f"{metrics.get('head_stability', 0):.1f}")

    def _append_log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{timestamp}] {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def save_log(self) -> None:
        if not self.session_log:
            messagebox.showinfo("No data", "There is no session data to save yet.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save session log",
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.session_log[0].keys()))
            writer.writeheader()
            writer.writerows(self.session_log)

        self._append_log(f"Saved session log to {Path(path).name}")

    def on_close(self) -> None:
        self.stop()
        self.root.destroy()
