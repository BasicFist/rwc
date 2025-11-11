#!/bin/bash
# RWC All-in-One Startup Script
# Launches the enhanced TUI with proper environment setup

set -e

# Define project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."

echo "🚀 Starting RWC Enhanced Terminal Interface..."
echo "📁 Project root: $PROJECT_ROOT"

# Check and activate virtual environment
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "🔌 Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
elif [ -f "$HOME/.venv/rwc/bin/activate" ]; then
    echo "🔌 Activating RWC virtual environment from home..."
    source "$HOME/.venv/rwc/bin/activate"
else
    echo "⚠️  Warning: No virtual environment found at $PROJECT_ROOT/venv or $HOME/.venv/rwc"
    echo "💡 Consider creating one with: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    echo "📋 Continuing without virtual environment..."
fi

# Check Python availability
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.9+"
    exit 1
fi

# Check CUDA availability
if python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then
    echo "✅ CUDA is available"
    GPU_NAME=$(python3 -c "import torch; print(torch.cuda.get_device_name(0))" 2>/dev/null || echo "Unknown")
    echo "🎮 GPU: $GPU_NAME"
else
    echo "⚠️  CUDA is not available. Using CPU."
fi

# Check if models exist
if [ ! -d "$PROJECT_ROOT/models" ] || [ -z "$(ls -A $PROJECT_ROOT/models 2>/dev/null)" ]; then
    echo "⚠️  No models directory found or directory is empty."
    echo "💡 Run: bash $PROJECT_ROOT/download_models.sh"
    echo "💡 Or: bash $PROJECT_ROOT/download_additional_models.sh"
fi

# Launch the enhanced TUI
echo "🎨 Launching Enhanced TUI..."
python3 "$PROJECT_ROOT/rwc/tui_enhanced.py"

echo "👋 RWC Enhanced TUI session ended."