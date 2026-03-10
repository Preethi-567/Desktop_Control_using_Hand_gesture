"""
Landmark Processor Module
Handles normalization and feature extraction from MediaPipe hand landmarks
"""

import numpy as np
from typing import List, Tuple, Optional
import math


class LandmarkProcessor:
    """
    Processes raw hand landmarks from MediaPipe for gesture recognition.
    Performs normalization, feature extraction, and geometric calculations.
    """
    
    def __init__(self):
        """Initialize the landmark processor."""
        self.wrist_index = 0
        self.num_landmarks = 21
        
    def normalize_landmarks(self, landmarks) -> np.ndarray:
        """
        Normalize hand landmarks to be position and scale invariant.
        
        Args:
            landmarks: MediaPipe hand landmarks
            
        Returns:
            np.ndarray: Normalized landmark coordinates (63 features: 21 * 3)
        """
        # Extract landmark coordinates
        landmark_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        
        # Get wrist position (reference point)
        wrist = landmark_array[self.wrist_index]
        
        # Translate so wrist is at origin
        translated = landmark_array - wrist
        
        # Calculate scale (maximum distance from wrist)
        distances = np.linalg.norm(translated, axis=1)
        max_distance = np.max(distances)
        
        # Avoid division by zero
        if max_distance > 0:
            normalized = translated / max_distance
        else:
            normalized = translated
            
        # Flatten to 1D feature vector
        features = normalized.flatten()
        
        return features
    
    def extract_extended_features(self, landmarks) -> np.ndarray:
        """
        Extract additional geometric features for improved classification.
        
        Args:
            landmarks: MediaPipe hand landmarks
            
        Returns:
            np.ndarray: Extended feature vector including angles and distances
        """
        # Get normalized base features
        base_features = self.normalize_landmarks(landmarks)
        
        # Extract fingertip and knuckle indices
        fingertips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        knuckles = [2, 5, 9, 13, 17]
        
        landmark_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        
        # Calculate finger extension status (1 if extended, 0 if folded)
        finger_extensions = []
        for tip, knuckle in zip(fingertips, knuckles):
            tip_pos = landmark_array[tip]
            knuckle_pos = landmark_array[knuckle]
            wrist_pos = landmark_array[0]
            
            # Distance from tip to wrist vs knuckle to wrist
            tip_dist = np.linalg.norm(tip_pos - wrist_pos)
            knuckle_dist = np.linalg.norm(knuckle_pos - wrist_pos)
            
            # If tip is farther than knuckle, finger is extended
            extension = 1.0 if tip_dist > knuckle_dist * 1.1 else 0.0
            finger_extensions.append(extension)
        
        # Calculate inter-fingertip distances
        fingertip_distances = []
        for i in range(len(fingertips)):
            for j in range(i + 1, len(fingertips)):
                pos_i = landmark_array[fingertips[i]]
                pos_j = landmark_array[fingertips[j]]
                dist = np.linalg.norm(pos_i - pos_j)
                fingertip_distances.append(dist)
        
        # Combine all features
        extended_features = np.concatenate([
            base_features,
            np.array(finger_extensions),
            np.array(fingertip_distances)
        ])
        
        return extended_features
    
    def get_finger_states(self, landmarks) -> dict:
        """
        Determine which fingers are extended or folded.
        
        Args:
            landmarks: MediaPipe hand landmarks
            
        Returns:
            dict: Finger states (thumb, index, middle, ring, pinky)
        """
        landmark_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        
        # Fingertip and knuckle indices
        finger_tips = {
            'thumb': 4,
            'index': 8,
            'middle': 12,
            'ring': 16,
            'pinky': 20
        }
        
        finger_knuckles = {
            'thumb': 2,
            'index': 5,
            'middle': 9,
            'ring': 13,
            'pinky': 17
        }
        
        wrist = landmark_array[0]
        states = {}
        
        for finger_name in finger_tips.keys():
            tip_idx = finger_tips[finger_name]
            knuckle_idx = finger_knuckles[finger_name]
            
            tip_pos = landmark_array[tip_idx]
            knuckle_pos = landmark_array[knuckle_idx]
            
            # Calculate distances
            tip_to_wrist = np.linalg.norm(tip_pos - wrist)
            knuckle_to_wrist = np.linalg.norm(knuckle_pos - wrist)
            
            # For thumb, use x-coordinate comparison (horizontal extension)
            if finger_name == 'thumb':
                # Check if thumb is extended away from palm
                states[finger_name] = abs(tip_pos[0] - wrist[0]) > abs(knuckle_pos[0] - wrist[0]) * 1.2
            else:
                # For other fingers, use y-coordinate (vertical extension)
                states[finger_name] = tip_pos[1] < knuckle_pos[1]
        
        return states
    
    def calculate_pinch_distance(self, landmarks) -> float:
        """
        Calculate distance between thumb tip and index finger tip.
        Used for pinch gesture detection.
        
        Args:
            landmarks: MediaPipe hand landmarks
            
        Returns:
            float: Distance between thumb and index tips (normalized)
        """
        landmark_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        
        thumb_tip = landmark_array[4]
        index_tip = landmark_array[8]
        
        distance = np.linalg.norm(thumb_tip - index_tip)
        return distance
    
    def get_index_fingertip_position(self, landmarks, frame_shape: Tuple[int, int]) -> Tuple[int, int]:
        """
        Get screen coordinates of index fingertip for cursor control.
        
        Args:
            landmarks: MediaPipe hand landmarks
            frame_shape: (height, width) of video frame
            
        Returns:
            Tuple[int, int]: (x, y) screen coordinates
        """
        index_tip = landmarks.landmark[8]
        
        height, width = frame_shape
        x = int(index_tip.x * width)
        y = int(index_tip.y * height)
        
        return (x, y)
    
    def calculate_hand_center(self, landmarks, frame_shape: Tuple[int, int]) -> Tuple[int, int]:
        """
        Calculate the center point of the hand for visualization.
        
        Args:
            landmarks: MediaPipe hand landmarks
            frame_shape: (height, width) of video frame
            
        Returns:
            Tuple[int, int]: (x, y) center coordinates
        """
        landmark_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        
        center = np.mean(landmark_array, axis=0)
        
        height, width = frame_shape
        x = int(center[0] * width)
        y = int(center[1] * height)
        
        return (x, y)
    
    def calculate_angle_between_fingers(self, landmarks, finger1_tip: int, 
                                       finger2_tip: int, base_point: int = 0) -> float:
        """
        Calculate angle between two fingers from a base point.
        
        Args:
            landmarks: MediaPipe hand landmarks
            finger1_tip: Index of first fingertip
            finger2_tip: Index of second fingertip
            base_point: Index of base point (default: wrist)
            
        Returns:
            float: Angle in degrees
        """
        landmark_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        
        base = landmark_array[base_point]
        finger1 = landmark_array[finger1_tip]
        finger2 = landmark_array[finger2_tip]
        
        # Vectors from base to fingertips
        vec1 = finger1 - base
        vec2 = finger2 - base
        
        # Calculate angle using dot product
        cos_angle = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-6)
        angle = math.degrees(math.acos(np.clip(cos_angle, -1.0, 1.0)))
        
        return angle


if __name__ == "__main__":
    # Test landmark processor
    print("Landmark Processor Module - Ready")
    processor = LandmarkProcessor()
    print(f"Initialized with {processor.num_landmarks} landmarks")