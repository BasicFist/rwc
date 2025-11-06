"""
Audio device listing utility for RWC
"""
import pyaudio


def list_audio_devices():
    """
    List all audio devices with their properties
    """
    p = pyaudio.PyAudio()
    
    print("Available Audio Devices:")
    print("=" * 50)
    
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        device_type = "Input" if info['maxInputChannels'] > 0 else "Output"
        
        print(f"Device {i}: {info['name']}")
        print(f"  - Type: {device_type}")
        print(f"  - Sample rate: {info['defaultSampleRate']:.0f} Hz")
        if info['maxInputChannels'] > 0:
            print(f"  - Max input channels: {info['maxInputChannels']}")
        if info['maxOutputChannels'] > 0:
            print(f"  - Max output channels: {info['maxOutputChannels']}")
        print()
    
    # Show default devices
    try:
        default_input = p.get_default_input_device_info()
        print(f"Default input device: {default_input['name']} (ID: {default_input['index']})")
    except OSError:
        print("No default input device found")
    
    try:
        default_output = p.get_default_output_device_info()
        print(f"Default output device: {default_output['name']} (ID: {default_output['index']})")
    except OSError:
        print("No default output device found")
    
    p.terminate()


if __name__ == "__main__":
    list_audio_devices()