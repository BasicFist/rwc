#!/bin/bash
# Homer Simpson Voice Converter
# A convenience script to convert audio to Homer Simpson's voice

INPUT_FILE=""
OUTPUT_FILE="homer_output.wav"
PITCH_CHANGE=0
INDEX_RATE=0.75

# Parse command line options
while [[ $# -gt 0 ]]; do
    case $F in
        -i|--input)
            INPUT_FILE="$2"
            shift
            shift
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift
            shift
            ;;
        -p|--pitch-change)
            PITCH_CHANGE="$2"
            shift
            shift
            ;;
        -ir|--index-rate)
            INDEX_RATE="$2"
            shift
            shift
            ;;
        -h|--help)
            echo "Homer Simpson Voice Converter"
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -i, --input INPUT_FILE      Input audio file (required)"
            echo "  -o, --output OUTPUT_FILE    Output audio file (default: homer_output.wav)"
            echo "  -p, --pitch-change VALUE    Pitch change value (default: 0)"
            echo "  -ir, --index-rate VALUE     Index rate value (default: 0.75)"
            echo "  -h, --help                  Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if input file is provided
if [ -z "$INPUT_FILE" ]; then
    echo "Error: Input file is required."
    echo "Use -h or --help for usage information."
    exit 1
fi

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' does not exist."
    exit 1
fi

# Activate virtual environment and run conversion
source venv/bin/activate
echo "Converting $INPUT_FILE to Homer Simpson voice..."
echo "Using model: models/community/HomerSimpson2333333/model.pth"
echo "Pitch change: $PITCH_CHANGE, Index rate: $INDEX_RATE"
rwc convert --input "$INPUT_FILE" --model "models/community/HomerSimpson2333333/model.pth" --output "$OUTPUT_FILE" --pitch-change "$PITCH_CHANGE" --index-rate "$INDEX_RATE" --use-rmvpe
echo "Conversion complete! Output saved to: $OUTPUT_FILE"