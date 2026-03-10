"""
Rule-Based Gesture Recognition Module
Detects simple gestures using geometric rules and landmark positions
"""

import numpy as np
from typing import Optional, Dict


class RuleBasedGestureDetector:
    """
    Detects gestures using geometric rules based on finger positions.
    Handles: OpenPalm, Fist, Pinch, Victory, Rock, Index Pointing
    """
    
    def __init__(self, landmark_processor):
        """
        Initialize rule-based gesture detector.
        
        Args:
            landmark_processor: LandmarkProcessor instance for feature extraction
        """
        self.processor = landmark_processor
        self.pinch_threshold = 0.05  # Distance threshold for pinch gesture
        
    def detect_gesture(self, landmarks) -> Optional[str]:
        """
        Detect gesture from hand landmarks using rules.
        
        Args:
            landmarks: MediaPipe hand landmarks
            
        Returns:
            Optional[str]: Detected gesture name or None
        """
        # Get finger states
        finger_states = self.processor.get_finger_states(landmarks)
        
        # Count extended fingers
        extended_count = sum(finger_states.values())
        
        # Check for specific gestures in priority order
        
        # 1. OpenPalm - All fingers extended
        if self._is_open_palm(finger_states):
            return "open_palm"
        
        # 2. Fist - All fingers folded
        if self._is_fist(finger_states):
            return "fist"
        
        # 3. Pinch - Thumb and index close together
        if self._is_pinch(landmarks):
            return "pinch"
        
        # 4. Victory - Index and middle extended, others folded
        if self._is_victory(finger_states):
            return "victory"
        
        # 5. Rock - Index and pinky extended, others folded
        if self._is_rock(finger_states):
            return "rock"
        
        # 6. Index Pointing - Only index extended
        if self._is_index_pointing(finger_states):
            return "index_pointing"
        
        # 7. Thumbs Up - Only thumb extended
        if self._is_thumbs_up(finger_states):
            return "thumbs_up"
        
        # 8. Thumbs Down - Only thumb extended downward
        if self._is_thumbs_down(finger_states, landmarks):
            return "thumbs_down"
        
        # 9. Three Fingers Up - Index, Middle, Ring extended
        if self._is_three_fingers(finger_states):
            return "three_fingers"
        
        # 10. Two Fingers Crossed - Copy
        if self._is_two_fingers_crossed(finger_states, landmarks):
            return "two_crossed"
        
        # 11. One Finger Up - Paste
        if self._is_one_finger_up(finger_states, landmarks):
            return "one_up"
        
        # 12. Palm Up - Undo
        if self._is_palm_up(finger_states, landmarks):
            return "palm_up"
        
        # 13. Palm Down - Close Window
        if self._is_palm_down(finger_states, landmarks):
            return "palm_down"
        
        # 14. Vulcan Salute - New Tab / Context-aware
        if self._is_vulcan_salute(finger_states, landmarks):
            return "vulcan"
        
        return None
    
    def _is_open_palm(self, finger_states: Dict[str, bool]) -> bool:
        """
        Check if hand shows open palm gesture (all fingers extended).
        
        Args:
            finger_states: Dictionary of finger extension states
            
        Returns:
            bool: True if open palm detected
        """
        return all(finger_states.values())
    
    def _is_fist(self, finger_states: Dict[str, bool]) -> bool:
        """
        Check if hand shows fist gesture (all fingers folded).
        
        Args:
            finger_states: Dictionary of finger extension states
            
        Returns:
            bool: True if fist detected
        """
        # All fingers should be folded
        return not any(finger_states.values())
    
    def _is_pinch(self, landmarks) -> bool:
        """
        Check if hand shows pinch gesture (thumb and index close).
        
        Args:
            landmarks: MediaPipe hand landmarks
            
        Returns:
            bool: True if pinch detected
        """
        pinch_distance = self.processor.calculate_pinch_distance(landmarks)
        
        # Get finger states to ensure other fingers are not extended
        finger_states = self.processor.get_finger_states(landmarks)
        
        # Pinch: thumb and index close, middle/ring/pinky can be any state
        return pinch_distance < self.pinch_threshold
    
    def _is_victory(self, finger_states: Dict[str, bool]) -> bool:
        """
        Check if hand shows victory gesture (index and middle extended).
        
        Args:
            finger_states: Dictionary of finger extension states
            
        Returns:
            bool: True if victory detected
        """
        return (finger_states['index'] and 
                finger_states['middle'] and 
                not finger_states['ring'] and 
                not finger_states['pinky'])
    
    def _is_rock(self, finger_states: Dict[str, bool]) -> bool:
        """
        Check if hand shows rock gesture (index and pinky extended).
        
        Args:
            finger_states: Dictionary of finger extension states
            
        Returns:
            bool: True if rock detected
        """
        return (finger_states['index'] and 
                finger_states['pinky'] and 
                not finger_states['middle'] and 
                not finger_states['ring'])
    
    def _is_index_pointing(self, finger_states: Dict[str, bool]) -> bool:
        """
        Check if hand shows pointing gesture (only index extended).
        
        Args:
            finger_states: Dictionary of finger extension states
            
        Returns:
            bool: True if pointing detected
        """
        return (finger_states['index'] and 
                not finger_states['middle'] and 
                not finger_states['ring'] and 
                not finger_states['pinky'])
    
    def _is_thumbs_up(self, finger_states: Dict[str, bool]) -> bool:
        """
        Check if hand shows thumbs up gesture (only thumb extended).
        
        Args:
            finger_states: Dictionary of finger extension states
            
        Returns:
            bool: True if thumbs up detected
        """
        return (finger_states['thumb'] and 
                not finger_states['index'] and 
                not finger_states['middle'] and 
                not finger_states['ring'] and 
                not finger_states['pinky'])
    
    def _is_thumbs_down(self, finger_states: Dict[str, bool], landmarks) -> bool:
        """
        Check if hand shows thumbs down gesture.
        
        Args:
            finger_states: Dictionary of finger extension states
            landmarks: MediaPipe hand landmarks
            
        Returns:
            bool: True if thumbs down detected
        """
        # Get thumb tip and wrist positions
        landmark_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        thumb_tip = landmark_array[4]
        wrist = landmark_array[0]
        
        # Thumb should be below wrist (pointing down)
        thumb_down = thumb_tip[1] > wrist[1]
        
        return (finger_states['thumb'] and 
                not finger_states['index'] and 
                not finger_states['middle'] and 
                not finger_states['ring'] and 
                not finger_states['pinky'] and
                thumb_down)
    
    def _is_three_fingers(self, finger_states: Dict[str, bool]) -> bool:
        """
        Check if hand shows three fingers up (index, middle, ring).
        
        Args:
            finger_states: Dictionary of finger extension states
            
        Returns:
            bool: True if three fingers detected
        """
        return (not finger_states['thumb'] and
                finger_states['index'] and 
                finger_states['middle'] and 
                finger_states['ring'] and 
                not finger_states['pinky'])

    def _is_two_fingers_crossed(self, finger_states: Dict[str, bool], landmarks) -> bool:
        """
        Check if hand shows two fingers crossed (index over middle).
        Used for Copy action.
        
        Args:
            finger_states: Dictionary of finger extension states
            landmarks: MediaPipe hand landmarks
            
        Returns:
            bool: True if two fingers crossed detected
        """
        # Index and middle should be extended, others folded
        if not (finger_states['index'] and finger_states['middle']):
            return False
        if finger_states['ring'] or finger_states['pinky'] or finger_states['thumb']:
            return False
        
        # Check if fingers are close together (crossed)
        landmark_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        index_tip = landmark_array[8]
        middle_tip = landmark_array[12]
        
        # Distance between tips should be small (crossed)
        distance = np.linalg.norm(index_tip - middle_tip)
        return distance < 0.05  # Close together = crossed
    
    def _is_one_finger_up(self, finger_states: Dict[str, bool], landmarks) -> bool:
        """
        Check if hand shows one finger pointing up vertically.
        Used for Paste action.
        
        Args:
            finger_states: Dictionary of finger extension states
            landmarks: MediaPipe hand landmarks
            
        Returns:
            bool: True if one finger up detected
        """
        # Only index should be extended
        if not finger_states['index']:
            return False
        if finger_states['middle'] or finger_states['ring'] or finger_states['pinky']:
            return False
        
        # Check if finger is pointing up (vertical)
        landmark_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        index_tip = landmark_array[8]
        index_base = landmark_array[5]
        
        # Vertical means y-difference is significant
        y_diff = abs(index_tip[1] - index_base[1])
        return y_diff > 0.15  # Pointing up
    
    def _is_palm_up(self, finger_states: Dict[str, bool], landmarks) -> bool:
        """
        Check if hand shows palm facing camera (all fingers up).
        Used for Undo action.
        
        Args:
            finger_states: Dictionary of finger extension states
            landmarks: MediaPipe hand landmarks
            
        Returns:
            bool: True if palm up detected
        """
        # All fingers extended
        if not all(finger_states.values()):
            return False
        
        # Check palm orientation (z-coordinate of palm should be positive)
        landmark_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        wrist = landmark_array[0]
        middle_base = landmark_array[9]
        
        # Palm facing camera means z values are similar
        z_diff = abs(wrist[2] - middle_base[2])
        return z_diff < 0.05  # Palm flat facing camera
    
    def _is_palm_down(self, finger_states: Dict[str, bool], landmarks) -> bool:
        """
        Check if hand shows palm facing down.
        Used for Close Window action.
        
        Args:
            finger_states: Dictionary of finger extension states
            landmarks: MediaPipe hand landmarks
            
        Returns:
            bool: True if palm down detected
        """
        # All fingers extended
        if not all(finger_states.values()):
            return False
        
        # Check if palm is facing down (fingertips below knuckles)
        landmark_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        
        # Average y of fingertips vs knuckles
        fingertips_y = np.mean([landmark_array[i][1] for i in [4, 8, 12, 16, 20]])
        knuckles_y = np.mean([landmark_array[i][1] for i in [2, 5, 9, 13, 17]])
        
        # Palm down = fingertips below knuckles
        return fingertips_y > knuckles_y
    
    def _is_vulcan_salute(self, finger_states: Dict[str, bool], landmarks) -> bool:
        """
        Check if hand shows Vulcan salute (index+middle together, ring+pinky together, split).
        Used for New Tab / Context-aware action.
        
        Args:
            finger_states: Dictionary of finger extension states
            landmarks: MediaPipe hand landmarks
            
        Returns:
            bool: True if Vulcan salute detected
        """
        # All fingers except thumb should be extended
        if not (finger_states['index'] and finger_states['middle'] and 
                finger_states['ring'] and finger_states['pinky']):
            return False
        
        landmark_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        
        # Check distance between middle and ring (should be larger = split)
        middle_tip = landmark_array[12]
        ring_tip = landmark_array[16]
        split_distance = np.linalg.norm(middle_tip - ring_tip)
        
        # Check distance between index and middle (should be small = together)
        index_tip = landmark_array[8]
        together_distance = np.linalg.norm(index_tip - middle_tip)
        
        return split_distance > 0.08 and together_distance < 0.05
    
    def get_gesture_info(self, gesture_name: str) -> Dict:
        """
        Get information about a detected gesture.
        
        Args:
            gesture_name: Name of the gesture
            
        Returns:
            Dict: Gesture information (description, emoji, etc.)
        """
        gesture_info = {
            "open_palm": {
                "description": "Open Palm - All fingers extended",
                "emoji": "🖐️",
                "category": "mode_control"
            },
            "fist": {
                "description": "Fist - All fingers closed",
                "emoji": "✊",
                "category": "mouse_action"
            },
            "pinch": {
                "description": "Pinch - Thumb and index together",
                "emoji": "🤏",
                "category": "mouse_action"
            },
            "victory": {
                "description": "Victory - Index and middle extended",
                "emoji": "✌️",
                "category": "mouse_action"
            },
            "rock": {
                "description": "Rock - Index and pinky extended",
                "emoji": "🤘",
                "category": "mouse_action"
            },
            "index_pointing": {
                "description": "Pointing - Index finger extended",
                "emoji": "👉",
                "category": "mouse_control"
            },
            "thumbs_up": {
                "description": "Thumbs Up - Activate action mode",
                "emoji": "👍",
                "category": "mode_control"
            },
            "thumbs_down": {
                "description": "Thumbs Down - Deactivate action mode",
                "emoji": "👎",
                "category": "mode_control"
            },
            "three_fingers": {
                "description": "Three Fingers - Enter mouse mode",
                "emoji": "✋",
                "category": "mode_control"
            },
            "two_crossed": {
                "description": "Two Fingers Crossed - Copy",
                "emoji": "🤞",
                "category": "productivity"
            },
            "one_up": {
                "description": "One Finger Up - Paste",
                "emoji": "☝️",
                "category": "productivity"
            },
            "palm_up": {
                "description": "Palm Up - Undo",
                "emoji": "🫴",
                "category": "productivity"
            },
            "palm_down": {
                "description": "Palm Down - Close Window",
                "emoji": "🫳",
                "category": "productivity"
            },
            "vulcan": {
                "description": "Vulcan Salute - New Tab (Context-aware)",
                "emoji": "🖖",
                "category": "productivity"
            }
        }
        
        return gesture_info.get(gesture_name, {
            "description": "Unknown gesture",
            "emoji": "❓",
            "category": "unknown"
        })


if __name__ == "__main__":
    # Test rule-based gesture detection
    print("Rule-Based Gesture Detector Module - Ready")
    print("\nDetectable Gestures:")
    
    detector = RuleBasedGestureDetector(None)
    
    gestures = ["open_palm", "fist", "pinch", "victory", "rock", "index_pointing"]
    
    for gesture in gestures:
        info = detector.get_gesture_info(gesture)
        print(f"  {info['emoji']} {gesture}: {info['description']}")