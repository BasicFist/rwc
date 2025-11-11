#!/bin/bash
# RWC Enhanced All-in-One Launcher
# Launches the enhanced Terminal User Interface with comprehensive environment setup

set -e

# Define project root (assumes script is in the project root)
PROJECT_ROOT="$(pwd)"

echo "🌟 RWC Enhanced All-in-One Launcher"
echo "===================================="
echo "📍 Project: $PROJECT_ROOT"
echo "📅 $(date)"
echo

# Function to check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 not found"
        exit 1
    fi
    echo "✅ Python: $(python3 --version 2>&1)"
    
    # Check pip
    if ! command -v pip &> /dev/null; then
        echo "❌ Pip not found"
        exit 1
    fi
    echo "✅ Pip: $(pip --version)"
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        echo "✅ Virtual environment: Found"
    else
        echo "⚠️  Virtual environment: Not found"
        echo "💡 Create with: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    fi
    
    # Check CUDA availability
    if python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then
        GPU_NAME=$(python3 -c "import torch; print(torch.cuda.get_device_name(0))" 2>/dev/null)
        echo "🎮 GPU: $GPU_NAME (CUDA available)"
    else
        echo "💻 GPU: Not available (CPU only)"
    fi
    
    # Check for models
    if [ -d "models" ] && [ -n "$(find models -name '*.pth' -type f | head -n 1 2>/dev/null)" ]; then
        MODEL_COUNT=$(find models -name '*.pth' -type f | wc -l)
        echo "📦 Models: $MODEL_COUNT RVC models found"
    else
        echo "📦 Models: Not found (run: bash download_models.sh)"
    fi
    echo
}

# Function to activate virtual environment if available
activate_venv() {
    if [ -d "venv" ]; then
        echo "🔌 Activating virtual environment..."
        source venv/bin/activate
        echo "📍 Virtual environment activated: $(which python)"
        echo
    else
        echo "⚠️  No virtual environment found. Installing packages directly."
        echo "💡 For best practice, create a venv: python3 -m venv venv"
        echo
    fi
}

# Function to install dependencies if not in venv or missing
install_dependencies() {
    echo "⚙️  Installing dependencies..."
    
    # Install requirements if not already installed or in venv
    pip list | grep -q torch || {
        echo "📦 Installing PyTorch and dependencies..."
        pip install -r requirements.txt
    }
    
    # Verify key packages
    python3 -c "import torch" 2>/dev/null && echo "✅ PyTorch OK" || echo "⚠️  PyTorch check failed"
    python3 -c "import rwc" 2>/dev/null && echo "✅ RWC OK" || echo "⚠️  RWC check failed"
    echo
}

# Function to launch the enhanced TUI
launch_enhanced_tui() {
    echo "🎨 Launching Enhanced TUI..."
    echo "✨ Features included:"
    echo "   • Improved navigation and menus"
    echo "   • Better error handling and validation"
    echo "   • Enhanced audio device detection"
    echo "   • System information panel"
    echo "   • Model download options"
    echo "   • Real-time conversion interface"
    echo
    
    # Launch the enhanced TUI
    export ALSA_PLUGIN_DIR=/usr/lib/x86_64-linux-gnu/alsa-lib
    export ALSA_CONFIG_DIR=/usr/share/alsa
    if command -v pw-jack >/dev/null 2>&1; then
        pw-jack python3 -m rwc.tui_enhanced
    else
        python3 -m rwc.tui_enhanced
    fi
    
    echo
    echo "👋 Enhanced TUI session ended."
}

# Main execution
main() {
    check_prerequisites
    activate_venv
    install_dependencies
    launch_enhanced_tui
}

# Run main function
main "$@"
