"""
Gesture Logger Module
Logs all gesture detections for debugging and analytics
"""

import os
import csv
import json
from datetime import datetime
from collections import defaultdict


class GestureLogger:
    """Logs gesture detections, executions, and analytics."""
    
    def __init__(self, log_dir='logs'):
        """
        Initialize gesture logger.
        
        Args:
            log_dir: Directory for log files
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Log files
        self.gesture_log = os.path.join(log_dir, 'gestures.csv')
        self.session_log = os.path.join(log_dir, 'session.json')
        self.analytics_log = os.path.join(log_dir, 'analytics.json')
        
        # Session tracking
        self.session_start = datetime.now()
        self.session_id = self.session_start.strftime('%Y%m%d_%H%M%S')
        
        # Analytics counters
        self.gesture_counts = defaultdict(int)
        self.execution_counts = defaultdict(int)
        self.false_positive_count = 0
        self.false_negative_count = 0
        self.total_detections = 0
        self.total_executions = 0
        
        # Performance tracking
        self.detection_times = []
        self.classification_times = []
        
        # Initialize CSV
        self._init_csv()
        
        print(f"📝 Gesture logging initialized")
        print(f"   Session ID: {self.session_id}")
        print(f"   Log directory: {self.log_dir}")
    
    def _init_csv(self):
        """Initialize CSV file with headers."""
        if not os.path.exists(self.gesture_log):
            with open(self.gesture_log, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'session_id',
                    'gesture',
                    'confidence',
                    'executed',
                    'mode',
                    'detection_time_ms',
                    'classification_time_ms',
                    'notes'
                ])
    
    def log_gesture(self, gesture: str, confidence: float, executed: bool, 
                    mode: str, detection_time: float = 0.0, 
                    classification_time: float = 0.0, notes: str = ''):
        """
        Log a gesture detection.
        
        Args:
            gesture: Gesture name
            confidence: Detection confidence (0-1)
            executed: Whether action was executed
            mode: Current system mode
            detection_time: Hand detection time (ms)
            classification_time: Gesture classification time (ms)
            notes: Additional notes
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Write to CSV
        with open(self.gesture_log, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                self.session_id,
                gesture,
                f"{confidence:.4f}",
                executed,
                mode,
                f"{detection_time:.2f}",
                f"{classification_time:.2f}",
                notes
            ])
        
        # Update analytics
        self.total_detections += 1
        self.gesture_counts[gesture] += 1
        if executed:
            self.total_executions += 1
            self.execution_counts[gesture] += 1
        
        # Track performance
        if detection_time > 0:
            self.detection_times.append(detection_time)
        if classification_time > 0:
            self.classification_times.append(classification_time)
    
    def log_false_positive(self, gesture: str, confidence: float, mode: str):
        """Log a false positive detection."""
        self.false_positive_count += 1
        self.log_gesture(
            gesture, confidence, False, mode,
            notes='FALSE_POSITIVE'
        )
    
    def log_false_negative(self, expected_gesture: str, mode: str):
        """Log a missed gesture (false negative)."""
        self.false_negative_count += 1
        self.log_gesture(
            expected_gesture, 0.0, False, mode,
            notes='FALSE_NEGATIVE'
        )
    
    def log_performance(self, detection_ms: float, classification_ms: float):
        """Log performance metrics."""
        self.detection_times.append(detection_ms)
        self.classification_times.append(classification_ms)
    
    def get_statistics(self) -> dict:
        """
        Get current session statistics.
        
        Returns:
            dict: Statistics summary
        """
        avg_detection = sum(self.detection_times) / len(self.detection_times) if self.detection_times else 0
        avg_classification = sum(self.classification_times) / len(self.classification_times) if self.classification_times else 0
        
        execution_rate = (self.total_executions / self.total_detections * 100) if self.total_detections > 0 else 0
        
        stats = {
            'session_id': self.session_id,
            'session_duration': str(datetime.now() - self.session_start),
            'total_detections': self.total_detections,
            'total_executions': self.total_executions,
            'execution_rate': f"{execution_rate:.1f}%",
            'false_positives': self.false_positive_count,
            'false_negatives': self.false_negative_count,
            'gesture_counts': dict(self.gesture_counts),
            'execution_counts': dict(self.execution_counts),
            'avg_detection_time_ms': f"{avg_detection:.2f}",
            'avg_classification_time_ms': f"{avg_classification:.2f}",
            'top_gestures': self._get_top_gestures(5)
        }
        
        return stats
    
    def _get_top_gestures(self, n: int = 5) -> list:
        """Get top N most used gestures."""
        sorted_gestures = sorted(
            self.gesture_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [(g, c) for g, c in sorted_gestures[:n]]
    
    def print_statistics(self):
        """Print session statistics to console."""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("📊 GESTURE LOGGING STATISTICS")
        print("="*60)
        print(f"Session ID: {stats['session_id']}")
        print(f"Duration: {stats['session_duration']}")
        print(f"\nDetections:")
        print(f"  Total: {stats['total_detections']}")
        print(f"  Executed: {stats['total_executions']} ({stats['execution_rate']})")
        print(f"  False Positives: {stats['false_positives']}")
        print(f"  False Negatives: {stats['false_negatives']}")
        
        print(f"\nPerformance:")
        print(f"  Avg Detection Time: {stats['avg_detection_time_ms']}ms")
        print(f"  Avg Classification Time: {stats['avg_classification_time_ms']}ms")
        
        print(f"\nTop Gestures:")
        for i, (gesture, count) in enumerate(stats['top_gestures'], 1):
            executed = self.execution_counts.get(gesture, 0)
            print(f"  {i}. {gesture}: {count} detections ({executed} executed)")
        
        print("="*60)
    
    def save_session_summary(self):
        """Save session summary to JSON."""
        stats = self.get_statistics()
        
        # Save to session log
        with open(self.session_log, 'w') as f:
            json.dump(stats, f, indent=2)
        
        # Append to analytics log (history)
        analytics = []
        if os.path.exists(self.analytics_log):
            with open(self.analytics_log, 'r') as f:
                try:
                    analytics = json.load(f)
                except:
                    analytics = []
        
        analytics.append(stats)
        
        with open(self.analytics_log, 'w') as f:
            json.dump(analytics, f, indent=2)
        
        print(f"💾 Session summary saved: {self.session_log}")
    
    def generate_report(self, output_file='logs/gesture_report.txt'):
        """
        Generate human-readable text report.
        
        Args:
            output_file: Output file path
        """
        stats = self.get_statistics()
        
        report = []
        report.append("="*70)
        report.append("GESTRON - GESTURE DETECTION REPORT")
        report.append("="*70)
        report.append(f"\nSession: {stats['session_id']}")
        report.append(f"Duration: {stats['session_duration']}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        report.append("\n" + "-"*70)
        report.append("DETECTION SUMMARY")
        report.append("-"*70)
        report.append(f"Total Detections:        {stats['total_detections']}")
        report.append(f"Executed Actions:        {stats['total_executions']} ({stats['execution_rate']})")
        report.append(f"False Positives:         {stats['false_positives']}")
        report.append(f"False Negatives:         {stats['false_negatives']}")
        
        report.append("\n" + "-"*70)
        report.append("PERFORMANCE METRICS")
        report.append("-"*70)
        report.append(f"Avg Detection Time:      {stats['avg_detection_time_ms']}ms")
        report.append(f"Avg Classification Time: {stats['avg_classification_time_ms']}ms")
        
        report.append("\n" + "-"*70)
        report.append("GESTURE USAGE")
        report.append("-"*70)
        report.append(f"{'Rank':<6} {'Gesture':<20} {'Detections':<12} {'Executed':<10}")
        report.append("-"*70)
        for i, (gesture, count) in enumerate(stats['top_gestures'], 1):
            executed = self.execution_counts.get(gesture, 0)
            report.append(f"{i:<6} {gesture:<20} {count:<12} {executed:<10}")
        
        report.append("\n" + "-"*70)
        report.append("ALL GESTURES")
        report.append("-"*70)
        for gesture in sorted(stats['gesture_counts'].keys()):
            count = stats['gesture_counts'][gesture]
            executed = self.execution_counts.get(gesture, 0)
            rate = (executed / count * 100) if count > 0 else 0
            report.append(f"{gesture:<20} {count:>4} detections  {executed:>4} executed ({rate:>5.1f}%)")
        
        report.append("\n" + "="*70)
        
        # Write to file
        with open(output_file, 'w') as f:
            f.write('\n'.join(report))
        
        print(f"📄 Report generated: {output_file}")
        
        return '\n'.join(report)
    
    def cleanup(self):
        """Cleanup and save final statistics."""
        self.print_statistics()
        self.save_session_summary()
        self.generate_report()


if __name__ == "__main__":
    # Test gesture logger
    print("Gesture Logger Module - Testing...")
    
    logger = GestureLogger()
    
    # Simulate some detections
    logger.log_gesture('shaka_sign', 0.93, True, 'gesture_mode', 25.3, 42.1, 'Test detection')
    logger.log_gesture('fist', 0.88, True, 'mouse_mode', 18.5, 35.2)
    logger.log_gesture('victory', 0.75, False, 'gesture_mode', 22.1, 38.9, 'Below threshold')
    logger.log_false_positive('finger_heart', 0.65, 'gesture_mode')
    
    # Print stats
    logger.print_statistics()
    
    # Generate report
    logger.generate_report()
    
    print("\n✅ Gesture logger test completed")