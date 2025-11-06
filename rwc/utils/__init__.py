"""
Utility functions for RWC
"""
import os
import subprocess
from pathlib import Path


def download_models():
    """
    Download required RVC models using huggingface-cli
    """
    print("Downloading required RVC models...")
    
    # Create models directory
    models_dir = Path("./models")
    models_dir.mkdir(exist_ok=True)
    
    # Install huggingface_hub if not already installed
    try:
        import huggingface_hub
    except ImportError:
        subprocess.run([os.sys.executable, "-m", "pip", "install", "huggingface-hub"])
    
    # Download HuBERT base model (used for feature extraction)
    print("Downloading HuBERT base model...")
    subprocess.run([
        "huggingface-cli", "download", "fishaudio/hubert_base.pt",
        "--local-dir", str(models_dir / "hubert_base")
    ])
    
    # Download vocoder models (used for audio synthesis)
    print("Downloading vocoder models...")
    subprocess.run([
        "huggingface-cli", "download", "RinaChanNAI/VocoderModels",
        "--local-dir", str(models_dir / "pretrained")
    ])
    
    # Download UVR5 vocal separators (used for audio preprocessing)
    print("Downloading UVR5 vocal separators...")
    subprocess.run([
        "huggingface-cli", "download", "Rejekts/uvr-models",
        "--local-dir", str(models_dir / "uvr5_weights")
    ])
    
    print("Model download complete!")


if __name__ == "__main__":
    download_models()