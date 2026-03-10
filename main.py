"""
GESTRON - Real-Time Hand Gesture Interface for Human-Computer Interaction
Main Application - COMPLETE VERSION with Context-Aware, Sequences, Hold Gestures
"""

import cv2
import json
import time
import sys
import os
import re
from datetime import datetime
import argparse
import types

# Parse quick CLI args and provide a safe no-op pyautogui when requested or missing
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--no-pyautogui', action='store_true', help='Run without controlling real mouse/keyboard')
args, _unknown = parser.parse_known_args()

def _install_pyautogui_noop():
    import types
    import sys
    noop_mod = types.ModuleType('pyautogui')
    def _no_op(*_a, **_k):
        print("[NoOp pyautogui] called")
        return None
    noop_mod.click = _no_op
    noop_mod.doubleClick = _no_op
    noop_mod.double_click = _no_op
    noop_mod.moveTo = _no_op
    noop_mod.moveRel = _no_op
    noop_mod.press = _no_op
    noop_mod.hotkey = _no_op
    noop_mod.size = lambda: (1920, 1080)
    noop_mod.position = lambda: (0, 0)
    noop_mod.FAILSAFE = False
    noop_mod.mouseDown = _no_op
    noop_mod.mouseUp = _no_op
    noop_mod.click = _no_op
    sys.modules['pyautogui'] = noop_mod

if args.no_pyautogui:
    print("⚠️  Running with --no-pyautogui: pyautogui actions will be no-ops")
    _install_pyautogui_noop()
else:
    # If pyautogui is not installed we inject a no-op module so the app doesn't crash
    try:
        import importlib.util
        if importlib.util.find_spec('pyautogui') is None:
            print("⚠️  pyautogui not found => installing no-op fallback to prevent crashes")
            _install_pyautogui_noop()
    except Exception:
        # If importlib is unavailable for some reason, just ensure a no-op fallback
        try:
            import pyautogui  # type: ignore
        except Exception:
            _install_pyautogui_noop()

# Import modules
from modules.hand_detector import HandDetector
from modules.landmark_processor import LandmarkProcessor
from modules.rule_based_gestures import RuleBasedGestureDetector
from modules.ml_gesture_classifier import MLGestureClassifier
from modules.cursor_controller import CursorController
from modules.state_manager import StateManager, SystemState
from modules.safety_layer import SafetyLayer
from modules.voice_feedback import VoiceFeedback
from modules.voice_commands import VoiceCommandListener
from utils.desktop_actions import DesktopActions


