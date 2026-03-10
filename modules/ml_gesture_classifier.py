"""
ML Gesture Classifier Module
Uses TensorFlow Lite model for custom gesture recognition (IMAGE-BASED)
"""

import tensorflow as tf
import numpy as np
import cv2
from typing import Tuple, Optional, List
import os


class MLGestureClassifier:
    """
    Classifies hand gestures using a trained TensorFlow Lite model.
    Handles custom gestures: ShakaSign, FingerHeart, L-Shape, Super
    
    THIS VERSION USES IMAGE INPUT (for Teachable Machine models)
    """
    
    def __init__(self, model_path: str, labels_path: str, confidence_threshold: float = 0.80):
        """
        Initialize ML gesture classifier.
        
        Args:
            model_path: Path to model.tflite file
            labels_path: Path to labels.txt file
            confidence_threshold: Minimum confidence for valid prediction
        """
        self.model_path = model_path
        self.labels_path = labels_path
        self.confidence_threshold = confidence_threshold
        
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.labels = []
        self.input_shape = None
        
        self._load_model()
        self._load_labels()
        
    def _load_model(self):
        """Load TensorFlow Lite model."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        try:
            # Load TFLite model
            self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
            self.interpreter.allocate_tensors()
            
            # Get input and output details
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            # Get expected input shape
            self.input_shape = self.input_details[0]['shape']
            
            print(f"✅ Model loaded: {self.model_path}")
            print(f"   Input shape: {self.input_shape}")
            print(f"   Output shape: {self.output_details[0]['shape']}")
            print(f"   ⚠️  Using IMAGE-BASED classification (Teachable Machine)")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")
    
    def _load_labels(self):
        """Load gesture class labels."""
        if not os.path.exists(self.labels_path):
            raise FileNotFoundError(f"Labels file not found: {self.labels_path}")
        
        try:
            with open(self.labels_path, 'r') as f:
                self.labels = [line.strip() for line in f.readlines()]
            
            print(f"✅ Labels loaded: {len(self.labels)} classes")
            print(f"   Classes: {', '.join(self.labels)}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load labels: {e}")
    
    def _preprocess_hand_image(self, frame: np.ndarray, landmarks) -> Optional[np.ndarray]:
        """
        Extract and preprocess hand region from frame.
        
        Args:
            frame: Full camera frame (BGR)
            landmarks: MediaPipe hand landmarks
            
        Returns:
            np.ndarray: Preprocessed image ready for model (224x224x3)
        """
        try:
            h, w, _ = frame.shape
            
            # Get bounding box of hand
            x_coords = [lm.x for lm in landmarks.landmark]
            y_coords = [lm.y for lm in landmarks.landmark]
            
            x_min = int(min(x_coords) * w)
            x_max = int(max(x_coords) * w)
            y_min = int(min(y_coords) * h)
            y_max = int(max(y_coords) * h)
            
            # Add padding (20%)
            padding_x = int((x_max - x_min) * 0.2)
            padding_y = int((y_max - y_min) * 0.2)
            
            x_min = max(0, x_min - padding_x)
            x_max = min(w, x_max + padding_x)
            y_min = max(0, y_min - padding_y)
            y_max = min(h, y_max + padding_y)
            
            # Crop hand region
            hand_img = frame[y_min:y_max, x_min:x_max]
            
            if hand_img.size == 0:
                return None
            
            # Resize to model input size (usually 224x224)
            target_size = (self.input_shape[1], self.input_shape[2])
            hand_img = cv2.resize(hand_img, target_size)
            
            # Convert BGR to RGB (Teachable Machine uses RGB)
            hand_img = cv2.cvtColor(hand_img, cv2.COLOR_BGR2RGB)
            
            # Normalize to [0, 1] range
            hand_img = hand_img.astype(np.float32) / 255.0
            
            # Add batch dimension
            hand_img = np.expand_dims(hand_img, axis=0)
            
            return hand_img
            
        except Exception as e:
            print(f"❌ Preprocessing error: {e}")
            return None
    
    def classify(self, frame: np.ndarray, landmarks) -> Tuple[Optional[str], float]:
        """
        Classify gesture from camera frame and landmarks.
        
        Args:
            frame: Full camera frame (BGR image)
            landmarks: MediaPipe hand landmarks
            
        Returns:
            Tuple[Optional[str], float]: (gesture_name, confidence) or (None, 0.0)
        """
        if self.interpreter is None:
            return None, 0.0
        
        try:
            # Preprocess hand image
            preprocessed = self._preprocess_hand_image(frame, landmarks)
            
            if preprocessed is None:
                return None, 0.0
            
            # Set input tensor
            self.interpreter.set_tensor(self.input_details[0]['index'], preprocessed)
            
            # Run inference
            self.interpreter.invoke()
            
            # Get output
            output = self.interpreter.get_tensor(self.output_details[0]['index'])
            predictions = output[0]
            
            # Get top prediction
            max_index = np.argmax(predictions)
            confidence = float(predictions[max_index])
            
            # Check confidence threshold
            if confidence >= self.confidence_threshold:
                gesture_name = self.labels[max_index]
                return gesture_name, confidence
            else:
                return None, confidence
                
        except Exception as e:
            print(f"❌ Classification error: {e}")
            return None, 0.0
    
    def get_all_predictions(self, frame: np.ndarray, landmarks) -> List[Tuple[str, float]]:
        """
        Get all gesture predictions with their confidences.
        
        Args:
            frame: Full camera frame
            landmarks: MediaPipe hand landmarks
            
        Returns:
            List[Tuple[str, float]]: List of (gesture_name, confidence) sorted by confidence
        """
        if self.interpreter is None:
            return []
        
        try:
            # Preprocess hand image
            preprocessed = self._preprocess_hand_image(frame, landmarks)
            
            if preprocessed is None:
                return []
            
            # Set input and run inference
            self.interpreter.set_tensor(self.input_details[0]['index'], preprocessed)
            self.interpreter.invoke()
            
            # Get output
            output = self.interpreter.get_tensor(self.output_details[0]['index'])
            predictions = output[0]
            
            # Create list of (label, confidence) tuples
            results = [(self.labels[i], float(predictions[i])) 
                      for i in range(len(self.labels))]
            
            # Sort by confidence (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return []
    
   
    
    def is_model_loaded(self) -> bool:
        """
        Check if model is successfully loaded.
        
        Returns:
            bool: True if model loaded
        """
        return self.interpreter is not None and len(self.labels) > 0


if __name__ == "__main__":
    # Test ML gesture classifier
    print("ML Gesture Classifier Module - Testing...")
    
    try:
        # Try to load model (will fail if files don't exist)
        classifier = MLGestureClassifier(
            model_path="models/model.tflite",
            labels_path="models/labels.txt"
        )
        
        print(f"\n✅ Classifier ready")
        print(f"   Confidence threshold: {classifier.confidence_threshold}")
        print(f"   Expected input: {classifier.input_shape}")
        
        # Test with dummy image
        import cv2
        dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        print("\n📊 Test requires actual hand landmarks from MediaPipe")
        print("   Run main.py to test with real hand detection")
        
    except FileNotFoundError as e:
        print(f"\n⚠️  {e}")
        print("   Please provide model.tflite and labels.txt in models/ directory")
    except Exception as e:
        print(f"\n❌ Error: {e}")