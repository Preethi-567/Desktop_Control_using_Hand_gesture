"""
Safety Layer Module
Implements temporal smoothing and false positive prevention for gesture recognition
"""

from collections import deque
import time


class SafetyLayer:
    """
    Prevents false activations through temporal smoothing and confidence thresholding.
    Implements a sliding window buffer to validate gesture consistency across multiple frames.
    """
    
    def __init__(self, window_size=9, required_detections=6, confidence_threshold=0.87):
        """
        Initialize safety layer with temporal smoothing parameters.
        
        Args:
            window_size: Size of temporal window in frames (default: 9)
            required_detections: Minimum detections in window for valid gesture (default: 6)
                                This means gesture must be detected in 6 out of 9 frames
            confidence_threshold: Minimum confidence for acceptance (default: 0.87)
        """
        self.window_size = window_size
        self.required_detections = required_detections
        self.confidence_threshold = confidence_threshold
        self.last_stable_gesture = None
        self.gesture_change_frames = 0
        self.required_change_frames = 4
        self.dynamic_threshold = confidence_threshold

        # Sliding window buffers for gesture history
        self.gesture_buffer = deque(maxlen=window_size)
        self.confidence_buffer = deque(maxlen=window_size)
        
        # Timestamp tracking for rate limiting
        self.last_gesture_time = {}
        self.min_time_between_same_gesture = 0.5  # seconds
        
        print(f"🛡️  Safety Layer initialized:")
        print(f"   Window size: {window_size} frames")
        print(f"   Required detections: {required_detections}/{window_size}")
        print(f"   Confidence threshold: {confidence_threshold:.2%}")
    
    def add_detection(self, gesture: str, confidence: float):
        """
        Add a gesture detection to the temporal buffer.
        
        Args:
            gesture: Detected gesture name (e.g., "fist", "thumbs_up")
            confidence: Detection confidence score (0.0 to 1.0)
        """
        self.gesture_buffer.append(gesture)
        self.confidence_buffer.append(confidence)
    
    def is_gesture_stable(self, gesture: str) -> bool:
        """
        Check if a specific gesture is stable (detected consistently).
        
        A gesture is considered stable if it appears in at least 
        'required_detections' frames within the current window.
        
        Args:
            gesture: Gesture name to check
            
        Returns:
            bool: True if gesture is stable and consistent
        """
        # Need minimum frames before validation
        if len(self.gesture_buffer) < self.required_detections:
            return False
        
        # Count occurrences of target gesture in buffer
        count = sum(1 for g in self.gesture_buffer if g == gesture)
        
        # Check if meets required detection threshold
        return count >= self.required_detections
    
    def get_stable_gesture(self) -> tuple:
        """
        Get the most stable gesture with confidence validation.
        
        This method:
        1. Finds the most frequently detected gesture in the buffer
        2. Verifies it meets the required detection count
        3. Checks average confidence meets threshold
        4. Implements rate limiting to prevent rapid re-detection
        
        Returns:
            tuple: (gesture_name, average_confidence) or (None, 0.0) if no stable gesture
        """
        # Need minimum frames for validation
        if len(self.gesture_buffer) < self.required_detections:
            return None, 0.0
        
        # Update dynamic threshold based on average confidence
        if len(self.confidence_buffer) > 0:
            avg_conf = sum(self.confidence_buffer) / len(self.confidence_buffer)
            if avg_conf < 0.75:
                self.dynamic_threshold = 0.75
            elif avg_conf > 0.9:
                self.dynamic_threshold = 0.9
        
        # Count gesture occurrences in buffer
        gesture_counts = {}
        for gesture in self.gesture_buffer:
            if gesture:  # Ignore None values
                gesture_counts[gesture] = gesture_counts.get(gesture, 0) + 1
        
        # Return None if no gestures detected
        if not gesture_counts:
            return None, 0.0
        
        # Find gesture with highest count
        stable_gesture = max(gesture_counts, key=gesture_counts.get)
        
        # Verify meets required detection threshold
        if gesture_counts[stable_gesture] < self.required_detections:
            return None, 0.0
        
        # Calculate average confidence for this gesture
        confidences = [
            conf for g, conf in zip(self.gesture_buffer, self.confidence_buffer) 
            if g == stable_gesture
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Check confidence threshold
        if avg_confidence < self.dynamic_threshold:
            return None, avg_confidence
        
        # Gesture change debouncing
        if stable_gesture != self.last_stable_gesture:
            self.gesture_change_frames += 1
            if self.gesture_change_frames < self.required_change_frames:
                return None, avg_confidence
        else:
            self.gesture_change_frames = 0

        self.last_stable_gesture = stable_gesture
        
        # Rate limiting: prevent same gesture from triggering too frequently
        current_time = time.time()
        last_time = self.last_gesture_time.get(stable_gesture, 0)
        
        if current_time - last_time < self.min_time_between_same_gesture:
            # Gesture detected too soon after previous detection
            return None, avg_confidence
        
        # Update timestamp for rate limiting
        self.last_gesture_time[stable_gesture] = current_time
        
        return stable_gesture, avg_confidence
    
    def get_gesture_statistics(self) -> dict:
        """
        Get detailed statistics about current gesture buffer.
        Useful for debugging and performance monitoring.
        
        Returns:
            dict: Statistics including gesture counts, confidences, and stability metrics
        """
        if not self.gesture_buffer:
            return {
                'buffer_size': 0,
                'gestures': {},
                'avg_confidence': 0.0,
                'most_common': None
            }
        
        # Count gesture occurrences
        gesture_counts = {}
        for gesture in self.gesture_buffer:
            if gesture:
                gesture_counts[gesture] = gesture_counts.get(gesture, 0) + 1
        
        # Calculate statistics
        stats = {
            'buffer_size': len(self.gesture_buffer),
            'gestures': gesture_counts,
            'avg_confidence': sum(self.confidence_buffer) / len(self.confidence_buffer),
            'most_common': max(gesture_counts, key=gesture_counts.get) if gesture_counts else None
        }
        
        return stats
    
    def reset(self):
        """
        Clear all buffers and reset safety layer state.
        
        Called when:
        - Hand is no longer detected
        - Mode transition occurs
        - Gesture is successfully executed
        - System needs to clear pending state
        """
        self.gesture_buffer.clear()
        self.confidence_buffer.clear()
    
    def reset_rate_limit(self, gesture: str = None):
        """
        Reset rate limiting timer for specific gesture or all gestures.
        
        Args:
            gesture: Specific gesture to reset, or None to reset all
        """
        if gesture:
            if gesture in self.last_gesture_time:
                del self.last_gesture_time[gesture]
        else:
            self.last_gesture_time.clear()
    
    def set_parameters(self, window_size: int = None, 
                      required_detections: int = None,
                      confidence_threshold: float = None):
        """
        Update safety layer parameters dynamically.
        
        Args:
            window_size: New window size (updates buffer max length)
            required_detections: New required detection count
            confidence_threshold: New confidence threshold
        """
        if window_size is not None:
            self.window_size = window_size
            # Create new buffers with updated size
            old_gestures = list(self.gesture_buffer)
            old_confidences = list(self.confidence_buffer)
            self.gesture_buffer = deque(old_gestures[-window_size:], maxlen=window_size)
            self.confidence_buffer = deque(old_confidences[-window_size:], maxlen=window_size)
        
        if required_detections is not None:
            self.required_detections = required_detections
        
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold
        
        print(f"🛡️  Safety Layer parameters updated:")
        print(f"   Window: {self.window_size}, Required: {self.required_detections}, "
              f"Confidence: {self.confidence_threshold:.2%}")
    
    def get_buffer_status(self) -> str:
        """
        Get human-readable status of current buffer state.
        
        Returns:
            str: Status description
        """
        if not self.gesture_buffer:
            return "Empty buffer"
        
        stats = self.get_gesture_statistics()
        most_common = stats['most_common']
        
        if most_common:
            count = stats['gestures'][most_common]
            return f"{most_common}: {count}/{self.window_size} frames ({stats['avg_confidence']:.1%} confidence)"
        
        return "No stable gesture"
    
    def is_buffer_full(self) -> bool:
        """
        Check if buffer has reached maximum capacity.
        
        Returns:
            bool: True if buffer is full
        """
        return len(self.gesture_buffer) >= self.window_size
    
    def get_stability_score(self, gesture: str) -> float:
        """
        Calculate stability score for a specific gesture (0.0 to 1.0).
        
        Score combines:
        - Detection frequency in buffer
        - Average confidence
        - Consistency over time
        
        Args:
            gesture: Gesture name to evaluate
            
        Returns:
            float: Stability score between 0.0 and 1.0
        """
        if not self.gesture_buffer:
            return 0.0
        
        # Count occurrences
        count = sum(1 for g in self.gesture_buffer if g == gesture)
        frequency_score = count / len(self.gesture_buffer)
        
        # Calculate average confidence for this gesture
        confidences = [
            conf for g, conf in zip(self.gesture_buffer, self.confidence_buffer) 
            if g == gesture
        ]
        confidence_score = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Combine scores (weighted average)
        stability = (frequency_score * 0.6) + (confidence_score * 0.4)
        
        return stability


if __name__ == "__main__":
    """Test safety layer functionality."""
    print("=" * 60)
    print("🛡️  Safety Layer Module - Testing")
    print("=" * 60)
    
    # Initialize safety layer
    safety = SafetyLayer(window_size=9, required_detections=6, confidence_threshold=0.87)
    
    print("\n📋 Test 1: Adding detections")
    print("-" * 40)
    
    # Simulate gesture detections
    test_gestures = [
        ("thumbs_up", 0.92),
        ("thumbs_up", 0.89),
        ("open_palm", 0.75),  # Low confidence
        ("thumbs_up", 0.91),
        ("thumbs_up", 0.88),
        ("thumbs_up", 0.93),
        ("thumbs_up", 0.90),
        ("open_palm", 0.80),
        ("thumbs_up", 0.94),
    ]
    
    for gesture, confidence in test_gestures:
        safety.add_detection(gesture, confidence)
        print(f"Added: {gesture} (confidence: {confidence:.2%})")
    
    print(f"\n📊 Buffer status: {safety.get_buffer_status()}")
    
    # Check for stable gesture
    stable_gesture, avg_conf = safety.get_stable_gesture()
    
    if stable_gesture:
        print(f"\n✅ Stable gesture detected: {stable_gesture}")
        print(f"   Average confidence: {avg_conf:.2%}")
    else:
        print(f"\n❌ No stable gesture (confidence too low or insufficient detections)")
    
    # Test statistics
    print("\n📊 Test 2: Buffer Statistics")
    print("-" * 40)
    stats = safety.get_gesture_statistics()
    print(f"Buffer size: {stats['buffer_size']}")
    print(f"Gesture counts: {stats['gestures']}")
    print(f"Average confidence: {stats['avg_confidence']:.2%}")
    print(f"Most common: {stats['most_common']}")
    
    # Test stability scores
    print("\n📈 Test 3: Stability Scores")
    print("-" * 40)
    for gesture in ['thumbs_up', 'open_palm']:
        score = safety.get_stability_score(gesture)
        print(f"{gesture}: {score:.2%}")
    
    # Test reset
    print("\n🔄 Test 4: Reset Buffer")
    print("-" * 40)
    print(f"Before reset: {safety.get_buffer_status()}")
    safety.reset()
    print(f"After reset: {safety.get_buffer_status()}")
    
    # Test parameter updates
    print("\n⚙️  Test 5: Dynamic Parameter Update")
    print("-" * 40)
    safety.set_parameters(window_size=7, required_detections=5, confidence_threshold=0.85)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)