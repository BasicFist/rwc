#!/bin/bash
# RWC Model Download Script
# This script downloads all required RVC models for the RWC project

set -e

echo "Starting RWC model download..."

# Create models directory structure
mkdir -p models/hubert_base
mkdir -p models/pretrained
mkdir -p models/uvr5_weights

# Download the hubert model - using the correct repository
echo "Downloading HuBERT base model (used for feature extraction)..."
huggingface-cli download lj1995/VoiceConversionWebUI --include "hubert_base.pt" --local-dir ./models/hubert_base --revision main

# Download pretrained models
echo "Downloading vocoder models (used for audio synthesis)..."
huggingface-cli download lj1995/VoiceConversionWebUI --include "pretrained/*.pth" --local-dir ./models/pretrained --revision main

# Download UVR5 models
echo "Downloading UVR5 vocal separators (used for audio preprocessing)..."
huggingface-cli download lj1995/VoiceConversionWebUI --include "uvr5_weights/*" --local-dir ./models/uvr5_weights --revision main

echo
echo "✓ All models downloaded successfully!"
echo "Models are located in the 'models' directory"
echo "You can now start using RWC for voice conversion"