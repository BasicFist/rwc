"""
RWC Terminal User Interface (TUI)
A comprehensive, navigable, and user-friendly interface for Real-time Voice Conversion
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

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # Define fallback colors
    class ColorsFallback:
        RED = ''
        GREEN = ''
        YELLOW = ''
        BLUE = ''
        MAGENTA = ''
        CYAN = ''
        WHITE = ''
        BRIGHT = ''
        RESET = ''
    Fore = ColorsFallback()
    Style = ColorsFallback()

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from rwc.core import VoiceConverter
from rwc.utils.audio_devices import list_audio_devices


def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')


def print_colored(text, color=Fore.WHITE, style=Style.NORMAL):
    """Print colored text if colorama is available"""
    if COLORS_AVAILABLE:
        print(f"{color}{style}{text}")
    else:
        print(text)


def print_header():
    """Print the header of the application"""
    print_colored("=" * 60, Fore.CYAN, Style.BRIGHT)
    print_colored("              RWC - Real-time Voice Conversion", Fore.MAGENTA, Style.BRIGHT)
    print_colored("        A Comprehensive Terminal User Interface", Fore.CYAN)
    print_colored("=" * 60, Fore.CYAN, Style.BRIGHT)
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
        print_colored("No models found. Please download models first.", Fore.RED)
        return None
    
    print_colored("\nAvailable Models:", Fore.YELLOW)
    for i, model in enumerate(models, 1):
        # Format the model path for better readability
        model_path_parts = model.split('/')
        if len(model_path_parts) >= 3:
            # Show parent directory and filename
            parent_dir = model_path_parts[-2]
            model_name = model_path_parts[-1]
            display_text = f"{parent_dir}/{model_name}"
        else:
            display_text = os.path.basename(model)
        
        print_colored(f"{i:2d}. {display_text}", Fore.GREEN)
        print_colored(f"    {model}", Fore.BLUE)
    
    print_colored(f"{len(models) + 1}. Enter custom model path", Fore.CYAN)
    print_colored(f"{len(models) + 2}. Go back", Fore.MAGENTA)
    
    try:
        choice = int(input(f"\n{Fore.YELLOW}Select a model (1-{len(models)+2}): {Fore.RESET}"))
        
        if 1 <= choice <= len(models):
            return models[choice - 1]
        elif choice == len(models) + 1:
            custom_path = input(f"{Fore.YELLOW}Enter path to model file: {Fore.RESET}").strip()
            return custom_path if custom_path else None
        elif choice == len(models) + 2:
            return None
        else:
            print_colored("Invalid selection.", Fore.RED)
            return None
    except ValueError:
        print_colored("Invalid input. Please enter a number.", Fore.RED)
        return None


def file_conversion_tui():
    """File-based conversion interface with improved UX"""
    print_colored("\n--- File Conversion ---", Fore.CYAN, Style.BRIGHT)
    
    model_path = select_model()
    if not model_path:
        return
    
    if not os.path.exists(model_path):
        print_colored(f"Model not found: {model_path}", Fore.RED)
        return
    
    print_colored(f"\nSelected model: {os.path.basename(model_path)}", Fore.GREEN)
    
    input_path = input(f"{Fore.YELLOW}Enter path to input audio file: {Fore.RESET}").strip()
    if not input_path:
        print_colored("No input file specified.", Fore.RED)
        return
        
    if not os.path.exists(input_path):
        print_colored(f"Input audio file not found: {input_path}", Fore.RED)
        return
    
    output_path = input(f"{Fore.YELLOW}Enter output path for converted audio (default: output.wav): {Fore.RESET}").strip()
    if not output_path:
        output_path = "output.wav"
    
    try:
        default_pitch = "0"
        pitch_input = input(f"{Fore.YELLOW}Enter pitch change (-24 to 24, default: {default_pitch}): {Fore.RESET}") or default_pitch
        pitch_change = int(pitch_input)
        if pitch_change < -24 or pitch_change > 24:
            print_colored("Pitch change must be between -24 and 24", Fore.RED)
            return
    except ValueError:
        print_colored("Invalid pitch change value", Fore.RED)
        return
    
    try:
        default_index = "0.75"
        index_input = input(f"{Fore.YELLOW}Enter index rate (0.0 to 1.0, default: {default_index}): {Fore.RESET}") or default_index
        index_rate = float(index_input)
        if index_rate < 0.0 or index_rate > 1.0:
            print_colored("Index rate must be between 0.0 and 1.0", Fore.RED)
            return
    except ValueError:
        print_colored("Invalid index rate value", Fore.RED)
        return
    
    use_rmvpe_input = input(f"{Fore.YELLOW}Use RMVPE for pitch extraction? (Y/n): {Fore.RESET}").lower()
    use_rmvpe = True if use_rmvpe_input in ['', 'y', 'yes'] else False
    
    print_colored(f"\nConverting with model: {os.path.basename(model_path)}", Fore.CYAN)
    print_colored("This may take a moment...", Fore.YELLOW)
    
    try:
        converter = VoiceConverter(model_path, use_rmvpe=use_rmvpe)
        result_path = converter.convert_voice(
            input_path,
            output_path,
            pitch_change=pitch_change,
            index_rate=index_rate
        )
        print_colored(f"\n✓ Conversion completed successfully!", Fore.GREEN, Style.BRIGHT)
        print_colored(f"Output saved to: {result_path}", Fore.CYAN)
    except Exception as e:
        print_colored(f"\n✗ Conversion failed: {str(e)}", Fore.RED)


def real_time_conversion_tui():
    """Real-time conversion interface with improved UX"""
    if not PYAUDIO_AVAILABLE:
        print_colored("\nPyAudio is not available. Please install it with: pip install pyaudio", Fore.RED)
        print_colored("Also ensure PortAudio is installed: sudo apt-get install portaudio19-dev", Fore.RED)
        return
    
    print_colored("\n--- Real-time Conversion ---", Fore.CYAN, Style.BRIGHT)
    print_colored("Available audio devices:", Fore.YELLOW)
    list_audio_devices()
    
    model_path = select_model()
    if not model_path:
        return
    
    if not os.path.exists(model_path):
        print_colored(f"Model not found: {model_path}", Fore.RED)
        return
    
    print_colored(f"\nSelected model: {os.path.basename(model_path)}", Fore.GREEN)
    
    try:
        default_input = "4"
        input_device_str = input(f"{Fore.YELLOW}Enter input device ID (default: {default_input}): {Fore.RESET}") or default_input
        input_device = int(input_device_str)
        
        default_output = "0"
        output_device_str = input(f"{Fore.YELLOW}Enter output device ID (default: {default_output}): {Fore.RESET}") or default_output
        output_device = int(output_device_str)
    except ValueError:
        print_colored("Invalid device ID. Please enter a number.", Fore.RED)
        return
    
    use_rmvpe_input = input(f"{Fore.YELLOW}Use RMVPE for pitch extraction? (Y/n): {Fore.RESET}").lower()
    use_rmvpe = True if use_rmvpe_input in ['', 'y', 'yes'] else False
    
    print_colored(f"\nStarting real-time conversion with model: {os.path.basename(model_path)}", Fore.CYAN)
    print_colored("Press Ctrl+C to stop conversion", Fore.YELLOW)
    print_colored("Note: The actual real-time conversion will start in a new thread", Fore.YELLOW)
    
    try:
        converter = VoiceConverter(model_path, use_rmvpe=use_rmvpe)
        print_colored("\nReal-time conversion starting...", Fore.GREEN)
        converter.real_time_convert(input_device=input_device, output_device=output_device)
        print_colored("\nReal-time conversion completed!", Fore.GREEN)
    except KeyboardInterrupt:
        print_colored("\nReal-time conversion stopped by user.", Fore.YELLOW)
    except Exception as e:
        print_colored(f"\nError during real-time conversion: {str(e)}", Fore.RED)


def main_tui():
    """Main TUI loop with comprehensive navigation"""
    while True:
        clear_screen()
        print_header()
        
        print_colored("Select an option:", Fore.YELLOW)
        print_colored("1. 🎵 File Conversion", Fore.GREEN)
        print_colored("   Convert audio files using RVC models", Fore.WHITE)
        print_colored("2. 🎤 Real-time Conversion", Fore.GREEN) 
        print_colored("   Live microphone-based voice conversion", Fore.WHITE)
        print_colored("3. 🔧 Audio Devices", Fore.CYAN)
        print_colored("   List available audio devices", Fore.WHITE)
        print_colored("4. 🤖 Models", Fore.CYAN)
        print_colored("   List available RVC models", Fore.WHITE)
        print_colored("5. ❓ Help & Info", Fore.CYAN)
        print_colored("   Show usage information and system info", Fore.WHITE)
        print_colored("6. 🚪 Exit", Fore.RED)
        
        try:
            choice = input(f"\n{Fore.YELLOW}Enter your choice (1-6): {Fore.RESET}")
            
            if choice == '1':
                file_conversion_tui()
                input(f"\n{Fore.CYAN}Press Enter to return to the main menu...{Fore.RESET}")
            elif choice == '2':
                real_time_conversion_tui()
                input(f"\n{Fore.CYAN}Press Enter to return to the main menu...{Fore.RESET}")
            elif choice == '3':
                print_colored("\nAvailable audio devices:", Fore.YELLOW)
                list_audio_devices()
                input(f"\n{Fore.CYAN}Press Enter to return to the main menu...{Fore.RESET}")
            elif choice == '4':
                models = list_available_models()
                if models:
                    print_colored(f"\nAvailable models ({len(models)}):", Fore.YELLOW)
                    for i, model in enumerate(models, 1):
                        # Format for better readability
                        model_path_parts = model.split('/')
                        if len(model_path_parts) >= 3:
                            parent_dir = model_path_parts[-2]
                            model_name = model_path_parts[-1]
                            display_text = f"{parent_dir}/{model_name}"
                        else:
                            display_text = os.path.basename(model)
                            
                        print_colored(f"{i:2d}. {display_text}", Fore.GREEN)
                        print_colored(f"    {model}", Fore.BLUE)
                else:
                    print_colored("\nNo models found. Please make sure models are downloaded.", Fore.RED)
                input(f"\n{Fore.CYAN}Press Enter to return to the main menu...{Fore.RESET}")
            elif choice == '5':
                print_colored(f"\n{'='*60}", Fore.MAGENTA)
                print_colored("                    HELP & INFORMATION", Fore.MAGENTA, Style.BRIGHT)
                print_colored(f"{'='*60}", Fore.MAGENTA)
                
                print_colored("""
