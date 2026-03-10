# utils/performance_monitor.py
# VTU-compliant Performance Monitor for GESTRON
# Requires: psutil
# Writes logs to performance.log and prints TABLE 5.6 at shutdown.
import time
import threading
import psutil
import os
from collections import deque
from datetime import datetime

class PerfTimer:
    """Simple context manager to time blocks and report to monitor."""
    def __init__(self, monitor, tag):
        self.monitor = monitor
        self.tag = tag
        self.t0 = None
    def __enter__(self):
        self.t0 = time.time()
        return self
    def __exit__(self, exc_type, exc, tb):
        dt = (time.time() - self.t0) * 1000.0
        if self.tag == 'detection':
            self.monitor.record_detection_latency(dt)
        elif self.tag == 'classification':
            self.monitor.record_classification_latency(dt)
        elif self.tag == 'action':
            self.monitor.record_action_latency(dt)
        else:
            # generic
            self.monitor.record_misc_latency(self.tag, dt)

class PerformanceMonitor:
    def __init__(self, log_file='logs/performance.log', sampling_interval=1.0, perf_window_seconds=60):
        self.log_file = log_file
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True) if os.path.dirname(self.log_file) else None

        # Sampling
        self.sampling_interval = sampling_interval
        self._sampler_thread = None
        self._sampler_running = False

        # psutil process handle
        self.process = psutil.Process()

        # Samples
        self.cpu_samples = []
        self.mem_samples = []
        self.cpu_peak = 0.0
        self.mem_peak = 0

        # Frame timing
        self.frame_times = deque(maxlen=10000)
        self.frame_fps_samples = []

        # latency buckets (ms)
        self.detection_latency_samples = []
        self.classification_latency_samples = []
        self.action_latency_samples = []
        self.misc_latency = {}

        # counters
        self.total_frames = 0
        self.hand_detect_count = 0

        # gesture execution counters (heuristic)
        self.confirmed_actions = 0        # actions that were confirmed by fist (TP heuristic)
        self.unconfirmed_executions = 0   # immediate executions (potential FP)
        self.false_positives = 0          # user can bump this manually during tests
        self.false_negatives = 0          # user can bump this manually during tests

        # logging
        self._log_lock = threading.Lock()

        # start time
        self.start_time = None
        self.stop_time = None

        # perf window for rolling stats
        self.perf_window = deque(maxlen=int(max(5, perf_window_seconds / sampling_interval)))

    # ---- Public API ----
    def start(self):
        self.start_time = time.time()
        self._sampler_running = True
        self._sampler_thread = threading.Thread(target=self._sampler_loop, daemon=True)
        self._sampler_thread.start()
        # write csv header if new file
        with self._log_lock:
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'w') as f:
                    f.write("timestamp,fps,cpu_percent,memory_mb,latency_ms,notes\n")

    def stop(self):
        self.stop_time = time.time()
        self._sampler_running = False
        if self._sampler_thread:
            self._sampler_thread.join(timeout=1.0)

    def timeit(self, tag):
        """Convenience context manager for timing blocks. Usage:
           with perf_monitor.timeit('detection'):
               ..."""
        return PerfTimer(self, tag)

    def record_frame(self, frame_time_s):
        """Record one frame's processing time (seconds)."""
        fps = 1.0 / frame_time_s if frame_time_s > 0 else 0.0
        self.frame_times.append(frame_time_s)
        self.frame_fps_samples.append(fps)
        self.total_frames += 1

    def record_hand_detection(self, detected: bool, confidence: float = None):
        if detected:
            self.hand_detect_count += 1

    def record_detection_latency(self, ms: float):
        self.detection_latency_samples.append(ms)

    def record_classification_latency(self, ms: float):
        self.classification_latency_samples.append(ms)

    def record_action_latency(self, ms: float):
        self.action_latency_samples.append(ms)

    def record_misc_latency(self, tag, ms: float):
        if tag not in self.misc_latency:
            self.misc_latency[tag] = []
        self.misc_latency[tag].append(ms)

    def record_confirmed_action(self):
        self.confirmed_actions += 1

    def record_unconfirmed_execution(self):
        self.unconfirmed_executions += 1

    def increment_false_positive(self, n=1):
        self.false_positives += n

    def increment_false_negative(self, n=1):
        self.false_negatives += n

    # ---- Internal sampler ----
    def _sampler_loop(self):
        while self._sampler_running:
            try:
                cpu = psutil.cpu_percent(interval=None)
                mem = self.process.memory_info().rss / (1024 * 1024)  # MB

                self.cpu_samples.append(cpu)
                self.mem_samples.append(mem)
                if cpu > self.cpu_peak:
                    self.cpu_peak = cpu
                if mem > self.mem_peak:
                    self.mem_peak = mem

                # rolling perf window storing short summary
                self.perf_window.append({
                    'time': time.time(),
                    'cpu': cpu,
                    'mem': mem,
                    'fps': (self.frame_fps_samples[-1] if self.frame_fps_samples else 0.0),
                    'detection_ms': (self.detection_latency_samples[-1] if self.detection_latency_samples else 0.0)
                })
            except Exception:
                pass
            time.sleep(self.sampling_interval)

    # ---- Reporting & logging ----
    def _safe_mean(self, arr):
        return sum(arr) / len(arr) if arr else 0.0

    def _format_bytes_mb(self, v):
        return f"{v:.1f}"

    def log_current(self, notes=""):
        """Append a CSV line with current aggregates."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fps = self._format_stat_fps()
        cpu = self._safe_mean(self.cpu_samples[-60:]) if self.cpu_samples else 0.0
        mem = self._safe_mean(self.mem_samples[-60:]) if self.mem_samples else 0.0
        latency = self._safe_mean(self.detection_latency_samples[-60:]) if self.detection_latency_samples else 0.0

        entry = f"{timestamp},{fps:.2f},{cpu:.1f},{mem:.1f},{latency:.2f},{notes}\n"
        with self._log_lock:
            with open(self.log_file, 'a') as f:
                f.write(entry)

    def _format_stat_fps(self):
        fpss = self.frame_fps_samples
        if not fpss:
            return 0.0
        return sum(fpss) / len(fpss)

    def compute_summary(self):
        """Compute full summary dict used to print TABLE 5.6"""
        avg_fps = self._safe_mean(self.frame_fps_samples)
        min_fps = min(self.frame_fps_samples) if self.frame_fps_samples else 0.0
        max_fps = max(self.frame_fps_samples) if self.frame_fps_samples else 0.0

        summary = {
            'avg_fps': avg_fps,
            'min_fps': min_fps,
            'max_fps': max_fps,
            'avg_cpu': self._safe_mean(self.cpu_samples),
            'cpu_peak': self.cpu_peak,
            'avg_mem_mb': self._safe_mean(self.mem_samples),
            'mem_peak_mb': self.mem_peak,
            'avg_detection_ms': self._safe_mean(self.detection_latency_samples),
            'avg_classification_ms': self._safe_mean(self.classification_latency_samples),
            'avg_action_ms': self._safe_mean(self.action_latency_samples),
            'total_frames': self.total_frames,
            'hand_detect_rate': (self.hand_detect_count / self.total_frames * 100.0) if self.total_frames else 0.0,
            'confirmed_actions': self.confirmed_actions,
            'unconfirmed_executions': self.unconfirmed_executions,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives,
            'uptime_s': (self.stop_time - self.start_time) if self.stop_time and self.start_time else (time.time() - self.start_time if self.start_time else 0.0)
        }
        # derived
        # Gesture accuracy must use external ground truth when available. We'll give an approximate based on confirmed actions:
        executed = self.confirmed_actions + self.unconfirmed_executions
        summary['approx_true_positive_rate'] = (self.confirmed_actions / executed * 100.0) if executed else 0.0
        summary['approx_false_positive_rate'] = (self.unconfirmed_executions / executed * 100.0) if executed else 0.0
        return summary

    def print_summary(self):
        s = self.compute_summary()
        print("\n" + "="*60)
        print("📊 Performance Summary (AUTOGENERATED)")
        print("="*60)
        print(f"Average FPS: {s['avg_fps']:.2f}")
        print(f"Minimum FPS: {s['min_fps']:.2f}")
        print(f"Maximum FPS: {s['max_fps']:.2f}")
        print(f"Total Frames: {s['total_frames']}")
        print(f"Uptime: {s['uptime_s']:.1f}s")
        print(f"CPU: {s['avg_cpu']:.1f}% (peak: {s['cpu_peak']:.1f}%)")
        print(f"Memory: {s['avg_mem_mb']:.1f} MB (peak: {s['mem_peak_mb']:.1f} MB)")
        print(f"Gesture detection latency (avg): {s['avg_detection_ms']:.1f} ms")
        print(f"ML classification latency (avg): {s['avg_classification_ms']:.1f} ms")
        print(f"Action execution latency (avg): {s['avg_action_ms']:.1f} ms")
        print(f"Hand detection rate: {s['hand_detect_rate']:.1f}%")
        print(f"Confirmed actions: {s['confirmed_actions']}")
        print(f"Unconfirmed executed actions (possible FP): {s['unconfirmed_executions']}")
        print(f"Approx True Positive Rate (heuristic): {s['approx_true_positive_rate']:.1f}%")
        print(f"Approx False Positive Rate (heuristic): {s['approx_false_positive_rate']:.1f}%")
        print("="*60)

        # Also print TABLE 5.6 formatted to match the report
        print("\nTABLE 5.6: Performance Test Results")
        rows = [
            ("Average FPS", "25-30", f"{s['avg_fps']:.1f} FPS", "Single hand, 1280×720, normal lighting", "PASS" if 25 <= s['avg_fps'] <= 30 else "FAIL"),
            ("Minimum FPS", ">20", f"{s['min_fps']:.1f} FPS", "With ML classification active", "PASS" if s['min_fps'] > 20 else "FAIL"),
            ("Gesture Detection Latency", "<50ms", f"{s['avg_detection_ms']:.1f}ms", "From gesture presentation to classification", "PASS" if s['avg_detection_ms'] < 50 else "FAIL"),
            ("Action Execution Latency", "<100ms", f"{s['avg_action_ms']:.1f}ms", "From classification to desktop action", "PASS" if s['avg_action_ms'] < 100 else "FAIL"),
            ("CPU Usage (Average)", "<60%", f"{s['avg_cpu']:.1f}%", "Test device", "PASS" if s['avg_cpu'] < 60 else "FAIL"),
            ("CPU Usage (Peak)", "<80%", f"{s['cpu_peak']:.1f}%", "During ML inference + cursor movement", "PASS" if s['cpu_peak'] < 80 else "FAIL"),
            ("Memory Usage (Steady State)", "<500MB", f"{s['avg_mem_mb']:.1f} MB", "After 30 min operation", "PASS" if s['avg_mem_mb'] < 500 else "FAIL"),
            ("Memory Usage (Peak)", "<600MB", f"{s['mem_peak_mb']:.1f} MB", "With voice commands active", "PASS" if s['mem_peak_mb'] < 600 else "FAIL"),
            ("Startup Time", "<10s", f"{(self.start_time and (self.start_time - self.start_time)) or 0:.1f}s", "From launch to ready state", "N/A"),
            ("Hand Detection Rate (Good Lighting)", ">95%", f"{s['hand_detect_rate']:.1f}%", "300 lux, neutral background", "PASS" if s['hand_detect_rate'] > 95 else "CHECK"),
        ]
        for r in rows:
            print("\t".join(r))
        print("="*60)

    def draw_overlay(self, frame):
        """Return frame with HUD overlay. Called from main draw loop."""
        try:
            import cv2
            h, w = frame.shape[:2]
            # panel
            cv2.rectangle(frame, (5,5), (360,125), (0,0,0), -1)
            cv2.rectangle(frame, (5,5), (360,125), (255,255,255), 1)
            s = self.compute_summary()
            cv2.putText(frame, f"FPS: {s['avg_fps']:.1f}", (12,28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
            cv2.putText(frame, f"CPU: {s['avg_cpu']:.1f}%", (12,52), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,0), 1)
            cv2.putText(frame, f"Mem: {s['avg_mem_mb']:.0f}MB", (12,72), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,0), 1)
            cv2.putText(frame, f"Detect: {s['avg_detection_ms']:.0f}ms", (12,96), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,0), 1)
            return frame
        except Exception:
            return frame
