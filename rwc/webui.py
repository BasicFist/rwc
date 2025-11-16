"""
RWC Gradio Web Interface
A user-friendly web interface for the Real-time Voice Conversion system
"""
import os
import gradio as gr
import torch
from rwc.core import VoiceConverter

def convert_voice_interface(audio_input, model_path, pitch_change, index_rate, use_rmvpe):
    """
    Gradio interface function for voice conversion
    """
    if not audio_input or not model_path:
        return None, "Please provide both audio file and model path"
    
    if not os.path.exists(model_path):
        return None, f"Model not found: {model_path}"
    
    try:
        # Create output path
        output_path = audio_input.replace('.wav', '_converted.wav')
        
        # Initialize converter and perform conversion
        converter = VoiceConverter(model_path, use_rmvpe=bool(use_rmvpe))
        result_path = converter.convert_voice(
            audio_input,
            output_path,
            pitch_change=int(pitch_change),
            index_rate=float(index_rate)
        )
        
        return result_path, "Conversion completed successfully!"
    
    except Exception as e:
        return None, f"Error during conversion: {str(e)}"

def list_models():
    """
    List available models in the models directory
    """
    models_dir = "models"
    if os.path.exists(models_dir):
        # Look for model files in various subdirectories
        model_files = []
        for root, dirs, files in os.walk(models_dir):
            for file in files:
                if file.endswith(('.pth', '.onnx', '.pt')):
                    # Skip files that are not intended for voice conversion
                    if 'hubert' not in file.lower() and 'rmvpe' not in file.lower():
                        model_files.append(os.path.join(root, file))
        return sorted(model_files)
    return []

# Define the Gradio interface
with gr.Blocks(title="RWC - Real-time Voice Conversion") as demo:
    gr.Markdown("# RWC - Real-time Voice Conversion")
    gr.Markdown("Convert voices in real-time using advanced AI models")
    
    with gr.Tabs():
        with gr.TabItem("File Conversion"):
            with gr.Row():
                with gr.Column():
                    audio_input = gr.Audio(type="filepath", label="Input Audio")
                    model_path = gr.Dropdown(choices=list_models(), label="Model Path", 
                                           value=list_models()[0] if list_models() else None)
                    refresh_btn = gr.Button("Refresh Models")
                    
                    with gr.Row():
                        pitch_change = gr.Slider(minimum=-24, maximum=24, value=0, step=1, label="Pitch Change (semitones)")
                        index_rate = gr.Slider(minimum=0.0, maximum=1.0, value=0.75, step=0.05, label="Index Rate")
                    
                    with gr.Row():
                        use_rmvpe = gr.Checkbox(label="Use RMVPE for pitch extraction (more accurate)", value=True)
                    
                    convert_btn = gr.Button("Convert Voice", variant="primary")
                
                with gr.Column():
                    audio_output = gr.Audio(label="Converted Audio", type="filepath")
                    status_output = gr.Textbox(label="Status", interactive=False)
        
        with gr.TabItem("Real-time Conversion (CLI only)"):
            gr.Markdown(
                "Real-time streaming from the web UI is not yet available. "
                "Use the command-line interface instead to start live conversion."
            )
            gr.Markdown(
                "Run the following command from your terminal, adjusting device IDs "
                "and model path as needed:"
            )
            gr.Code(
                "rwc real-time --input-device 4 --output-device 0 --model /path/to/model.pth",
                language="bash",
            )
    
    convert_btn.click(
        fn=convert_voice_interface,
        inputs=[audio_input, model_path, pitch_change, index_rate, use_rmvpe],
        outputs=[audio_output, status_output]
    )
    
    refresh_btn.click(
        fn=lambda: gr.Dropdown(choices=list_models()),
        inputs=[],
        outputs=[model_path]
    )
    
if __name__ == "__main__":
    print("Starting RWC Web Interface...")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    demo.launch(server_name="0.0.0.0", server_port=7865, share=False)
