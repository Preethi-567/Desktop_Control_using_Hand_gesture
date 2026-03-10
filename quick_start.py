"""
Quick Start Script
Simplified launcher for GESTRON with interactive setup
"""

import os
import sys
import json

def create_default_config():
    """Create default config.json if not exists."""
    if os.path.exists('config.json'):
        print("✅ config.json already exists")
        return
    
    print("📝 Creating default config.json...")
    
    default_config = {
        "system": {
            "app_name": "GESTRON",
            "version": "1.0.0",
            "fps_target": 30,
            "camera_id": 0,
            "camera_width": 1280,
            "camera_height": 720
        },
        "hand_detection": {
            "max_num_hands": 1,
            "min_detection_confidence": 0.7,
            "min_tracking_confidence": 0.5,
            "model_complexity": 1
        },
        "gesture_recognition": {
            "confidence_threshold": 0.80,
            "temporal_smoothing_window": 5,
            "temporal_smoothing_required": 3,
            "confirmation_timeout_seconds": 3
        },
        "mouse_control": {
            "enabled": True,
            "cursor_smoothing": "kalman",
            "cursor_speed_multiplier": 1.5,
            "screen_width": 1920,
            "screen_height": 1080
        },
        "voice_feedback": {
            "enabled": True,
            "volume": 0.8,
            "rate": 150,
            "voice_gender": "female"
        },
        "voice_commands": {
            "enabled": True,
            "wake_word": "gestron",
            "stop_word": "stop",
            "command_timeout_seconds": 10,
            "language": "en-US",
            "media_platform": "spotify",
            "dictation_autosave_interval_seconds": 30
        },
        "paths": {
            "model_path": "models/model.tflite",
            "labels_path": "models/labels.txt",
            "desktop_path": "~/Desktop",
            "log_path": "logs/performance.log"
        },
        "display": {
            "show_landmarks": True,
            "show_fps": True
        }
    }
    
    with open('config.json', 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print("✅ Default config.json created")

def create_directories():
    """Create required directories."""
    dirs = ['models', 'logs', 'modules', 'utils']
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
    print("✅ Directories created")

def check_model_files():
    """Check if model files exist."""
    model_path = 'models/model.tflite'
    labels_path = 'models/labels.txt'
    
    if not os.path.exists(model_path):
        print("\n⚠️  WARNING: model.tflite not found!")
        print("   Custom gestures will not work.")
        print("   Please add your trained model to models/ directory")
        print("   Train model at: https://teachablemachine.withgoogle.com/")
        return False
    
    if not os.path.exists(labels_path):
        print("\n⚠️  WARNING: labels.txt not found!")
        print("   Please add labels.txt to models/ directory")
        return False
    
    print("✅ Model files found")
    return True

def interactive_setup():
    """Interactive first-time setup."""
    print("=" * 60)
    print("🚀 GESTRON Quick Start Setup")
    print("=" * 60)
    
    # Create directories
    print("\n1️⃣  Creating directories...")
    create_directories()
    
    # Create config
    print("\n2️⃣  Setting up configuration...")
    create_default_config()
    
    # Check model
    print("\n3️⃣  Checking model files...")
    has_model = check_model_files()
    
    # Final instructions
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    
    if not has_model:
        print("\n⚠️  To enable custom gestures:")
        print("   1. Visit https://teachablemachine.withgoogle.com/")
        print("   2. Train your model (shaka_sign, finger_heart, l_shape, super)")
        print("   3. Export as TensorFlow Lite")
        print("   4. Place model.tflite and labels.txt in models/ directory")
    
    print("\n🎮 Ready to launch GESTRON!")
    print("\nControls:")
    print("   • Press Q to quit")
    print("   • Press V to toggle voice")
    print("   • Say 'Gestron' for voice commands")
    print("\n" + "=" * 60)
    
    input("\nPress Enter to start GESTRON...")

def main():
    """Main quick start function."""
    # Check if first run
    if not os.path.exists('config.json'):
        interactive_setup()
    else:
        print("🚀 Launching GESTRON...")
    
    # Import and run main application
    try:
        from main_2P import Gestron
        app = Gestron(config_path='config.json')
        app.run()
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()