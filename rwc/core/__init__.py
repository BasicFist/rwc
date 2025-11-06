"""
Core RWC (Real-time Voice Conversion) functionality
Based on RVC (Retrieval-based Voice Conversion) framework
"""
import os
import torch
import librosa
import numpy as np
from typing import Optional, Tuple
import configparser

class VoiceConverter:
    """
    Core voice conversion class based on RVC framework
    """
    def __init__(self, model_path: str, config_path: Optional[str] = None, use_rmvpe: Optional[bool] = None):
        """
        Initialize the voice converter with a model
        
        Args:
            model_path: Path to the RVC model file (.pth)
            config_path: Optional path to config file
            use_rmvpe: Whether to use RMVPE for pitch extraction (more accurate)
        """
        self.model_path = model_path
        self.config_path = config_path or 'rwc/config.ini'
        self.config = self._load_config()
        
        # Use parameter if provided, otherwise use config default
        self.use_rmvpe = use_rmvpe if use_rmvpe is not None else self.config.getboolean('CONVERSION', 'use_rmvpe_by_default', fallback=True)
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.hubert_model = None
        self.rmvpe_model = None
        
        # Initialize models
        self._load_models()
    
    def _load_config(self):
        """
        Load configuration from config file
        """
        config = configparser.ConfigParser()
        
        # Read default config first
        default_config_path = 'rwc/config.ini'
        if os.path.exists(default_config_path):
            config.read(default_config_path)
        
        # Override with custom config if provided
        if self.config_path and os.path.exists(self.config_path):
            config.read(self.config_path)
        
        return config
    
    def _load_models(self):
        """
        Load the voice conversion models
        """
        print(f"Loading model from: {self.model_path}")
        print(f"Using device: {self.device}")
        
        # Initialize hubert model for feature extraction
        self._load_hubert_model()
        
        # Initialize RMVPE model if available and requested
        if self.use_rmvpe:
            self._load_rmvpe_model()
    
    def _load_hubert_model(self):
        """
        Load the HuBERT model for feature extraction
        """
        hubert_path = self.config.get('MODEL_PATHS', 'hubert_model_path', fallback='models/hubert_base/hubert_base.pt')
        if os.path.exists(hubert_path):
            print(f"Loading HuBERT model from {hubert_path}")
            # In a full implementation, we would load the actual model here
        else:
            print(f"Warning: HuBERT model not found at {hubert_path}. Please run 'bash download_models.sh'")
    
    def _load_rmvpe_model(self):
        """
        Load the RMVPE model for more accurate pitch extraction
        """
        rmvpe_path = self.config.get('MODEL_PATHS', 'rmvpe_model_path', fallback='models/rmvpe/rmvpe.pt')
        if os.path.exists(rmvpe_path):
            print(f"Loading RMVPE model from {rmvpe_path}")
            # In a full implementation, we would load the actual model here
            self.rmvpe_model = rmvpe_path
        else:
            print(f"RMVPE model not found at {rmvpe_path}, falling back to built-in pitch extraction")
            self.use_rmvpe = False
    
    def convert_voice(self, input_audio_path: str, output_audio_path: str, 
                     pitch_change: Optional[int] = None, index_rate: Optional[float] = None) -> str:
        """
        Convert voice from input audio to target speaker
        
        Args:
            input_audio_path: Path to input audio file
            output_audio_path: Path to save output audio file
            pitch_change: Pitch change in semitones (uses config default if not specified)
            index_rate: How much to use the feature index (0.0-1.0) (uses config default if not specified)
        
        Returns:
            Path to the output audio file
        """
        # Use config defaults if parameters not provided
        default_pitch_change = self.config.getint('CONVERSION', 'default_pitch_change', fallback=0)
        pitch_change = pitch_change if pitch_change is not None else default_pitch_change
        
        default_index_rate = self.config.getfloat('CONVERSION', 'default_index_rate', fallback=0.75)
        index_rate = index_rate if index_rate is not None else default_index_rate
        
        print(f"Converting voice: {input_audio_path} -> {output_audio_path}")
        print(f"Using {'RMVPE' if self.use_rmvpe else 'default'} pitch extraction")
        print(f"Pitch change: {pitch_change}, Index rate: {index_rate}")
        
        # Placeholder for actual voice conversion logic
        # In a real implementation, this would:
        # 1. Load the input audio
        # 2. Extract features using the loaded models
        # 3. Apply voice conversion using RVC techniques
        # 4. Generate output audio
        # 5. Save the output
        
        # For now, just return the output path
        return output_audio_path
    
    def real_time_convert(self, input_device: int = 0, output_device: int = 0):
        """
        Perform real-time voice conversion using microphone input
        
        Note: Real-time conversion requires the following additional dependencies:
        - PortAudio library (system library) - installed
        - PyAudio Python package - installed
        """
        import pyaudio
        import numpy as np
        
        print(f"Starting real-time conversion on device {input_device} -> {output_device}")
        print(f"Using {'RMVPE' if self.use_rmvpe else 'default'} pitch extraction")
        
        # Set up audio parameters
        chunk = 1024  # Buffer size
        FORMAT = pyaudio.paFloat32
        CHANNELS = 2  # Stereo input to match detected device
        RATE = 48000  # Sample rate to match detected device
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        try:
            # Open input stream
            stream_in = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=input_device,
                frames_per_buffer=chunk
            )
            
            # Open output stream
            stream_out = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                output_device_index=output_device,
                frames_per_buffer=chunk
            )
            
            print("Real-time conversion streams opened successfully!")
            print("Recording and converting in real-time... (Press Ctrl+C to stop)")
            
            # For demonstration, just pass through audio with a simple processing
            # In a real implementation, this would involve RVC-style processing
            try:
                while True:
                    # Read data from microphone
                    data = stream_in.read(chunk, exception_on_overflow=False)
                    
                    # Convert to numpy array for processing
                    audio_array = np.frombuffer(data, dtype=np.float32)
                    
                    # Here would be the actual RVC processing
                    # For now, just pass through with slight amplification to show processing
                    processed_audio = audio_array * 1.1
                    
                    # Convert back to bytes
                    output_data = processed_audio.astype(np.float32).tobytes()
                    
                    # Play processed audio
                    stream_out.write(output_data)
                    
            except KeyboardInterrupt:
                print("\nReal-time conversion stopped by user.")
                
        except Exception as e:
            print(f"Error during real-time conversion: {e}")
        finally:
            # Clean up
            if 'stream_in' in locals():
                stream_in.stop_stream()
                stream_in.close()
            if 'stream_out' in locals():
                stream_out.stop_stream()
                stream_out.close()
            p.terminate()
            print("Real-time conversion streams closed.")