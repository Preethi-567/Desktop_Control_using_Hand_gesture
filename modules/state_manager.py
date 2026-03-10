"""
State Manager Module
Manages system states: GESTURE_MODE, MOUSE_MODE, VOICE_MODE, CONFIRMATION_PENDING, ACTION_MODE
"""

from enum import Enum
import time


class SystemState(Enum):
    """System operating states."""
    GESTURE_MODE = "gesture_mode"
    MOUSE_MODE = "mouse_mode"
    VOICE_MODE = "voice_mode"
    CONFIRMATION_PENDING = "confirmation_pending"
    ACTION_MODE = "action_mode"


class StateManager:
    """Manages system state transitions and mode handling."""
    
    def __init__(self):
        """Initialize state manager."""
        self.current_state = SystemState.GESTURE_MODE
        self.previous_state = None
        
        # Confirmation tracking
        self.pending_gesture = None
        self.pending_action = None
        self.confirmation_start_time = None
        self.confirmation_timeout = 5.0  # seconds (increased from 3)
        
        # Voice mode tracking
        self.voice_start_time = None
        self.voice_timeout = 10.0  # seconds
        
        # Action mode tracking
        self.action_start_time = None
        self.action_timeout = 25.0  # seconds
        
    def get_current_state(self) -> SystemState:
        """Get current system state."""
        return self.current_state
    
    def is_gesture_mode(self) -> bool:
        """Check if in gesture mode."""
        return self.current_state == SystemState.GESTURE_MODE
    
    def is_mouse_mode(self) -> bool:
        """Check if in mouse mode."""
        return self.current_state == SystemState.MOUSE_MODE
    
    def is_voice_mode(self) -> bool:
        """Check if in voice mode."""
        return self.current_state == SystemState.VOICE_MODE
    
    def is_confirmation_pending(self) -> bool:
        """Check if waiting for confirmation."""
        return self.current_state == SystemState.CONFIRMATION_PENDING
    
    def is_action_mode(self) -> bool:
        """Check if in action mode."""
        return self.current_state == SystemState.ACTION_MODE
    
    def toggle_mouse_mode(self):
        """Toggle between gesture and mouse modes."""
        if self.current_state == SystemState.MOUSE_MODE:
            self.transition_to(SystemState.GESTURE_MODE)
        elif self.current_state == SystemState.GESTURE_MODE:
            self.transition_to(SystemState.MOUSE_MODE)
    
    def activate_voice_mode(self):
        """Activate voice command mode."""
        self.previous_state = self.current_state
        self.transition_to(SystemState.VOICE_MODE)
        self.voice_start_time = time.time()
    
    def deactivate_voice_mode(self):
        """Deactivate voice mode and return to previous state."""
        if self.previous_state:
            self.transition_to(self.previous_state)
        else:
            self.transition_to(SystemState.GESTURE_MODE)
        self.voice_start_time = None
    
    def activate_action_mode(self):
        """Activate fast action mode (no confirmation needed)."""
        self.previous_state = self.current_state
        self.transition_to(SystemState.ACTION_MODE)
        self.action_start_time = time.time()
    
    def deactivate_action_mode(self):
        """Deactivate action mode and return to previous state."""
        if self.previous_state:
            self.transition_to(self.previous_state)
        else:
            self.transition_to(SystemState.GESTURE_MODE)
        self.action_start_time = None
    
    def request_confirmation(self, gesture: str, action: str):
        """Request user confirmation for risky action."""
        self.pending_gesture = gesture
        self.pending_action = action
        self.confirmation_start_time = time.time()
        self.previous_state = self.current_state
        self.transition_to(SystemState.CONFIRMATION_PENDING)
    
    def confirm_action(self) -> tuple:
        """Confirm pending action."""
        gesture = self.pending_gesture
        action = self.pending_action
        self.cancel_confirmation()
        return gesture, action
    
    def cancel_confirmation(self):
        """Cancel pending confirmation."""
        self.pending_gesture = None
        self.pending_action = None
        self.confirmation_start_time = None
        if self.previous_state:
            self.transition_to(self.previous_state)
    
    def check_confirmation_timeout(self) -> bool:
        """Check if confirmation has timed out."""
        if self.confirmation_start_time:
            elapsed = time.time() - self.confirmation_start_time
            if elapsed > self.confirmation_timeout:
                self.cancel_confirmation()
                return True
        return False
    
    def check_voice_timeout(self) -> bool:
        """Check if voice mode has timed out."""
        if self.voice_start_time:
            elapsed = time.time() - self.voice_start_time
            if elapsed > self.voice_timeout:
                self.deactivate_voice_mode()
                return True
        return False
    
    def check_action_timeout(self) -> bool:
        """Check if action mode has timed out."""
        if self.action_start_time:
            elapsed = time.time() - self.action_start_time
            if elapsed > self.action_timeout:
                self.deactivate_action_mode()
                return True
        return False
    
    def transition_to(self, new_state: SystemState):
        """Transition to a new state."""
        self.previous_state = self.current_state
        self.current_state = new_state
        print(f"🔄 State transition: {self.previous_state.value} → {new_state.value}")
    
    def get_confirmation_remaining_time(self) -> float:
        """Get remaining time for confirmation."""
        if self.confirmation_start_time:
            elapsed = time.time() - self.confirmation_start_time
            remaining = max(0, self.confirmation_timeout - elapsed)
            return remaining
        return 0.0
    
    def get_action_remaining_time(self) -> float:
        """Get remaining time for action mode."""
        if self.action_start_time:
            elapsed = time.time() - self.action_start_time
            remaining = max(0, self.action_timeout - elapsed)
            return remaining
        return 0.0


if __name__ == "__main__":
    # Test state manager
    print("State Manager Module - Testing...")
    
    sm = StateManager()
    print(f"Initial state: {sm.get_current_state().value}")
    
    # Test transitions
    sm.toggle_mouse_mode()
    print(f"After toggle: {sm.get_current_state().value}")
    
    sm.activate_action_mode()
    print(f"Action mode: {sm.get_current_state().value}")
    print(f"Remaining time: {sm.get_action_remaining_time():.1f}s")
    
    sm.deactivate_action_mode()
    print(f"After deactivate: {sm.get_current_state().value}")
    
    print("\n✅ State Manager tests completed")