class Gestron:
    """Main application class for GESTRON gesture control system."""
    
    def __init__(self, config_path='config.json'):
        """Initialize GESTRON application."""
        print("=" * 60)
        print("🚀 GESTRON - Hand Gesture Desktop Control")
        print("   WITH CONTEXT-AWARE & ADVANCED FEATURES")
        print("=" * 60)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self._init_components()
        
        # Performance tracking
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        self.last_fps_update = time.time()
        
        # System state
        self.running = False
        
        # Gesture cooldown
        self.last_gesture_time = 0
        self.gesture_cooldown = 2.0
        
        # Hold gesture tracking
        self.hold_gesture_start = None
        self.hold_gesture_name = None
        self.hold_threshold = 2.0  # seconds
        
        # Gesture sequence tracking
        self.gesture_sequence = []
        self.sequence_timeout = 3.0  # seconds
        self.last_sequence_time = 0
        
        # Gesture dead zone
        self.wait_for_hand_removal = False
        
        print("\n✅ GESTRON initialized successfully!")
        print("=" * 60)
    
    def _load_config(self, config_path):
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"✅ Configuration loaded: {config_path}")
            return config
        except Exception as e:
            print(f"❌ Failed to load config: {e}")
            sys.exit(1)
    
    def _init_components(self):
        """Initialize all system components."""
        cfg = self.config
        
        # 1. Hand Detector
        print("\n📷 Initializing Hand Detector...")
        self.hand_detector = HandDetector(
            max_num_hands=cfg['hand_detection']['max_num_hands'],
            min_detection_confidence=cfg['hand_detection']['min_detection_confidence'],
            min_tracking_confidence=cfg['hand_detection']['min_tracking_confidence']
        )
        
        # 2. Landmark Processor
        print("🔧 Initializing Landmark Processor...")
        self.landmark_processor = LandmarkProcessor()
        
        # 3. Rule-Based Gesture Detector
        print("✋ Initializing Rule-Based Gesture Detector...")
        self.rule_detector = RuleBasedGestureDetector(self.landmark_processor)
        
        # 4. ML Gesture Classifier
        print("🤖 Initializing ML Gesture Classifier...")
        try:
            self.ml_classifier = MLGestureClassifier(
                model_path=cfg['paths']['model_path'],
                labels_path=cfg['paths']['labels_path'],
                confidence_threshold=cfg['gesture_recognition']['confidence_threshold']
            )
        except Exception as e:
            print(f"⚠️  ML Classifier not available: {e}")
            self.ml_classifier = None
        
        # 5. Cursor Controller
        if cfg['mouse_control']['enabled']:
            print("🖱️  Initializing Cursor Controller...")
            self.cursor_controller = CursorController(
                smoothing_method=cfg['mouse_control']['cursor_smoothing'],
                speed_multiplier=cfg['mouse_control']['cursor_speed_multiplier']
            )
        else:
            self.cursor_controller = None
        
        # 6. State Manager
        print("🎮 Initializing State Manager...")
        self.state_manager = StateManager()
        
        # 7. Safety Layer
        print("🛡️  Initializing Safety Layer...")
        self.safety_layer = SafetyLayer(
            window_size=cfg['gesture_recognition']['temporal_smoothing_window'],
            required_detections=cfg['gesture_recognition']['temporal_smoothing_required'],
            confidence_threshold=cfg['gesture_recognition']['confidence_threshold']
        )
        
        # 8. Voice Feedback
        if cfg['voice_feedback']['enabled']:
            print("🔊 Initializing Voice Feedback...")
            self.voice_feedback = VoiceFeedback(
                enabled=True,
                volume=cfg['voice_feedback']['volume'],
                rate=cfg['voice_feedback']['rate'],
                voice_gender=cfg['voice_feedback']['voice_gender']
            )
        else:
            self.voice_feedback = None
        
        # 9. Voice Commands
        if cfg['voice_commands']['enabled']:
            print("🎤 Initializing Voice Commands...")
            self.voice_commands = VoiceCommandListener(
                wake_word=cfg['voice_commands']['wake_word'],
                stop_word=cfg['voice_commands']['stop_word'],
                timeout=cfg['voice_commands']['command_timeout_seconds']
            )
            self.voice_commands.start_wake_word_listening(self._on_wake_word_detected)
        else:
            self.voice_commands = None
        
        # 10. Desktop Actions
        print("💻 Initializing Desktop Actions...")
        self.desktop_actions = DesktopActions(
            desktop_path=cfg['paths']['desktop_path']
        )
        
        # 11. Webcam
        print("📹 Initializing Webcam...")
        self.cap = cv2.VideoCapture(cfg['system']['camera_id'])
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg['system']['camera_width'])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg['system']['camera_height'])
        
        if not self.cap.isOpened():
            print("❌ Failed to open webcam")
            sys.exit(1)
    
    def _get_active_window_name(self):
        """Get active window title for context-aware gestures."""
        try:
            import pygetwindow as gw
            active_window = gw.getActiveWindow()
            if active_window:
                title = active_window.title.lower()
                return title
        except:
            pass
        return ""
    
    def _is_browser_active(self):
        """Check if browser is active window."""
        title = self._get_active_window_name()
        browsers = ['chrome', 'firefox', 'edge', 'opera', 'brave', 'safari']
        return any(browser in title for browser in browsers)
    
    def _is_powerpoint_active(self):
        """Check if PowerPoint is active window."""
        title = self._get_active_window_name()
        return 'powerpoint' in title or 'ppt' in title
    
    def _is_file_explorer_active(self):
        """Check if File Explorer is active window."""
        title = self._get_active_window_name()
        return 'explorer' in title or 'file' in title
    
    def _on_wake_word_detected(self):
        """Callback when wake word 'Gestron' is detected."""
        print("\n🎤 Wake word detected!")
        self.state_manager.activate_voice_mode()
        
        if self.voice_feedback:
            self.voice_feedback.announce_voice_listening()
        
        command_text = self.voice_commands.listen_for_command()
        
        if command_text:
            print(f"📝 Command: {command_text}")
            self._process_voice_command(command_text)
        else:
            if self.voice_feedback:
                self.voice_feedback.announce_voice_timeout()
        
        self.state_manager.deactivate_voice_mode()
    
    def _process_voice_command(self, command_text):
        """Process recognized voice command."""
        action, params = self.voice_commands.parse_command(command_text)
        
        if action == 'stop_listening':
            if self.voice_feedback:
                self.voice_feedback.announce_voice_stopped()
            return
        
        self._execute_voice_action(action, params)
    
    def _execute_voice_action(self, action, params):
        """Execute voice command action."""
        actions_map = {
            'play_media': lambda p: self.desktop_actions.play_spotify(p),
            'media_pause': lambda p: self.desktop_actions.media_play_pause(),
            'media_resume': lambda p: self.desktop_actions.media_play_pause(),
            'media_next': lambda p: self.desktop_actions.media_next(),
            'media_previous': lambda p: self.desktop_actions.media_previous(),
            'volume_up': lambda p: self.desktop_actions.volume_up(),
            'volume_down': lambda p: self.desktop_actions.volume_down(),
            'volume_mute': lambda p: self.desktop_actions.volume_mute(),
            'open_word_document': lambda p: self.desktop_actions.open_word_document(p),
            'dictate_to_word': lambda p: self.desktop_actions.dictate_to_word(p),
            'start_continuous_dictation': lambda p: self.desktop_actions.start_continuous_dictation(p),
            'stop_continuous_dictation': lambda p: self.desktop_actions.stop_continuous_dictation(),
            'insert_paragraph': lambda p: self.desktop_actions.insert_paragraph(),
            'save_word_document': lambda p: self.desktop_actions.save_word_document(),
            'take_screenshot': lambda p: self.desktop_actions.take_screenshot(),
            'create_desktop_folder': lambda p: self.desktop_actions.create_desktop_folder(p),
            'google_search': lambda p: self.desktop_actions.google_search(p),
            'speak_current_time': lambda p: self.desktop_actions.speak_current_time(self.voice_feedback),
            'list_commands': lambda p: self.desktop_actions.list_available_commands(self.voice_feedback),
            'exit_application': lambda p: self.stop()
        }
        
        if action in actions_map:
            try:
                actions_map[action](params)
                self.wait_for_hand_removal = True  # Enable gesture dead zone after action
                if self.voice_feedback:
                    self.voice_feedback.speak(f"{action.replace('_', ' ')} executed")
            except Exception as e:
                print(f"❌ Action error: {e}")
                if self.voice_feedback:
                    self.voice_feedback.announce_error()
    
    def run(self):
        """Main application loop."""
        self.running = True
        
        if self.voice_feedback:
            self.voice_feedback.announce_system_ready()
        
        print("\n🎮 GESTRON is running!")
        print("   Press 'Q' to quit")
        print("   Press 'V' to toggle voice")
        print("\n   GESTURES:")
        print("   👍 Thumbs Up = ACTION MODE")
        print("   👎 Thumbs Down = Exit ACTION MODE")
        print("   ✋ Three Fingers = MOUSE MODE")
        print("   🤞 Two Crossed = Copy | ☝️ One Up = Paste | 🫴 Palm Up = Undo")
        print("=" * 60)
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                frame = cv2.flip(frame, 1)
                frame_height, frame_width = frame.shape[:2]
                
                hand_detected, landmarks = self.hand_detector.detect_hands(frame)
                
                # Gesture dead zone: wait for hand removal after action
                if self.wait_for_hand_removal:
                    if not hand_detected:
                        self.wait_for_hand_removal = False
                    else:
                        continue
                
                if hand_detected:
                    if self.state_manager.is_gesture_mode():
                        self._handle_gesture_mode(frame, landmarks, frame_width, frame_height)
                    elif self.state_manager.is_mouse_mode():
                        self._handle_mouse_mode(frame, landmarks, frame_width, frame_height)
                    elif self.state_manager.is_action_mode():
                        self._handle_action_mode(frame, landmarks, frame_width, frame_height)
                    elif self.state_manager.is_confirmation_pending():
                        self._handle_confirmation_mode(frame, landmarks)
                    
                    if self.config['display']['show_landmarks']:
                        self.hand_detector.draw_landmarks(frame, landmarks)
                else:
                    self.safety_layer.reset()
                    self.hold_gesture_start = None
                    self.hold_gesture_name = None
                
                self._update_fps()
                self._draw_ui(frame, hand_detected)
                
                cv2.imshow('GESTRON - Gesture Control', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('v'):
                    self._toggle_voice()
                
        except KeyboardInterrupt:
            print("\n⏹️  Interrupted by user")
        finally:
            self.stop()
    
    def _handle_gesture_mode(self, frame, landmarks, frame_width, frame_height):

        # GLOBAL gesture cooldown
        current_time = time.time()
        if current_time - self.last_gesture_time < self.gesture_cooldown:
            return

        """Handle gesture detection in gesture mode."""
        rule_gesture = self.rule_detector.detect_gesture(landmarks)
        
        # Check for Thumbs Up to enter ACTION MODE
        if rule_gesture == 'thumbs_up':
            self.safety_layer.add_detection('thumbs_up', 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            
            if stable_gesture == 'thumbs_up':
                # Check for gesture sequence (Thumbs Up → ShakaSign)
                self._add_to_sequence('thumbs_up')
                
                print("👍 Activating ACTION MODE!")
                self.state_manager.activate_action_mode()
                self.last_gesture_time = time.time()   
                if self.voice_feedback:
                    self.voice_feedback.speak("Action mode activated", priority='high')
                self.safety_layer.reset()
            return
        
        # Check for Three Fingers to enter mouse mode
        if rule_gesture == 'three_fingers':
            self.safety_layer.add_detection('three_fingers', 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            
            if stable_gesture == 'three_fingers':
                # Check for sequence (Three Fingers → L-Shape)
                self._add_to_sequence('three_fingers')
                
                print("✋ Entering MOUSE MODE!")
                self.state_manager.toggle_mouse_mode()
                if self.voice_feedback:
                    self.voice_feedback.announce_mouse_mode_activated()
                self.safety_layer.reset()
            return
        
        # Check for OpenPalm to open browser
        if rule_gesture == 'open_palm':
            self.safety_layer.add_detection('open_palm', 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            
            if stable_gesture == 'open_palm':
                print("🌐 Opening Browser!")
                self.desktop_actions.open_chrome()
                if self.voice_feedback:
                    self.voice_feedback.speak("Opening browser", priority='high')
                self.safety_layer.reset()
                self.last_gesture_time = time.time()
            return
        
        # NEW PRODUCTIVITY GESTURES (instant execution)
        if rule_gesture in ['two_crossed', 'one_up', 'palm_up', 'palm_down', 'vulcan']:
            self.safety_layer.add_detection(rule_gesture, 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            
            if stable_gesture:
                self._execute_productivity_gesture(stable_gesture)
                self.safety_layer.reset()
                self.last_gesture_time = time.time()
            return
        
        # Check for Fist HOLD gesture
        if rule_gesture == 'fist':
            self._check_hold_gesture('fist', lambda: self.desktop_actions.lock_screen())
            return
        
        # Check cooldown for custom gestures
        current_time = time.time()
        if current_time - self.last_gesture_time < self.gesture_cooldown:
            return
        
        # Check for custom gestures (ML model) - REQUIRES CONFIRMATION
        if self.ml_classifier:
            ml_gesture, ml_confidence = self.ml_classifier.classify(frame, landmarks)
            
            if ml_gesture:
                print(f"🔍 Detected: {ml_gesture} (confidence: {ml_confidence:.2%})")
                
                self.safety_layer.add_detection(ml_gesture, ml_confidence)
                stable_gesture, avg_confidence = self.safety_layer.get_stable_gesture()
                
                if stable_gesture:
                    print(f"✅ Stable gesture: {stable_gesture} (avg confidence: {avg_confidence:.2%})")
                    
                    action = self._get_gesture_action(stable_gesture)
                    self.state_manager.request_confirmation(stable_gesture, action)
                    self.last_gesture_time = current_time
                    
                    if self.voice_feedback:
                        self.voice_feedback.announce_gesture_detected(stable_gesture)
                    
                    self.safety_layer.reset()
    
    def _handle_action_mode(self, frame, landmarks, frame_width, frame_height):
        """Handle ACTION MODE - instant execution without confirmation."""
        if self.state_manager.check_action_timeout():
            print("⏱️  Action mode timeout - returning to gesture mode")
            if self.voice_feedback:
                self.voice_feedback.speak("Action mode deactivated", priority='medium')
            return
        
        rule_gesture = self.rule_detector.detect_gesture(landmarks)
        
        # Check for Thumbs Down to deactivate
        if rule_gesture == 'thumbs_down':
            self.safety_layer.add_detection('thumbs_down', 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            
            if stable_gesture == 'thumbs_down':
                print("👎 Deactivating ACTION MODE!")
                self.state_manager.deactivate_action_mode()
                if self.voice_feedback:
                    self.voice_feedback.speak("Action mode deactivated", priority='high')
                self.safety_layer.reset()
            return
        
        # CONTEXT-AWARE: Victory gesture
        if rule_gesture == 'victory':
            self.safety_layer.add_detection('victory', 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            
            if stable_gesture:
                if self._is_browser_active():
                    print("⚡ Browser: Next tab")
                    self.desktop_actions.browser_next_tab()
                elif self._is_powerpoint_active():
                    print("⚡ PowerPoint: Next slide")
                    self.desktop_actions.powerpoint_next_slide()
                elif self._is_file_explorer_active():
                    print("⚡ Explorer: Forward")
                    self.desktop_actions.switch_window()  # Placeholder
                else:
                    print("⚡ Default: Volume up")
                    self.desktop_actions.volume_up()
                
                self.safety_layer.reset()
                self.state_manager.deactivate_action_mode()
                self.last_gesture_time = time.time()
                return
        
        # CONTEXT-AWARE: Rock gesture
        if rule_gesture == 'rock':
            self.safety_layer.add_detection('rock', 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            
            if stable_gesture:
                if self._is_browser_active():
                    print("⚡ Browser: Close tab")
                    self.desktop_actions.browser_close_tab()
                else:
                    print("⚡ Default: Volume down")
                    self.desktop_actions.volume_down()
                
                self.safety_layer.reset()
                self.state_manager.deactivate_action_mode()
                self.last_gesture_time = time.time()
                return
        
        # Fist for PowerPoint toggle
        if rule_gesture == 'fist':
            self.safety_layer.add_detection('fist', 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            
            if stable_gesture:
                print("⚡ PowerPoint: Toggle slideshow")
                self.desktop_actions.powerpoint_toggle_slideshow()
                self.safety_layer.reset()
                self.state_manager.deactivate_action_mode()
                self.last_gesture_time = time.time()
                return
        
        # Process custom ML gestures (instant execution)
        if self.ml_classifier:
            ml_gesture, ml_confidence = self.ml_classifier.classify(frame, landmarks)
            
            if ml_gesture:
                self.safety_layer.add_detection(ml_gesture, ml_confidence)
                stable_gesture, avg_confidence = self.safety_layer.get_stable_gesture()
                
                if stable_gesture:
                    print(f"⚡ ACTION MODE: Executing {stable_gesture} (confidence: {avg_confidence:.2%})")
                    
                    # Check for gesture sequences
                    self._check_gesture_sequence(stable_gesture)
                    
                    action = self._get_gesture_action(stable_gesture)
                    if action:
                        self._execute_gesture_action(action)
                        self.safety_layer.reset()
                        self.state_manager.deactivate_action_mode()
                        self.last_gesture_time = time.time()
    
    def _handle_mouse_mode(self, frame, landmarks, frame_width, frame_height):
        """Handle mouse control in mouse mode."""
        rule_gesture = self.rule_detector.detect_gesture(landmarks)
        
        if rule_gesture == 'open_palm':
            self.safety_layer.add_detection('open_palm', 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            
            if stable_gesture == 'open_palm':
                self.state_manager.toggle_mouse_mode()
                if self.voice_feedback:
                    self.voice_feedback.announce_mouse_mode_deactivated()
                self.safety_layer.reset()
                if self.cursor_controller:
                    self.cursor_controller.reset_smoothing()
            return
        
        if rule_gesture == 'index_pointing' and self.cursor_controller:
            finger_x, finger_y = self.landmark_processor.get_index_fingertip_position(
                landmarks, (frame_height, frame_width)
            )
            self.cursor_controller.move_cursor(finger_x, finger_y, frame_width, frame_height)
        
        elif rule_gesture == 'pinch':
            self.safety_layer.add_detection('pinch', 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            if stable_gesture == 'pinch':
                self.desktop_actions.left_click()
                if self.voice_feedback:
                    self.voice_feedback.announce_left_click()
                self.safety_layer.reset()
        
        elif rule_gesture == 'fist':
            self.safety_layer.add_detection('fist', 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            if stable_gesture == 'fist':
                self.desktop_actions.right_click()
                if self.voice_feedback:
                    self.voice_feedback.announce_right_click()
                self.safety_layer.reset()
        
        elif rule_gesture == 'victory':
            self.safety_layer.add_detection('victory', 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            if stable_gesture == 'victory':
                self.desktop_actions.volume_up()
                if self.voice_feedback:
                    self.voice_feedback.announce_volume_up()
                self.safety_layer.reset()
        
        elif rule_gesture == 'rock':
            self.safety_layer.add_detection('rock', 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            if stable_gesture == 'rock':
                self.desktop_actions.volume_down()
                if self.voice_feedback:
                    self.voice_feedback.announce_volume_down()
                self.safety_layer.reset()
    
    def _handle_confirmation_mode(self, frame, landmarks):
        """Handle confirmation waiting state."""
        if self.state_manager.check_confirmation_timeout():
            print("⏱️  Confirmation timeout - action cancelled")
            if self.voice_feedback:
                self.voice_feedback.announce_confirmation_timeout()
            self.safety_layer.reset()
            return
        
        rule_gesture = self.rule_detector.detect_gesture(landmarks)
        
        print(f"🔍 Waiting for Fist... detected: {rule_gesture}")
        
        if rule_gesture == 'fist':
            self.safety_layer.add_detection('fist', 1.0)
            stable_gesture, _ = self.safety_layer.get_stable_gesture()
            
            if stable_gesture == 'fist':
                print("✊ Fist confirmed!")
                
                gesture, action = self.state_manager.confirm_action()
                if self.voice_feedback:
                    self.voice_feedback.announce_confirmation_received()
                
                print(f"🎯 Executing action: {action} for gesture: {gesture}")
                self._execute_gesture_action(action)
                self.safety_layer.reset()
                self.last_gesture_time = time.time()
    
    def _execute_productivity_gesture(self, gesture):
        """Execute productivity gestures instantly."""
        actions = {
            'two_crossed': ('Copy', self.desktop_actions.copy_text),
            'one_up': ('Paste', self.desktop_actions.paste_text),
            'palm_up': ('Undo', self.desktop_actions.undo_action),
            'palm_down': ('Close Window', self.desktop_actions.close_window),
            'vulcan': ('New Tab', self.desktop_actions.browser_new_tab)
        }
        
        if gesture in actions:
            action_name, action_func = actions[gesture]
            print(f"⚡ {action_name}")
            action_func()
            if self.voice_feedback:
                self.voice_feedback.speak(action_name, priority='high')
    
    def _execute_gesture_action(self, action):
        """Execute a gesture action."""
        action_map = {
            'media_play_pause': self.desktop_actions.media_play_pause,
            'screenshot': self.desktop_actions.take_screenshot,
            'bookmark_page': self.desktop_actions.bookmark_page,
            'open_word': self.desktop_actions.open_word_document
        }
        
        if action in action_map:
            action_map[action]()
            if self.voice_feedback:
                if action == 'screenshot':
                    self.voice_feedback.announce_screenshot_saved()
                elif action == 'bookmark_page':
                    self.voice_feedback.speak("Page bookmarked", priority='high')
                elif action == 'open_word':
                    self.voice_feedback.announce_word_opened()
                elif action == 'media_play_pause':
                    self.voice_feedback.announce_media_action('play')
    
    def _get_gesture_action(self, gesture_name):
        """Map gesture to action."""
        gesture_clean = re.sub(r'^\d+\s+', '', gesture_name)
        gesture_key = gesture_clean.lower().replace(' ', '_').replace('-', '_')
        
        gesture_actions = self.config['gesture_actions']['gesture_mode']
        
        if gesture_key in gesture_actions:
            return gesture_actions[gesture_key]['action']
        
        fallback_map = {
            'shaka_sign': 'media_play_pause',
            'finger_heart': 'screenshot',
            'l_shape': 'bookmark_page',
            'super': 'open_word'
        }
        
        action = fallback_map.get(gesture_key, None)
        print(f"📋 Gesture mapping: '{gesture_name}' → '{gesture_key}' → action: '{action}'")
        return action
    
    def _check_hold_gesture(self, gesture, action_func):
        """Check if gesture is held for threshold time."""
        current_time = time.time()
        
        if self.hold_gesture_name != gesture:
            self.hold_gesture_start = current_time
            self.hold_gesture_name = gesture
        else:
            hold_duration = current_time - self.hold_gesture_start
            
            if hold_duration >= self.hold_threshold:
                print(f"🔒 Hold gesture detected: {gesture} (held {hold_duration:.1f}s)")
                action_func()
                if self.voice_feedback:
                    self.voice_feedback.speak("Screen locked", priority='high')
                
                self.hold_gesture_start = None
                self.hold_gesture_name = None
                self.last_gesture_time = current_time
    
    def _add_to_sequence(self, gesture):
        """Add gesture to sequence buffer."""
        current_time = time.time()
        
        if current_time - self.last_sequence_time > self.sequence_timeout:
            self.gesture_sequence = []
        
        self.gesture_sequence.append(gesture)
        self.last_sequence_time = current_time
        
        print(f"📝 Gesture sequence: {' → '.join(self.gesture_sequence)}")
    
    def _check_gesture_sequence(self, gesture):
        """Check for predefined gesture sequences."""
        self._add_to_sequence(gesture)
        
        # Sequence: Thumbs Up → ShakaSign = Open Spotify + Play
        if len(self.gesture_sequence) >= 2:
            if (self.gesture_sequence[-2] == 'thumbs_up' and 
                'shaka' in gesture.lower()):
                print("🎵 Sequence: Opening Spotify + Playing music")
                self.desktop_actions.play_spotify("liked songs")
                if self.voice_feedback:
                    self.voice_feedback.speak("Opening Spotify playlist", priority='high')
                self.gesture_sequence = []
                return True
        
        # Sequence: Three Fingers → L-Shape = Open Chrome + Gmail
        if len(self.gesture_sequence) >= 2:
            if (self.gesture_sequence[-2] == 'three_fingers' and 
                'l_shape' in gesture.lower()):
                print("📧 Sequence: Opening Chrome + Gmail")
                self.desktop_actions.open_chrome()
                time.sleep(2)
                self.desktop_actions.google_search("gmail")
                if self.voice_feedback:
                    self.voice_feedback.speak("Opening Gmail", priority='high')
                self.gesture_sequence = []
                return True
        
        return False
    
    def _update_fps(self):
        """Update FPS calculation."""
        self.frame_count += 1
        current_time = time.time()
        
        if current_time - self.last_fps_update >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_fps_update)
            self.frame_count = 0
            self.last_fps_update = current_time
    
    def _draw_ui(self, frame, hand_detected):
        """Draw UI overlay on frame."""
        h, w = frame.shape[:2]
        
        # Determine background color based on mode
        if self.state_manager.is_action_mode():
            bg_color = (0, 100, 0)
            border_color = (0, 255, 0)
        else:
            bg_color = (0, 0, 0)
            border_color = (255, 255, 255)
        
        # Background panel
        cv2.rectangle(frame, (10, 10), (w-10, 200), bg_color, -1)
        cv2.rectangle(frame, (10, 10), (w-10, 200), border_color, 2)
        
        # FPS
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Mode
        mode_text = self.state_manager.get_current_state().value.replace('_', ' ').upper()
        mode_color = (0, 255, 0) if self.state_manager.is_action_mode() else (255, 255, 0)
        cv2.putText(frame, f"Mode: {mode_text}", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
        
        # Hand status
        hand_status = "Hand Detected" if hand_detected else "No Hand"
        color = (0, 255, 0) if hand_detected else (0, 0, 255)
        cv2.putText(frame, hand_status, (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Context info
        if self._is_browser_active():
            cv2.putText(frame, "Context: Browser Active", (20, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 2)
        elif self._is_powerpoint_active():
            cv2.putText(frame, "Context: PowerPoint Active", (20, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 2)
        
        # Action mode timer
        if self.state_manager.is_action_mode():
            remaining = self.state_manager.get_action_remaining_time()
            cv2.putText(frame, f"ACTION MODE: {remaining:.1f}s", (20, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, "Context-aware gestures active!", (20, 190),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        
        # Confirmation timer
        elif self.state_manager.is_confirmation_pending():
            remaining = self.state_manager.get_confirmation_remaining_time()
            cv2.putText(frame, f"Show FIST to confirm ({remaining:.1f}s)", (20, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Normal mode hint
        elif self.state_manager.is_gesture_mode():
            cv2.putText(frame, "Productivity: 🤞Copy | ☝️Paste | 🫴Undo", (20, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        # Hold gesture indicator
        if self.hold_gesture_name:
            hold_duration = time.time() - self.hold_gesture_start
            cv2.putText(frame, f"Holding {self.hold_gesture_name}: {hold_duration:.1f}s", (20, h-20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
        
        # Gesture sequence indicator
        if self.gesture_sequence:
            sequence_text = " → ".join(self.gesture_sequence[-3:])  # Show last 3
            cv2.putText(frame, f"Sequence: {sequence_text}", (20, h-50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    
    def _toggle_voice(self):
        """Toggle voice feedback on/off."""
        if self.voice_feedback:
            self.voice_feedback.enabled = not self.voice_feedback.enabled
            status = "ON" if self.voice_feedback.enabled else "OFF"
            print(f"🔊 Voice feedback: {status}")
    
    def stop(self):
        """Stop the application and cleanup resources."""
        print("\n⏹️  Stopping GESTRON...")
        self.running = False
        
        if self.voice_feedback:
            self.voice_feedback.announce_system_shutdown()
            self.voice_feedback.shutdown()
        
        if self.voice_commands:
            self.voice_commands.stop_wake_word_listening()
        
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        self.hand_detector.release()
        
        print("✅ GESTRON stopped successfully")
        print("=" * 60)


if __name__ == "__main__":
    try:
        app = Gestron(config_path='config.json')
        app.run()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()