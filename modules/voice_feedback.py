"""
Voice Feedback Module
Text-to-speech feedback for all system events (21 situations)
"""

import pyttsx3
import threading
import queue
import time


class VoiceFeedback:
    """Provides voice feedback using pyttsx3."""
    
    def __init__(self, enabled=True, volume=0.8, rate=150, voice_gender='female'):
        """
        Initialize voice feedback system.
        
        Args:
            enabled: Enable/disable voice feedback
            volume: Speech volume (0.0 to 1.0)
            rate: Speech rate (words per minute)
            voice_gender: 'male' or 'female'
        """
        self.enabled = enabled
        self.engine = None
        self.speech_queue = queue.Queue()
        self.last_speech_time = {}
        self.throttle_duration = 2.0  # seconds
        
        if self.enabled:
            self._init_engine(volume, rate, voice_gender)
            self._start_speech_thread()
    
    def _init_engine(self, volume, rate, voice_gender):
        """Initialize pyttsx3 engine."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            
            # Set voice gender
            voices = self.engine.getProperty('voices')
            if voices:
                if voice_gender == 'female' and len(voices) > 1:
                    self.engine.setProperty('voice', voices[1].id)
                elif voice_gender == 'male' and len(voices) > 0:
                    self.engine.setProperty('voice', voices[0].id)
            
            print("🔊 Voice feedback initialized")
        except Exception as e:
            print(f"❌ Voice engine init failed: {e}")
            self.enabled = False
    
    def _start_speech_thread(self):
        """Start background thread for non-blocking speech."""
        def speech_worker():
            while True:
                text = self.speech_queue.get()
                if text is None:
                    break
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except:
                    pass
                self.speech_queue.task_done()
        
        thread = threading.Thread(target=speech_worker, daemon=True)
        thread.start()
    
    def speak(self, text: str, priority='medium', throttle_key=None):
        """
        Speak text with optional throttling.
        
        Args:
            text: Text to speak
            priority: 'high', 'medium', or 'low'
            throttle_key: Key for throttling repeated messages
        """
        if not self.enabled or not self.engine:
            return
        
        # Speech cooldown to prevent queue overload
        if priority == "low" and not self.speech_queue.empty():
            return
        
        # Check throttling
        if throttle_key:
            current_time = time.time()
            last_time = self.last_speech_time.get(throttle_key, 0)
            if current_time - last_time < self.throttle_duration:
                return  # Skip this message
            self.last_speech_time[throttle_key] = current_time
        
        # Add to queue
        self.speech_queue.put(text)
    
    # ===== Mode Switching (2 situations) =====
    def announce_mouse_mode_activated(self):
        """Mouse mode activated."""
        self.speak("Mouse mode activated", priority='high')
    
    def announce_mouse_mode_deactivated(self):
        """Mouse mode deactivated."""
        self.speak("Mouse mode deactivated", priority='high')
    
    # ===== Mouse Actions (4 situations) =====
    def announce_left_click(self):
        """Left click performed."""
        self.speak("Click", throttle_key='left_click')
    
    def announce_right_click(self):
        """Right click performed."""
        self.speak("Right click", throttle_key='right_click')
    
    def announce_volume_up(self):
        """Volume increased."""
        self.speak("Volume up", throttle_key='volume_up')
    
    def announce_volume_down(self):
        """Volume decreased."""
        self.speak("Volume down", throttle_key='volume_down')
    
    # ===== Gesture Detection (4 situations) =====
    def announce_gesture_detected(self, gesture_name: str):
        """Custom gesture detected, needs confirmation."""
        self.speak(f"{gesture_name} detected, show fist to confirm", priority='high')
    
    def announce_confirmation_received(self):
        """Confirmation fist shown."""
        self.speak("Confirmed", priority='high')
    
    def announce_confirmation_timeout(self):
        """Confirmation timeout."""
        self.speak("Action cancelled", priority='medium')
    
    def announce_gesture_unclear(self):
        """Low confidence detection."""
        self.speak("Gesture unclear, try again", priority='low')
    
    # ===== Action Results (4 situations) =====
    def announce_media_action(self, action: str):
        """Media control action."""
        messages = {
            'play': "Playing media",
            'pause': "Media paused",
            'next': "Next track",
            'previous': "Previous track"
        }
        self.speak(messages.get(action, f"{action}"), throttle_key='media')
    
    def announce_screenshot_saved(self):
        """Screenshot saved."""
        self.speak("Screenshot saved", priority='medium')
    
    def announce_folder_created(self):
        """New folder created."""
        self.speak("Folder created", priority='medium')
    
    def announce_word_opened(self):
        """Word document opened."""
        self.speak("Opening Word document", priority='medium')
    
    # ===== Errors (3 situations) =====
    def announce_no_hand_detected(self):
        """No hand in frame."""
        self.speak("No hand detected", throttle_key='no_hand')
    
    def announce_error(self, error_msg: str = "Error occurred"):
        """Generic error."""
        self.speak(error_msg, priority='high')
    
    # ===== System Status (2 situations) =====
    def announce_system_ready(self):
        """System started."""
        self.speak("Gesture control system ready", priority='high')
    
    def announce_system_shutdown(self):
        """System shutting down."""
        self.speak("Gesture control deactivated", priority='high')
    
    # ===== Voice Commands =====
    def announce_voice_listening(self):
        """Voice command mode activated."""
        self.speak("Yes?", priority='high')
    
    def announce_voice_stopped(self):
        """Voice command mode stopped."""
        self.speak("Voice commands deactivated", priority='high')
    
    def announce_voice_timeout(self):
        """Voice listening timeout."""
        self.speak("Listening timeout", priority='medium')
    
    def shutdown(self):
        """Shutdown voice engine."""
        if self.enabled:
            self.speech_queue.put(None)
            if self.engine:
                self.engine.stop()