#!/bin/bash
# RWC Startup Script
# Based on RVC deployment patterns for optimal performance

set -e

echo "Starting RWC (Real-time Voice Conversion) service..."

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
else
    echo "Error: venv not found. Please run: python3 -m venv venv"
    exit 1
fi

# Check for CUDA availability
if python3 -c "import torch; print(torch.cuda.is_available())" | grep -q "True"; then
    echo "CUDA is available"
else
    echo "Warning: CUDA is not available. Performance will be reduced."
fi

# Check if models exist
if [ ! -d "models" ]; then
    echo "Models directory not found. You may need to download models first."
    echo "To download basic models, run: bash download_models.sh"
    echo "To download additional models, run: bash download_additional_models.sh"
    echo "Or: python3 -m rwc.utils.download_models"
fi

# Check if RMVPE model exists
if [ ! -f "models/rmvpe/rmvpe.pt" ]; then
    echo "Warning: RMVPE model not found. For better pitch extraction, run:"
    echo "bash download_additional_models.sh"
fi

# Start the RWC service
echo "Starting RWC API server..."
python3 -m rwc.api

echo "RWC service stopped."