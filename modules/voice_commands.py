"""
Voice Commands Module
Wake word detection and command parsing
"""

import speech_recognition as sr
import threading


class VoiceCommandListener:
    """Listens for wake word and processes voice commands."""
    
    def __init__(self, wake_word="gestron", stop_word="stop", timeout=10):
        """
        Initialize voice command listener.
        
        Args:
            wake_word: Activation word
            stop_word: Deactivation word
            timeout: Command listening timeout (seconds)
        """
        self.wake_word = wake_word.lower()
        self.stop_word = stop_word.lower()
        self.timeout = timeout
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        self.listening_for_wake = False
        self.command_detected_callback = None
        
        # Adjust for ambient noise
        with self.microphone as source:
            print("🎤 Calibrating microphone...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        
        print(f"✅ Voice commands ready (wake word: '{self.wake_word}')")
    
    def start_wake_word_listening(self, callback):
        """
        Start background thread listening for wake word.
        
        Args:
            callback: Function to call when wake word detected
        """
        self.listening_for_wake = True
        self.command_detected_callback = callback
        
        def wake_word_worker():
            while self.listening_for_wake:
                try:
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                        text = self.recognizer.recognize_google(audio).lower()
                        
                        if self.wake_word in text:
                            if self.command_detected_callback:
                                self.command_detected_callback()
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    continue
        
        thread = threading.Thread(target=wake_word_worker, daemon=True)
        thread.start()
        print(f"👂 Listening for wake word '{self.wake_word}'...")
    
    def listen_for_command(self) -> str:
        """
        Listen for voice command after wake word.
        
        Returns:
            str: Recognized command text or None
        """
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=self.timeout, phrase_time_limit=5)
                command = self.recognizer.recognize_google(audio)
                return command
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"❌ Recognition error: {e}")
            return None
    
    def stop_wake_word_listening(self):
        """Stop listening for wake word."""
        self.listening_for_wake = False
    
    def parse_command(self, command_text: str) -> tuple:
        """
        Parse command text into action and parameters.
        
        Args:
            command_text: Raw command text
            
        Returns:
            tuple: (action, parameters)
        """
        if not command_text:
            return None, None
        
        text = command_text.lower().strip()
        
        # Check for stop command
        if self.stop_word in text:
            return 'stop_listening', None
        
        # Media commands
        if "play" in text:
            query = text.replace("play", "").strip()
            return 'play_media', query
        elif "pause" in text:
            return 'media_pause', None
        elif "resume" in text:
            return 'media_resume', None
        elif "next" in text:
            return 'media_next', None
        elif "previous" in text:
            return 'media_previous', None
        elif "mute" in text:
            return 'volume_mute', None
        elif "unmute" in text:
            return 'volume_unmute', None
        elif "volume up" in text:
            return 'volume_up', None
        elif "volume down" in text:
            return 'volume_down', None
        
        # Dictation commands
        elif "open word" in text:
            return 'open_word_document', None
        elif "note this" in text or "write this" in text:
            content = text.split("note this")[-1] if "note this" in text else text.split("write this")[-1]
            content = content.strip()
            return 'dictate_to_word', content
        elif "start dictation" in text:
            return 'start_continuous_dictation', None
        elif "stop dictation" in text:
            return 'stop_continuous_dictation', None
        elif "new paragraph" in text:
            return 'insert_paragraph', None
        elif "save document" in text:
            return 'save_word_document', None
        
        # System commands
        elif "screenshot" in text:
            return 'take_screenshot', None
        elif "create folder" in text:
            folder_name = text.replace("create folder", "").strip()
            return 'create_desktop_folder', folder_name or None
        elif "search" in text:
            query = text.replace("search", "").strip()
            return 'google_search', query
        elif "what time" in text:
            return 'speak_current_time', None
        elif "help" in text:
            return 'list_commands', None
        elif "exit" in text or "quit" in text:
            return 'exit_application', None
        
        return 'unknown_command', text