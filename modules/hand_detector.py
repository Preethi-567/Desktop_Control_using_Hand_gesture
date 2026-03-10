"""
Hand Detector Module
Uses MediaPipe Hands for real-time hand landmark detection
"""

import cv2
from typing import Optional, Tuple
import numpy as np


class HandDetector:
    """
    Detects and tracks hand landmarks using MediaPipe Hands.
    Provides 21 3D landmarks per hand in real-time.
    """
    
    def __init__(self, max_num_hands=1, min_detection_confidence=0.7,
                 min_tracking_confidence=0.5, model_complexity=1):
        """
        Initialize MediaPipe Hands detector.
        
        Args:
            max_num_hands: Maximum number of hands to detect
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
            model_complexity: Model complexity (0=lite, 1=full)
        """
        # Delay MediaPipe import to avoid slow startup
        try:
            import mediapipe as mp
            self.mp_hands = mp.solutions.hands
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=max_num_hands,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
                model_complexity=model_complexity
            )
            print("✅ MediaPipe Hands initialized")
        except ImportError as e:
            print(f"❌ MediaPipe not available: {e}")
            self.hands = None
            self.mp_hands = None
            self.mp_drawing = None
            self.mp_drawing_styles = None
        
        self.results = None
        self.hand_detected = False
        
    def detect_hands(self, frame: np.ndarray) -> Tuple[bool, Optional[any]]:
        """
        Detect hands in the given frame.
        
        Args:
            frame: BGR image from webcam
            
        Returns:
            Tuple[bool, Optional[landmarks]]: (hand_detected, hand_landmarks)
        """
        # Check if MediaPipe is available
        if self.hands is None:
            return False, None
        
        # Convert BGR to RGB (MediaPipe uses RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame
        self.results = self.hands.process(rgb_frame)
        
        # Check if hand detected
        if self.results.multi_hand_landmarks:
            self.hand_detected = True
            # Return first hand's landmarks
            return True, self.results.multi_hand_landmarks[0]
        else:
            self.hand_detected = False
            return False, None
    
    def draw_landmarks(self, frame: np.ndarray, landmarks=None) -> np.ndarray:
        """
        Draw hand landmarks and connections on the frame.
        
        Args:
            frame: BGR image
            landmarks: Hand landmarks to draw (uses last detected if None)
            
        Returns:
            np.ndarray: Frame with drawn landmarks
        """
        # Check if MediaPipe drawing is available
        if self.mp_drawing is None:
            return frame
        
        if landmarks is None and self.results and self.results.multi_hand_landmarks:
            landmarks = self.results.multi_hand_landmarks[0]
        
        if landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                landmarks,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style()
            )
        
        return frame
    
    def get_landmark_coordinates(self, landmarks, frame_shape: Tuple[int, int]) -> list:
        """
        Convert normalized landmarks to pixel coordinates.
        
        Args:
            landmarks: MediaPipe hand landmarks
            frame_shape: (height, width) of frame
            
        Returns:
            list: List of (x, y) pixel coordinates for each landmark
        """
        height, width = frame_shape
        coordinates = []
        
        for landmark in landmarks.landmark:
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            coordinates.append((x, y))
        
        return coordinates
    
    def is_hand_detected(self) -> bool:
        """
        Check if a hand is currently detected.
        
        Returns:
            bool: True if hand detected, False otherwise
        """
        return self.hand_detected
    
    def get_handedness(self) -> Optional[str]:
        """
        Get whether detected hand is left or right.
        
        Returns:
            Optional[str]: 'Left' or 'Right', None if no hand detected
        """
        if self.results and self.results.multi_handedness:
            return self.results.multi_handedness[0].classification[0].label
        return None
    
    def release(self):
        """Release MediaPipe resources."""
        if self.hands:
            self.hands.close()


if __name__ == "__main__":
    # Test hand detector with webcam
    print("Hand Detector Module - Testing...")
    
    detector = HandDetector()
    cap = cv2.VideoCapture(0)
    
    print("Press 'q' to quit")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Flip frame for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Detect hands
        detected, landmarks = detector.detect_hands(frame)
        
        # Draw landmarks
        if detected:
            frame = detector.draw_landmarks(frame, landmarks)
            handedness = detector.get_handedness()
            cv2.putText(frame, f"Hand: {handedness}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "No hand detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        cv2.imshow('Hand Detector Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    detector.release()
    print("Test completed")