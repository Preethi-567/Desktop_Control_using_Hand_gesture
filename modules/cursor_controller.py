"""
Cursor Controller Module
Handles smooth mouse cursor movement using Kalman filtering
"""

import numpy as np
import pyautogui
from filterpy.kalman import KalmanFilter
from typing import Tuple
import screeninfo


class CursorController:
    """
    Controls mouse cursor with smooth movement using Kalman filter.
    Prevents jittery cursor movement from hand tracking noise.
    """
    
    def __init__(self, smoothing_method="kalman", speed_multiplier=1.5):
        """
        Initialize cursor controller.
        
        Args:
            smoothing_method: 'kalman' or 'linear'
            speed_multiplier: Cursor movement speed multiplier
        """
        self.smoothing_method = smoothing_method
        self.speed_multiplier = speed_multiplier
        
        # Get screen dimensions
        try:
            monitors = screeninfo.get_monitors()
            primary = monitors[0]
            self.screen_width = primary.width
            self.screen_height = primary.height
        except:
            # Fallback to pyautogui
            self.screen_width, self.screen_height = pyautogui.size()
        
        print(f"🖥️  Screen resolution: {self.screen_width}x{self.screen_height}")
        
        # Initialize Kalman filter
        if self.smoothing_method == "kalman":
            self._init_kalman_filter()
        
        # Previous position for linear smoothing
        self.prev_x = None
        self.prev_y = None
        
        # Movement bounds (add margins to prevent cursor at extreme edges)
        self.margin = 50
        self.min_x = self.margin
        self.max_x = self.screen_width - self.margin
        self.min_y = self.margin
        self.max_y = self.screen_height - self.margin
        
        # Disable PyAutoGUI failsafe (cursor in corner)
        pyautogui.FAILSAFE = False
        
    def _init_kalman_filter(self):
        """Initialize Kalman filter for smooth cursor movement."""
        # State: [x, y, vx, vy] (position and velocity)
        self.kf = KalmanFilter(dim_x=4, dim_z=2)
        
        # State transition matrix (constant velocity model)
        dt = 0.1  # Time step
        self.kf.F = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        # Measurement matrix (we measure position only)
        self.kf.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])
        
        # Measurement noise covariance
        self.kf.R *= 10  # Increase if cursor is too jittery
        
        # Process noise covariance
        self.kf.Q *= 0.1  # Decrease for smoother movement
        
        # Initial state
        self.kf.x = np.array([self.screen_width/2, self.screen_height/2, 0, 0])
        
        # Initial covariance
        self.kf.P *= 100
        
        self.kalman_initialized = False
    
    def map_to_screen(self, hand_x: int, hand_y: int, 
                      frame_width: int, frame_height: int) -> Tuple[int, int]:
        """
        Map hand position from frame coordinates to screen coordinates.
        
        Args:
            hand_x: X coordinate in frame
            hand_y: Y coordinate in frame
            frame_width: Frame width
            frame_height: Frame height
            
        Returns:
            Tuple[int, int]: (screen_x, screen_y)
        """
        # Normalize hand position (0 to 1)
        norm_x = hand_x / frame_width
        norm_y = hand_y / frame_height
        
        # Map to screen coordinates with speed multiplier
        screen_x = int(norm_x * self.screen_width * self.speed_multiplier)
        screen_y = int(norm_y * self.screen_height * self.speed_multiplier)
        
        # Clamp to screen bounds with margins
        screen_x = max(self.min_x, min(self.max_x, screen_x))
        screen_y = max(self.min_y, min(self.max_y, screen_y))
        
        return screen_x, screen_y
    
    def smooth_position(self, x: int, y: int) -> Tuple[int, int]:
        """
        Apply smoothing to cursor position.
        
        Args:
            x: Raw X coordinate
            y: Raw Y coordinate
            
        Returns:
            Tuple[int, int]: Smoothed (x, y) coordinates
        """
        if self.smoothing_method == "kalman":
            return self._kalman_smooth(x, y)
        else:
            return self._linear_smooth(x, y)
    
    def _kalman_smooth(self, x: int, y: int) -> Tuple[int, int]:
        """
        Apply Kalman filtering for smooth movement.
        
        Args:
            x: Measured X coordinate
            y: Measured Y coordinate
            
        Returns:
            Tuple[int, int]: Filtered (x, y)
        """
        # Initialize Kalman filter with first measurement
        if not self.kalman_initialized:
            self.kf.x = np.array([x, y, 0, 0])
            self.kalman_initialized = True
            return x, y
        
        # Predict
        self.kf.predict()
        
        # Update with measurement
        measurement = np.array([x, y])
        self.kf.update(measurement)
        
        # Extract position from state
        smooth_x = int(self.kf.x[0])
        smooth_y = int(self.kf.x[1])
        
        return smooth_x, smooth_y
    
    def _linear_smooth(self, x: int, y: int, alpha=0.3) -> Tuple[int, int]:
        """
        Apply linear interpolation smoothing.
        
        Args:
            x: Current X coordinate
            y: Current Y coordinate
            alpha: Smoothing factor (0=no smoothing, 1=no update)
            
        Returns:
            Tuple[int, int]: Smoothed (x, y)
        """
        if self.prev_x is None or self.prev_y is None:
            self.prev_x, self.prev_y = x, y
            return x, y
        
        # Exponential moving average
        smooth_x = int(alpha * self.prev_x + (1 - alpha) * x)
        smooth_y = int(alpha * self.prev_y + (1 - alpha) * y)
        
        self.prev_x, self.prev_y = smooth_x, smooth_y
        
        return smooth_x, smooth_y
    
    def move_cursor(self, hand_x: int, hand_y: int, 
                    frame_width: int, frame_height: int):
        """
        Move cursor based on hand position.
        
        Args:
            hand_x: Hand X coordinate in frame
            hand_y: Hand Y coordinate in frame
            frame_width: Frame width
            frame_height: Frame height
        """
        # Map to screen coordinates
        screen_x, screen_y = self.map_to_screen(hand_x, hand_y, 
                                               frame_width, frame_height)
        
        # Apply smoothing
        smooth_x, smooth_y = self.smooth_position(screen_x, screen_y)
        
        # Move cursor (duration=0 for instant movement)
        pyautogui.moveTo(smooth_x, smooth_y, duration=0)
    
    def click(self, button='left', clicks=1):
        """
        Perform mouse click.
        
        Args:
            button: 'left', 'right', or 'middle'
            clicks: Number of clicks (1 for single, 2 for double)
        """
        pyautogui.click(button=button, clicks=clicks)
    
    def get_current_position(self) -> Tuple[int, int]:
        """
        Get current cursor position.
        
        Returns:
            Tuple[int, int]: (x, y) cursor position
        """
        return pyautogui.position()
    
    def reset_smoothing(self):
        """Reset smoothing filters."""
        if self.smoothing_method == "kalman":
            self.kalman_initialized = False
            self._init_kalman_filter()
        else:
            self.prev_x = None
            self.prev_y = None


if __name__ == "__main__":
    # Test cursor controller
    print("Cursor Controller Module - Testing...")
    
    controller = CursorController(smoothing_method="kalman", speed_multiplier=1.5)
    
    print(f"✅ Cursor controller initialized")
    print(f"   Smoothing: {controller.smoothing_method}")
    print(f"   Speed multiplier: {controller.speed_multiplier}")
    print(f"   Movement bounds: ({controller.min_x}, {controller.min_y}) to ({controller.max_x}, {controller.max_y})")
    
    # Test movement
    import time
    print("\n🖱️  Testing cursor movement (will move in circle)...")
    print("   Press Ctrl+C to stop")
    
    try:
        center_x, center_y = controller.screen_width // 2, controller.screen_height // 2
        radius = 100
        
        for angle in range(0, 360, 5):
            rad = np.radians(angle)
            x = center_x + int(radius * np.cos(rad))
            y = center_y + int(radius * np.sin(rad))
            
            # Simulate hand position mapping
            smooth_x, smooth_y = controller.smooth_position(x, y)
            pyautogui.moveTo(smooth_x, smooth_y, duration=0)
            time.sleep(0.05)
        
        print("✅ Test completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test stopped")