📁 File Conversion:
   • Convert audio files using RVC models
   • Adjustable parameters (pitch, index rate)
   • RMVPE support for accurate pitch extraction

🎤 Real-time Conversion:
   • Live microphone-based voice conversion
   • Device selection for input and output
   • Same RVC models and parameters as file conversion

🔧 Audio Devices:
   • Shows available input and output audio devices
   • Helps you select the correct device IDs

🤖 Models:
   • Shows all available RVC models in the system
   • Supports both pretrained and community models including Homer Simpson

📊 System Information:""", Fore.YELLOW)
                
                # Display system info
                if TORCH_AVAILABLE:
                    print_colored(f"   • CUDA Available: {torch.cuda.is_available()}", Fore.CYAN)
                    if torch.cuda.is_available():
                        gpu_name = torch.cuda.get_device_name(0)
                    print_colored(f"   • GPU: {gpu_name}", Fore.CYAN)
                
                print_colored(f"   • Total Models: {len(list_available_models())}", Fore.CYAN)
                
                if PYAUDIO_AVAILABLE:
                    print_colored("   • Audio Input: Available", Fore.GREEN)
                else:
                    print_colored("   • Audio Input: Not Available", Fore.RED)
                
                print_colored("""
📋 Prerequisites:
   • PyAudio library (pip install pyaudio)
   • PortAudio development library (sudo apt-get install portaudio19-dev)
   • Downloaded RVC models

🎯 Tips:
   • Use the Homer Simpson model for fun voice conversions
   • Adjust pitch change for different vocal styles
   • RMVPE provides better pitch extraction quality
""", Fore.YELLOW)
                
                print_colored(f"{'='*60}", Fore.MAGENTA)
                
                input(f"\n{Fore.CYAN}Press Enter to return to the main menu...{Fore.RESET}")
            elif choice == '6':
                print_colored("\n👋 Thank you for using RWC Terminal Interface!", Fore.GREEN, Style.BRIGHT)
                print_colored("Have a great day!", Fore.CYAN)
                break
            else:
                print_colored("\n❌ Invalid choice. Please enter a number between 1 and 6.", Fore.RED)
                time.sleep(2)
        except KeyboardInterrupt:
            print_colored("\n\n⚠️ Received interrupt. Exiting...", Fore.YELLOW)
            break
        except Exception as e:
            print_colored(f"\n💥 An error occurred: {str(e)}", Fore.RED)
            input(f"\n{Fore.CYAN}Press Enter to return to the main menu...{Fore.RESET}")


if __name__ == "__main__":
    main_tui()