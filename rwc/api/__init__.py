"""
RWC API endpoints for voice conversion
"""
import os
import tempfile
import contextlib
from pathlib import Path
import torch
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from rwc.core import VoiceConverter

app = Flask(__name__)

# Configure upload settings
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Allowed audio file extensions
ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.flac', '.m4a', '.aac', '.ogg'}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_path(path, base_dir="models"):
    """
    Sanitize file paths to prevent directory traversal attacks.

    Args:
        path: User-provided path (relative or absolute)
        base_dir: Allowed base directory (default: "models")

    Returns:
        str: Validated absolute path

    Raises:
        ValueError: If path attempts to escape base_dir
    """
    # Get absolute paths
    base_dir_abs = Path(base_dir).resolve()

    # Resolve the requested path (follows symlinks, resolves ..)
    try:
        requested_path = (base_dir_abs / path).resolve()
    except (ValueError, OSError) as e:
        raise ValueError(f"Invalid path: {e}")

    # Verify the resolved path is within base_dir
    try:
        requested_path.relative_to(base_dir_abs)
    except ValueError:
        raise ValueError(f"Path escapes base directory: {path}")

    # Check if path exists (optional but recommended)
    if not requested_path.exists():
        raise ValueError(f"Path does not exist: {path}")

    return str(requested_path)

# Global converter instance (in a real app, you'd want proper resource management)
converter = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "gpu_available": True if torch.cuda.is_available() else False})

@app.route('/convert', methods=['POST'])
def convert_voice():
    """
    Convert voice using uploaded audio file
    Expects form data with:
    - audio_file: the input audio file
    - model_path: path to the RVC model
    - pitch_change: optional pitch change (default 0)
    - index_rate: optional index rate (default 0.75)
    - use_rmvpe: whether to use RMVPE for pitch extraction (default true)
    """
    global converter
    
    if 'audio_file' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio_file']
    
    if audio_file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(audio_file.filename):
        return jsonify({"error": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
    
    model_path = request.form.get('model_path')
    if not model_path:
        return jsonify({"error": "Model path required"}), 400

    # Validate and sanitize model path
    try:
        model_path = sanitize_path(model_path, base_dir="models")
    except ValueError as e:
        return jsonify({"error": f"Invalid model path: {str(e)}"}), 400
    
    try:
        pitch_change = int(request.form.get('pitch_change', 0))
        # Validate pitch change is in reasonable range
        if pitch_change < -24 or pitch_change > 24:
            return jsonify({"error": "Pitch change must be between -24 and 24"}), 400
    except ValueError:
        return jsonify({"error": "Invalid pitch_change value"}), 400
    
    try:
        index_rate = float(request.form.get('index_rate', 0.75))
        # Validate index rate is in reasonable range
        if index_rate < 0.0 or index_rate > 1.0:
            return jsonify({"error": "Index rate must be between 0.0 and 1.0"}), 400
    except ValueError:
        return jsonify({"error": "Invalid index_rate value"}), 400
    
    use_rmvpe = request.form.get('use_rmvpe', 'true').lower() in ['true', '1', 'yes', 'on']
    
    # Initialize converter if not already done
    if converter is None or converter.model_path != model_path:
        try:
            converter = VoiceConverter(model_path, use_rmvpe=use_rmvpe)
        except Exception as e:
            return jsonify({"error": "Failed to initialize converter"}), 500

    # Use secure temporary files with automatic cleanup
    filename = secure_filename(audio_file.filename)

    # Create temporary file for input
    with tempfile.NamedTemporaryFile(
        mode='wb',
        suffix=os.path.splitext(filename)[1],
        prefix='rwc_input_',
        delete=False
    ) as input_tmp:
        input_path = input_tmp.name
        audio_file.save(input_path)

    # Create temporary file for output
    with tempfile.NamedTemporaryFile(
        mode='wb',
        suffix='.wav',
        prefix='rwc_output_',
        delete=False
    ) as output_tmp:
        output_path = output_tmp.name

    try:
        # Perform conversion
        result_path = converter.convert_voice(
            input_path,
            output_path,
            pitch_change=pitch_change,
            index_rate=index_rate
        )

        # Send file and schedule cleanup
        @contextlib.contextmanager
        def cleanup_after_send():
            try:
                yield
            finally:
                # Cleanup after sending
                for path in [input_path, output_path]:
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                    except OSError:
                        pass  # Best effort cleanup

        with cleanup_after_send():
            return send_file(
                result_path,
                as_attachment=True,
                download_name=f"converted_{os.path.basename(result_path)}"
            )

    except Exception as e:
        # Ensure cleanup even on error
        for path in [input_path, output_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass

        return jsonify({"error": "Conversion failed"}), 500

@app.route('/models', methods=['GET'])
def list_models():
    """List available models"""
    # This would return a list of available RVC models
    model_dir = "models"
    if os.path.exists(model_dir):
        model_files = [f for f in os.listdir(model_dir) if f.endswith('.pth') or f.endswith('.onnx')]
        return jsonify({"models": model_files})
    return jsonify({"models": []})

@app.route('/')
def home():
    """Home endpoint with basic info"""
    return jsonify({
        "name": "RWC - Real-time Voice Conversion API",
        "version": "0.1.0",
        "cuda_available": torch.cuda.is_available(),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    })

if __name__ == '__main__':
    # Never enable debug in production
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    if debug_mode:
        print("⚠️  WARNING: Running in DEBUG mode. Do NOT use in production!")

    app.run(
        host=os.getenv('FLASK_HOST', '127.0.0.1'),  # Bind to localhost by default
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=debug_mode
    )