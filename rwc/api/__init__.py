"""
RWC API endpoints for voice conversion
"""
import os
import torch
from flask import Flask, request, jsonify, send_file
from rwc.core import VoiceConverter

app = Flask(__name__)

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
    model_path = request.form.get('model_path')
    pitch_change = int(request.form.get('pitch_change', 0))
    index_rate = float(request.form.get('index_rate', 0.75))
    use_rmvpe = request.form.get('use_rmvpe', 'true').lower() in ['true', '1', 'yes', 'on']
    
    if not model_path or not os.path.exists(model_path):
        return jsonify({"error": "Valid model path required"}), 400
    
    # Initialize converter if not already done
    if converter is None or converter.model_path != model_path:
        converter = VoiceConverter(model_path, use_rmvpe=use_rmvpe)
    
    # Save uploaded file temporarily
    input_path = f"/tmp/rwc_input_{id(audio_file)}.wav"
    audio_file.save(input_path)
    
    # Generate output path
    output_path = f"/tmp/rwc_output_{id(audio_file)}.wav"
    
    try:
        # Perform conversion
        result_path = converter.convert_voice(
            input_path, 
            output_path, 
            pitch_change=pitch_change,
            index_rate=index_rate
        )
        
        return send_file(result_path, as_attachment=True)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        # Clean up temporary files
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

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
    app.run(host='0.0.0.0', port=5000, debug=True)