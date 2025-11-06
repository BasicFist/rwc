#!/bin/bash
# RWC Model Download Script
# This script downloads all required RVC models for the RWC project

set -e

echo "Starting RWC model download..."

# Create models directory structure
mkdir -p models/hubert_base
mkdir -p models/pretrained
mkdir -p models/uvr5_weights
mkdir -p models/rmvpe
mkdir -p models/checkpoints
mkdir -p models/community

echo "Downloading HuBERT base model (used for feature extraction)..."
huggingface-cli download lj1995/VoiceConversionWebUI --include "hubert_base.pt" --local-dir ./models/hubert_base --revision main

# Download RMVPE model (better pitch extraction model)
echo "Downloading RMVPE model (more accurate pitch extraction)..."
huggingface-cli download lj1995/VoiceConversionWebUI --include "rmvpe.pt" --local-dir ./models/rmvpe --revision main

# Download pretrained models
echo "Downloading vocoder models (used for audio synthesis)..."
huggingface-cli download lj1995/VoiceConversionWebUI --include "pretrained/*.pth" --local-dir ./models/pretrained --revision main

# Download UVR5 models
echo "Downloading UVR5 vocal separators (used for audio preprocessing)..."
huggingface-cli download lj1995/VoiceConversionWebUI --include "uvr5_weights/*" --local-dir ./models/uvr5_weights --revision main

# Additional model files that are commonly used
echo "Downloading additional checkpoint models..."
huggingface-cli download lj1995/VoiceConversionWebUI --include "checkpoints/*" --local-dir ./models/checkpoints --revision main

# The following are popular community models you can download separately:
echo
echo "Popular community models (download separately):"
echo "- sail-rvc/HomerSimpson2333333 (8,970 downloads)"
echo "- sail-rvc/Donald_Trump__RVC_v2_ (5,951 downloads)"
echo "- sail-rvc/Hatsune_Miku__RVC_v2_ (2,791 downloads)"
echo "- sail-rvc/ArthurMorgan (1,832 downloads)"
echo "- sail-rvc/Jesse-Pinkman (1,727 downloads)"
echo
echo "To download a community model, use:"
echo "huggingface-cli download <username/model-name> --local-dir ./models/community/<model-name>"
echo
echo "Example:"
echo "huggingface-cli download sail-rvc/HomerSimpson2333333 --local-dir ./models/community/HomerSimpson2333333"
echo
echo "For custom-trained models, you would typically train them using:"
echo "- Your own voice dataset (typically 10-50 minutes of clean audio)"
echo "- RVC training scripts provided in the RVC repository"
echo "- Audio preprocessing tools for noise reduction and normalization"

echo
echo "✓ All models downloaded successfully!"
echo "Models are located in the 'models' directory"
echo "You can now start using RWC for voice conversion"