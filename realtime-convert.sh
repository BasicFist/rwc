#!/bin/bash
# Real-Time Voice Converter
# A convenience script for real-time RVC voice conversion with optimal settings

# Default settings optimized for voice chat
# Note: Can use either full path or just model name (ultimate-rvc will find it in models/ directory)
MODEL="models/HomerSimpson2333333/model.pth"
INPUT_DEVICE=4
OUTPUT_DEVICE=0
CHUNK_SIZE=4096      # ~85ms @ 48kHz (balanced quality/latency)
PITCH_SHIFT=0
INDEX_RATE=0.75
USE_RMVPE=true

# Parse command line options
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -i|--input-device)
            INPUT_DEVICE="$2"
            shift 2
            ;;
        -o|--output-device)
            OUTPUT_DEVICE="$2"
            shift 2
            ;;
        -c|--chunk-size)
            CHUNK_SIZE="$2"
            shift 2
            ;;
        -p|--pitch-shift)
            PITCH_SHIFT="$2"
            shift 2
            ;;
        -r|--index-rate)
            INDEX_RATE="$2"
            shift 2
            ;;
        --no-rmvpe)
            USE_RMVPE=false
            shift
            ;;
        --list-devices)
            source venv/bin/activate
            python -m rwc.utils.list_devices
            exit 0
            ;;
        --low-latency)
            CHUNK_SIZE=2048
            echo "Using low-latency mode (chunk size: 2048)"
            shift
            ;;
        --high-quality)
            CHUNK_SIZE=8192
            echo "Using high-quality mode (chunk size: 8192)"
            shift
            ;;
        -h|--help)
            echo "Real-Time Voice Converter - Phase 1 (500-700ms latency)"
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -m, --model MODEL           RVC model file (default: models/HomerSimpson/model.pth)"
            echo "  -i, --input-device ID       Input device ID (default: 4)"
            echo "  -o, --output-device ID      Output device ID (default: 0)"
            echo "  -c, --chunk-size SIZE       Chunk size in samples (default: 4096)"
            echo "  -p, --pitch-shift VALUE     Pitch shift in semitones -24 to +24 (default: 0)"
            echo "  -r, --index-rate VALUE      Feature retrieval strength 0.0-1.0 (default: 0.75)"
            echo "  --no-rmvpe                  Disable RMVPE pitch extraction (use CREPE)"
            echo "  --list-devices              List available audio devices and exit"
            echo "  --low-latency               Use 2048 chunk size (~450-550ms latency)"
            echo "  --high-quality              Use 8192 chunk size (~700-850ms latency)"
            echo "  -h, --help                  Show this help message"
            echo ""
            echo "Quality/Latency Presets:"
            echo "  --low-latency:   2048 samples (~42ms chunks) → 450-550ms total"
            echo "  [default]:       4096 samples (~85ms chunks) → 550-650ms total (RECOMMENDED)"
            echo "  --high-quality:  8192 samples (~170ms chunks) → 700-850ms total"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Use defaults"
            echo "  $0 --list-devices                     # List audio devices"
            echo "  $0 -m models/Voice/model.pth          # Use different model"
            echo "  $0 --low-latency                      # Minimize latency"
            echo "  $0 -p 2 -r 0.5                        # Custom pitch/index"
            echo ""
            echo "Note: Press Ctrl+C to stop streaming"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information."
            exit 1
            ;;
    esac
done

# Get script directory (works even if called from elsewhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if model file exists
if [ ! -f "$MODEL" ]; then
    echo "Error: Model file '$MODEL' not found."
    echo ""
    echo "Available models:"
    find models/ -name "*.pth" -type f 2>/dev/null | head -10
    echo ""
    echo "Use --list-devices to see audio devices."
    exit 1
fi

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Run: python -m venv venv && source venv/bin/activate && pip install -e ."
    exit 1
fi

source venv/bin/activate

# Display configuration
echo "═══════════════════════════════════════════════════════"
echo "  Real-Time Voice Conversion - Phase 1"
echo "═══════════════════════════════════════════════════════"
echo "Model:         $MODEL"
echo "Input Device:  $INPUT_DEVICE"
echo "Output Device: $OUTPUT_DEVICE"
echo "Chunk Size:    $CHUNK_SIZE samples (~$((CHUNK_SIZE * 1000 / 48000))ms)"
echo "Pitch Shift:   $PITCH_SHIFT semitones"
echo "Index Rate:    $INDEX_RATE"
echo "Pitch Method:  $([ "$USE_RMVPE" = true ] && echo "RMVPE (accurate)" || echo "CREPE (fallback)")"
echo "Expected Latency: 500-700ms"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Starting real-time conversion..."
echo "Press Ctrl+C to stop"
echo ""

# Build command
CMD="rwc real-time \
    --model \"$MODEL\" \
    --input-device $INPUT_DEVICE \
    --output-device $OUTPUT_DEVICE \
    --chunk-size $CHUNK_SIZE \
    --pitch-shift $PITCH_SHIFT \
    --index-rate $INDEX_RATE"

if [ "$USE_RMVPE" = false ]; then
    CMD="$CMD --no-rmvpe"
fi

# Run the command
eval $CMD

echo ""
echo "Real-time conversion stopped."
