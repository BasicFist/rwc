"""
RWC Terminal User Interface (TUI)
A simple text-based interface for Real-time Voice Conversion
"""
import os
import sys
import time
import threading
from typing import Optional

try:
    import pyaudio
    import numpy as np
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

from rwc.core import VoiceConverter
from rwc.utils.audio_devices import list_audio_devices


def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')


def print_header():
    """Print the header of the application"""
    print("=" * 60)
    print("              RWC - Real-time Voice Conversion")
    print("=" * 60)
    print()


def list_available_models():
    """List all available models in the models directory"""
    models_dir = "models"
    if os.path.exists(models_dir):
        model_files = []
        for root, dirs, files in os.walk(models_dir):
            for file in files:
                if file.endswith(('.pth', '.onnx', '.pt')):
                    # Skip files that are not intended for voice conversion
                    if 'hubert' not in file.lower() and 'rmvpe' not in file.lower():
                        model_files.append(os.path.join(root, file))
        return sorted(model_files)
    return []


def select_model():
    """Allow user to select a model from available models"""
    models = list_available_models()
    
    if not models:
        print("No models found. Please download models first.")
        return None
    
    print("\nAvailable Models:")
    for i, model in enumerate(models, 1):
        print(f"{i}. {os.path.basename(model)} ({model})")
    
    print(f"{len(models) + 1}. Enter custom model path")
    print(f"{len(models) + 2}. Go back")
    
    try:
        choice = int(input(f"\nSelect a model (1-{len(models)+2}): "))
        
        if 1 <= choice <= len(models):
            return models[choice - 1]
        elif choice == len(models) + 1:
            return input("Enter path to model file: ").strip()
        elif choice == len(models) + 2:
            return None
        else:
            print("Invalid selection.")
            return None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None


def file_conversion_tui():
    """File-based conversion interface"""
    print("\n--- File Conversion ---")
    
    model_path = select_model()
    if not model_path:
        return
    
    if not os.path.exists(model_path):
        print(f"Model not found: {model_path}")
        return
    
    input_path = input("Enter path to input audio file: ").strip()
    if not os.path.exists(input_path):
        print(f"Input audio file not found: {input_path}")
        return
    
    output_path = input("Enter output path for converted audio (default: output.wav): ").strip()
    if not output_path:
        output_path = "output.wav"
    
    try:
        pitch_change = int(input("Enter pitch change (-24 to 24, default: 0): ") or "0")
        if pitch_change < -24 or pitch_change > 24:
            print("Pitch change must be between -24 and 24")
            return
    except ValueError:
        print("Invalid pitch change value")
        return
    
    try:
        index_rate = float(input("Enter index rate (0.0 to 1.0, default: 0.75): ") or "0.75")
        if index_rate < 0.0 or index_rate > 1.0:
            print("Index rate must be between 0.0 and 1.0")
            return
    except ValueError:
        print("Invalid index rate value")
        return
    
    use_rmvpe = input("Use RMVPE for pitch extraction? (y/N): ").lower().startswith('y')
    
    print(f"\nConverting with model: {os.path.basename(model_path)}")
    print("This may take a moment...")
    
    try:
        converter = VoiceConverter(model_path, use_rmvpe=use_rmvpe)
        result_path = converter.convert_voice(
            input_path,
            output_path,
            pitch_change=pitch_change,
            index_rate=index_rate
        )
        print(f"\n✓ Conversion completed successfully!")
        print(f"Output saved to: {result_path}")
    except Exception as e:
        print(f"\n✗ Conversion failed: {str(e)}")


def real_time_conversion_tui():
    """Real-time conversion interface"""
    if not PYAUDIO_AVAILABLE:
        print("\nPyAudio is not available. Please install it with: pip install pyaudio")
        print("Also ensure PortAudio is installed: sudo apt-get install portaudio19-dev")
        return
    
    print("\n--- Real-time Conversion ---")
    print("Available audio devices:")
    list_audio_devices()
    
    model_path = select_model()
    if not model_path:
        return
    
    if not os.path.exists(model_path):
        print(f"Model not found: {model_path}")
        return
    
    try:
        input_device = int(input("Enter input device ID (default: 4): ") or "4")
        output_device = int(input("Enter output device ID (default: 0): ") or "0")
    except ValueError:
        print("Invalid device ID. Please enter a number.")
        return
    
    use_rmvpe = input("Use RMVPE for pitch extraction? (y/N): ").lower().startswith('y')
    
    print(f"\nStarting real-time conversion with model: {os.path.basename(model_path)}")
    print("Press Ctrl+C to stop conversion")
    print("Note: The actual real-time conversion will start in a new thread")
    
    try:
        converter = VoiceConverter(model_path, use_rmvpe=use_rmvpe)
        converter.real_time_convert(input_device, output_device)
        print("\nReal-time conversion completed!")
    except KeyboardInterrupt:
        print("\nReal-time conversion stopped by user.")
    except Exception as e:
        print(f"\nError during real-time conversion: {str(e)}")


def main_tui():
    """Main TUI loop"""
    while True:
        clear_screen()
        print_header()
        
        print("Select an option:")
        print("1. File Conversion - Convert audio files using RVC models")
        print("2. Real-time Conversion - Live microphone-based conversion")
        print("3. List Audio Devices - Show available audio devices")
        print("4. List Models - Show available RVC models")
        print("5. Help - Show usage information")
        print("6. Exit")
        
        try:
            choice = input("\nEnter your choice (1-6): ")
            
            if choice == '1':
                file_conversion_tui()
                input("\nPress Enter to return to the main menu...")
            elif choice == '2':
                real_time_conversion_tui()
                input("\nPress Enter to return to the main menu...")
            elif choice == '3':
                print("\nAvailable audio devices:")
                list_audio_devices()
                input("\nPress Enter to return to the main menu...")
            elif choice == '4':
                models = list_available_models()
                if models:
                    print("\nAvailable models:")
                    for i, model in enumerate(models, 1):
                        print(f"{i}. {model}")
                else:
                    print("\nNo models found. Please make sure models are downloaded.")
                input("\nPress Enter to return to the main menu...")
            elif choice == '5':
                print("""
Help - RWC Terminal Interface

This TUI provides a simple terminal-based interface to the Real-time Voice 
Conversion (RVC) system with the following features:

1. File Conversion:
   - Convert audio files using RVC models
   - Adjustable parameters (pitch, index rate)
   - RMVPE support for accurate pitch extraction

2. Real-time Conversion:
   - Live microphone-based voice conversion
   - Device selection for input and output
   - Same RVC models and parameters as file conversion

3. Device Listing:
   - Shows available input and output audio devices
   - Helps you select the correct device IDs

4. Model Listing:
   - Shows all available RVC models in the system
   - Supports both pretrained and community models

Prerequisites:
- PyAudio library (install with: pip install pyaudio)
- PortAudio development library (install with: sudo apt-get install portaudio19-dev)
- Downloaded RVC models
                """)
                input("\nPress Enter to return to the main menu...")
            elif choice == '6':
                print("\nThank you for using RWC Terminal Interface!")
                break
            else:
                print("\nInvalid choice. Please enter a number between 1 and 6.")
                time.sleep(2)
        except KeyboardInterrupt:
            print("\n\nReceived interrupt. Exiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            input("\nPress Enter to return to the main menu...")


if __name__ == "__main__":
    main_tui()