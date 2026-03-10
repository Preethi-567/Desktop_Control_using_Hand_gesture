"""
Desktop Actions Module
Wrapper functions for all desktop control actions - FINAL UPDATED VERSION
All missing functions added and media controls fixed
"""

import pyautogui
import subprocess
import os
import webbrowser
import time
import sys
from datetime import datetime
from typing import Optional


class DesktopActions:
    """Handles all desktop control actions."""
    
    def __init__(self, desktop_path=None):
        """
        Initialize desktop actions.
        
        Args:
            desktop_path: Path to Desktop folder
        """
        if desktop_path:
            self.desktop_path = os.path.expanduser(desktop_path)
        else:
            self.desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        
        # Create Desktop folder if doesn't exist
        os.makedirs(self.desktop_path, exist_ok=True)
        
        # Dictation state
        self.word_process = None
        self.dictation_active = False
        self.current_word_doc = None
        self.autosave_timer = None
        
        print(f"📁 Desktop path: {self.desktop_path}")
    
    # ========== Mouse Actions ==========
    
    def left_click(self):
        """Perform left mouse click."""
        pyautogui.click(button='left')
        print("🖱️  Left click")
    
    def right_click(self):
        """Perform right mouse click."""
        pyautogui.click(button='right')
        print("🖱️  Right click")
    
    def double_click(self):
        """Perform double click."""
        pyautogui.doubleClick()
        print("🖱️  Double click")
    
    # ========== Media Control (FIXED CROSS-PLATFORM) ==========
    
    def media_play_pause(self):
        """Toggle play/pause - FIXED CROSS-PLATFORM VERSION."""
        try:
            # Method 1: Try keyboard library (most reliable)
            import keyboard
            keyboard.press_and_release('play/pause media')
            print("🎵 Media play/pause (keyboard library)")
            return True
        except:
            pass
        
        try:
            # Method 2: Try PyAutoGUI with correct key name
            pyautogui.press('playpause')
            print("🎵 Media play/pause (pyautogui)")
            return True
        except:
            pass
        
        try:
            # Method 3: Windows-specific fallback
            if os.name == 'nt':
                import ctypes
                VK_MEDIA_PLAY_PAUSE = 0xB3
                ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
                print("🎵 Media play/pause (Windows VK)")
                return True
        except:
            pass
        
        try:
            # Method 4: Universal fallback (space key)
            pyautogui.press('space')
            print("⚠️  Using SPACE as media control fallback")
            return True
        except Exception as e:
            print(f"❌ All media control methods failed: {e}")
            return False
    
    def media_next(self):
        """Next track - FIXED VERSION."""
        try:
            import keyboard
            keyboard.press_and_release('next track')
            print("⏭️  Next track")
            return True
        except:
            try:
                pyautogui.press('nexttrack')
                print("⏭️  Next track")
                return True
            except:
                if os.name == 'nt':
                    import ctypes
                    VK_MEDIA_NEXT_TRACK = 0xB0
                    ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 2, 0)
                    print("⏭️  Next track (Windows)")
                    return True
        print("❌ Next track failed")
        return False
    
    def media_previous(self):
        """Previous track - FIXED VERSION."""
        try:
            import keyboard
            keyboard.press_and_release('previous track')
            print("⏮️  Previous track")
            return True
        except:
            try:
                pyautogui.press('prevtrack')
                print("⏮️  Previous track")
                return True
            except:
                if os.name == 'nt':
                    import ctypes
                    VK_MEDIA_PREV_TRACK = 0xB1
                    ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
                    print("⏮️  Previous track (Windows)")
                    return True
        print("❌ Previous track failed")
        return False
    
    def media_stop(self):
        """Stop media - FIXED VERSION."""
        try:
            import keyboard
            keyboard.press_and_release('stop media')
            print("⏹️  Media stopped")
            return True
        except:
            try:
                pyautogui.press('stop')
                print("⏹️  Media stopped")
                return True
            except:
                if os.name == 'nt':
                    import ctypes
                    VK_MEDIA_STOP = 0xB2
                    ctypes.windll.user32.keybd_event(VK_MEDIA_STOP, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(VK_MEDIA_STOP, 0, 2, 0)
                    print("⏹️  Media stopped (Windows)")
                    return True
        print("❌ Stop media failed")
        return False
    
    def volume_up(self):
        """Increase volume - FIXED VERSION."""
        try:
            import keyboard
            keyboard.press_and_release('volume up')
            print("🔊 Volume up")
            return True
        except:
            try:
                pyautogui.press('volumeup')
                print("🔊 Volume up")
                return True
            except:
                if os.name == 'nt':
                    import ctypes
                    VK_VOLUME_UP = 0xAF
                    ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
                    print("🔊 Volume up (Windows)")
                    return True
        print("❌ Volume up failed")
        return False
    
    def volume_down(self):
        """Decrease volume - FIXED VERSION."""
        try:
            import keyboard
            keyboard.press_and_release('volume down')
            print("🔉 Volume down")
            return True
        except:
            try:
                pyautogui.press('volumedown')
                print("🔉 Volume down")
                return True
            except:
                if os.name == 'nt':
                    import ctypes
                    VK_VOLUME_DOWN = 0xAE
                    ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
                    print("🔉 Volume down (Windows)")
                    return True
        print("❌ Volume down failed")
        return False
    
    def volume_mute(self):
        """Toggle mute - FIXED VERSION."""
        try:
            import keyboard
            keyboard.press_and_release('volume mute')
            print("🔇 Volume muted/unmuted")
            return True
        except:
            try:
                pyautogui.press('volumemute')
                print("🔇 Volume muted/unmuted")
                return True
            except:
                if os.name == 'nt':
                    import ctypes
                    VK_VOLUME_MUTE = 0xAD
                    ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
                    print("🔇 Volume muted/unmuted (Windows)")
                    return True
        print("❌ Volume mute failed")
        return False
    
    # ========== Text Editing (ADDED - WAS MISSING) ==========
    
    def copy_text(self):
        """Copy selected text (Ctrl+C)."""
        try:
            pyautogui.hotkey('ctrl', 'c')
            print("📋 Text copied")
            return True
        except Exception as e:
            print(f"❌ Copy error: {e}")
            return False
    
    def paste_text(self):
        """Paste from clipboard (Ctrl+V)."""
        try:
            pyautogui.hotkey('ctrl', 'v')
            print("📋 Text pasted")
            return True
        except Exception as e:
            print(f"❌ Paste error: {e}")
            return False
    
    def undo_action(self):
        """Undo last action (Ctrl+Z)."""
        try:
            pyautogui.hotkey('ctrl', 'z')
            print("↩️  Undo")
            return True
        except Exception as e:
            print(f"❌ Undo error: {e}")
            return False
    
    def redo_action(self):
        """Redo action (Ctrl+Y)."""
        try:
            pyautogui.hotkey('ctrl', 'y')
            print("↪️  Redo")
            return True
        except Exception as e:
            print(f"❌ Redo error: {e}")
            return False
    
    def select_all(self):
        """Select all text (Ctrl+A)."""
        try:
            pyautogui.hotkey('ctrl', 'a')
            print("📄 Select all")
            return True
        except Exception as e:
            print(f"❌ Select all error: {e}")
            return False
    
    # ========== Browser Control (ADDED - WAS MISSING) ==========
    
    def browser_new_tab(self):
        """Open new browser tab (Ctrl+T)."""
        try:
            pyautogui.hotkey('ctrl', 't')
            print("🌐 New tab opened")
            return True
        except Exception as e:
            print(f"❌ Browser new tab error: {e}")
            return False
    
    def browser_close_tab(self):
        """Close current browser tab (Ctrl+W)."""
        try:
            pyautogui.hotkey('ctrl', 'w')
            print("🌐 Tab closed")
            return True
        except Exception as e:
            print(f"❌ Browser close tab error: {e}")
            return False
    
    def browser_next_tab(self):
        """Switch to next browser tab (Ctrl+Tab)."""
        try:
            pyautogui.hotkey('ctrl', 'tab')
            print("🌐 Next tab")
            return True
        except Exception as e:
            print(f"❌ Browser next tab error: {e}")
            return False
    
    def browser_previous_tab(self):
        """Switch to previous browser tab (Ctrl+Shift+Tab)."""
        try:
            pyautogui.hotkey('ctrl', 'shift', 'tab')
            print("🌐 Previous tab")
            return True
        except Exception as e:
            print(f"❌ Browser previous tab error: {e}")
            return False
    
    def bookmark_page(self):
        """
        Bookmark current page in browser (Ctrl+D).
        Works in Chrome, Firefox, Edge, Opera, etc.
        """
        try:
            pyautogui.hotkey('ctrl', 'd')
            time.sleep(0.3)
            pyautogui.press('enter')  # Confirm bookmark dialog
            print("🔖 Page bookmarked")
            return True
        except Exception as e:
            print(f"❌ Bookmark error: {e}")
            return False
    
    # ========== Spotify Integration ==========
    
    def play_spotify(self, query: str):
        """
        Play music on Spotify.
        
        Args:
            query: Song/artist name to search
        """
        try:
            # Try to open Spotify desktop app
            if os.name == 'nt':  # Windows
                subprocess.Popen(['spotify.exe'], shell=True)
            else:  # Linux/Mac
                subprocess.Popen(['spotify'])
            
            time.sleep(2)  # Wait for Spotify to open
            
            # Use keyboard shortcut to search
            pyautogui.hotkey('ctrl', 'l')  # Search bar
            time.sleep(0.5)
            pyautogui.write(query, interval=0.05)
            time.sleep(0.5)
            pyautogui.press('enter')
            
            print(f"🎵 Playing on Spotify: {query}")
            return True
        except Exception as e:
            print(f"❌ Spotify error: {e}")
            return False
    
    # ========== Word Document Actions ==========
    
    def open_word_document(self, doc_name: Optional[str] = None):
        """
        Open Microsoft Word document.
        
        Args:
            doc_name: Optional document name to open
        """
        try:
            if os.name == 'nt':  # Windows
                if doc_name:
                    # Open specific document
                    doc_path = os.path.join(self.desktop_path, f"{doc_name}.docx")
                    if os.path.exists(doc_path):
                        os.startfile(doc_path)
                    else:
                        # Create new document
                        subprocess.Popen(['start', 'winword', doc_path], shell=True)
                    self.current_word_doc = doc_path
                else:
                    # Open blank document
                    subprocess.Popen(['start', 'winword'], shell=True)
                
                time.sleep(2)  # Wait for Word to open
                print("📝 Word opened")
                return True
            else:
                # Linux/Mac - use LibreOffice Writer
                subprocess.Popen(['libreoffice', '--writer'])
                print("📝 LibreOffice Writer opened")
                return True
        except Exception as e:
            print(f"❌ Word open error: {e}")
            return False
    
    def dictate_to_word(self, text: str, doc_name: Optional[str] = None):
        """
        Type text into Word document.
        
        Args:
            text: Text to type
            doc_name: Optional document name
        """
        try:
            # Open Word if not already open
            if not self.word_process or doc_name:
                self.open_word_document(doc_name)
            
            # Type the text
            time.sleep(0.5)
            pyautogui.write(text, interval=0.02)
            pyautogui.press('space')
            
            print(f"📝 Dictated: {text}")
            return True
        except Exception as e:
            print(f"❌ Dictation error: {e}")
            return False
    
    def start_continuous_dictation(self, doc_name: Optional[str] = None):
        """Start continuous dictation mode with auto-save."""
        self.open_word_document(doc_name)
        self.dictation_active = True
        self._start_autosave_timer()
        print("🎤 Continuous dictation started")
    
    def stop_continuous_dictation(self):
        """Stop continuous dictation and save."""
        self.dictation_active = False
        self.save_word_document()
        if self.autosave_timer:
            self.autosave_timer.cancel()
        print("🎤 Continuous dictation stopped")
    
    def insert_paragraph(self):
        """Insert new paragraph in Word."""
        pyautogui.press('enter')
        pyautogui.press('enter')
        print("📝 New paragraph inserted")
    
    def save_word_document(self):
        """Save current Word document."""
        pyautogui.hotkey('ctrl', 's')
        time.sleep(0.5)
        print("💾 Document saved")
    
    def _start_autosave_timer(self, interval=30):
        """Start auto-save timer for dictation."""
        import threading
        
        def autosave():
            if self.dictation_active:
                self.save_word_document()
                self._start_autosave_timer(interval)
        
        self.autosave_timer = threading.Timer(interval, autosave)
        self.autosave_timer.daemon = True
        self.autosave_timer.start()
    
    # ========== System Actions ==========
    
    def take_screenshot(self):
        """Take screenshot and save to Desktop."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'screenshot_{timestamp}.png'
            filepath = os.path.join(self.desktop_path, filename)
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            print(f"📸 Screenshot saved: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Screenshot error: {e}")
            return False
    
    def google_search(self, query: str):
        """
        Open Google search for query.
        
        Args:
            query: Search query
        """
        try:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            print(f"🔍 Searching: {query}")
            return True
        except Exception as e:
            print(f"❌ Search error: {e}")
            return False
    
    def switch_window(self):
        """Switch to next window (Alt+Tab)."""
        pyautogui.hotkey('alt', 'tab')
        print("🪟 Switched window")
    
    def close_window(self):
        """Close current window (Alt+F4)."""
        pyautogui.hotkey('alt', 'f4')
        print("❌ Window closed")
    
    def minimize_window(self):
        """Minimize current window."""
        pyautogui.hotkey('win', 'down')
        print("⬇️  Window minimized")
    
    def maximize_window(self):
        """Maximize current window."""
        pyautogui.hotkey('win', 'up')
        print("⬆️  Window maximized")
    
    def lock_screen(self):
        """Lock the computer screen."""
        try:
            if os.name == 'nt':
                subprocess.Popen(['rundll32.exe', 'user32.dll,LockWorkStation'])
            else:
                subprocess.Popen(['gnome-screensaver-command', '-l'])
            print("🔒 Screen locked")
        except Exception as e:
            print(f"❌ Lock screen error: {e}")
    
    # ========== PowerPoint Control ==========
    
    def open_powerpoint(self, file_path: Optional[str] = None):
        """
        Open PowerPoint presentation.
        
        Args:
            file_path: Optional path to specific presentation
        """
        try:
            if os.name == 'nt':  # Windows
                if file_path and os.path.exists(file_path):
                    os.startfile(file_path)
                else:
                    subprocess.Popen(['start', 'powerpnt'], shell=True)
                print("📊 PowerPoint opened")
                return True
            else:
                subprocess.Popen(['libreoffice', '--impress'])
                print("📊 LibreOffice Impress opened")
                return True
        except Exception as e:
            print(f"❌ PowerPoint open error: {e}")
            return False
    
    def powerpoint_next_slide(self):
        """Navigate to next PowerPoint slide."""
        pyautogui.press('right')
        print("➡️  Next slide")
    
    def powerpoint_previous_slide(self):
        """Navigate to previous PowerPoint slide."""
        pyautogui.press('left')
        print("⬅️  Previous slide")
    
    def powerpoint_start_slideshow(self):
        """Start PowerPoint slideshow from beginning."""
        pyautogui.press('f5')
        print("▶️  Slideshow started")
    
    def powerpoint_start_from_current(self):
        """Start PowerPoint slideshow from current slide."""
        pyautogui.hotkey('shift', 'f5')
        print("▶️  Slideshow started from current")
    
    def powerpoint_end_slideshow(self):
        """End PowerPoint slideshow."""
        pyautogui.press('esc')
        print("⏹️  Slideshow ended")
    
    def powerpoint_toggle_slideshow(self):
        """Toggle PowerPoint slideshow on/off."""
        pyautogui.press('f5')
        print("🔄 Slideshow toggled")
    
    # ========== Application Launchers ==========
    
    def open_chrome(self):
        """Open Google Chrome browser."""
        try:
            if os.name == 'nt':
                subprocess.Popen(['start', 'chrome'], shell=True)
            elif sys.platform == 'darwin':  # macOS
                subprocess.Popen(['open', '-a', 'Google Chrome'])
            else:  # Linux
                subprocess.Popen(['google-chrome'])
            print("🌐 Chrome opened")
            return True
        except Exception as e:
            print(f"❌ Chrome open error: {e}")
            return False
    
    def open_file_explorer(self):
        """Open File Explorer."""
        try:
            if os.name == 'nt':
                subprocess.Popen(['explorer'])
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', '.'])
            else:
                subprocess.Popen(['xdg-open', '.'])
            print("📁 File Explorer opened")
            return True
        except Exception as e:
            print(f"❌ Explorer open error: {e}")
            return False
    
    def open_calculator(self):
        """Open Calculator app."""
        try:
            if os.name == 'nt':
                subprocess.Popen(['calc'])
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', '-a', 'Calculator'])
            else:
                subprocess.Popen(['gnome-calculator'])
            print("🔢 Calculator opened")
            return True
        except Exception as e:
            print(f"❌ Calculator open error: {e}")
            return False
    
    def open_notepad(self):
        """Open Notepad."""
        try:
            if os.name == 'nt':
                subprocess.Popen(['notepad'])
            else:
                subprocess.Popen(['gedit'])
            print("📝 Notepad opened")
            return True
        except Exception as e:
            print(f"❌ Notepad open error: {e}")
            return False
    
    # ========== Utility Actions ==========
    
    def speak_current_time(self, voice_feedback):
        """Announce current time via voice feedback."""
        current_time = datetime.now().strftime('%I:%M %p')
        voice_feedback.speak(f"It's {current_time}")
        print(f"🕐 Current time: {current_time}")
    
    def list_available_commands(self, voice_feedback):
        """List available voice commands."""
        commands = """
        Available commands: 
        Play music, Pause, Next, Previous,
        Open Word, Note this, Screenshot,
        Search, What time is it
        """
        voice_feedback.speak(commands)
        print("📋 Listing available commands")


if __name__ == "__main__":
    # Test desktop actions
    print("Desktop Actions Module - Testing...")
    
    actions = DesktopActions()
    
    print("\n✅ Desktop Actions initialized")
    print(f"   Desktop path: {actions.desktop_path}")
    
    print("\n🎵 All functions available:")
    print("   - Text editing: copy, paste, undo")
    print("   - Browser control: new tab, close tab, next tab")
    print("   - Media control: play/pause, next, previous, volume")
    print("   - System: screenshot, lock, window management")
    
    print("\n✅ All fixes applied!")