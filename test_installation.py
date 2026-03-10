"""
Installation Test Script
Verifies all dependencies and components are properly installed
"""

import sys
import importlib

def check_module(module_name, package=None):
    """Check if a module can be imported."""
    try:
        if package:
            mod = importlib.import_module(f"{package}.{module_name}")
        else:
            mod = importlib.import_module(module_name)
        print(f"✅ {module_name if not package else package + '.' + module_name}")
        return True
    except ImportError as e:
        print(f"❌ {module_name if not package else package + '.' + module_name}: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 GESTRON Installation Verification")
    print("=" * 60)
    
    required_modules = [
        'cv2',
        'mediapipe',
        'tensorflow',
        'numpy',
        'pyautogui',
        'keyboard',
        'pyttsx3',
        'speech_recognition',
        'pyaudio',
        'filterpy',
        'screeninfo'
    ]
    
    print("\n📦 Checking Required Packages...")
    results = []
    for module in required_modules:
        results.append(check_module(module))
    
    # Check custom modules
    print("\n🔧 Checking Custom Modules...")
    custom_modules = [
        'hand_detector',
        'landmark_processor',
        'rule_based_gestures',
        'ml_gesture_classifier',
        'cursor_controller',
        'state_manager',
        'safety_layer',
        'voice_feedback',
        'voice_commands'
    ]
    
    for module in custom_modules:
        results.append(check_module(module, 'modules'))
    
    results.append(check_module('desktop_actions', 'utils'))
    
    # Check files
    print("\n📁 Checking Configuration Files...")
    import os
    
    files_to_check = [
        'config.json',
        'models/model.tflite',
        'models/labels.txt'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
            results.append(True)
        else:
            print(f"⚠️  {file_path} (optional - will need for custom gestures)")
            # Don't mark as failure for model files
            if 'model' not in file_path:
                results.append(False)
    
    # Check webcam
    print("\n📷 Checking Webcam...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✅ Webcam detected")
            cap.release()
            results.append(True)
        else:
            print("❌ No webcam detected")
            results.append(False)
    except Exception as e:
        print(f"❌ Webcam check failed: {e}")
        results.append(False)
    
    # Check microphone
    print("\n🎤 Checking Microphone...")
    try:
        import speech_recognition as sr
        mics = sr.Microphone.list_microphone_names()
        if mics:
            print(f"✅ Microphone detected: {mics[0]}")
            results.append(True)
        else:
            print("❌ No microphone detected")
            results.append(False)
    except Exception as e:
        print(f"❌ Microphone check failed: {e}")
        results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print("🎉 SUCCESS! All components verified.")
        print("   You can run: python main.py")
    else:
        print(f"⚠️  WARNING: {total_count - success_count} checks failed")
        print("   Please install missing dependencies:")
        print("   pip install -r requirements.txt")
    
    print("=" * 60)
    
    return success_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)