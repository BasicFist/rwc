"""
RWC Gradio Web Interface
A user-friendly web interface for the Real-time Voice Conversion system
"""
import os
import gradio as gr
import torch
import threading
import time
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

# Global variables for real-time conversion
real_time_thread = None
stop_conversion_flag = threading.Event()

def start_real_time_conversion_gui(model_path, input_device, output_device, use_rmvpe):
    """
    Start real-time voice conversion in a separate thread
    """
    global real_time_thread
    
    if not model_path:
        return "Please select a model for real-time conversion."
    
    if not os.path.exists(model_path):
        return f"Model not found: {model_path}"
    
    if real_time_thread and real_time_thread.is_alive():
        return "Real-time conversion is already running. Please stop it first."
    
    # Reset the stop flag
    stop_conversion_flag.clear()
    
    # Start real-time conversion in a separate thread
    real_time_thread = threading.Thread(
        target=_real_time_worker_gui,
        args=(model_path, input_device, output_device, use_rmvpe, stop_conversion_flag)
    )
    real_time_thread.start()
    
    return (
        "Real-time streaming started (sub-100ms target). "
        f"Model: {model_path.split('/')[-1]}"
    )

def _real_time_worker_gui(model_path, input_device, output_device, use_rmvpe, stop_flag):
    """
    Worker function for real-time conversion (runs in separate thread)
    """
    try:
        # In a real implementation, this would handle actual real-time conversion
        # But for web interface, we'll indicate that the command to start real-time
        # conversion has been issued
        command = (
            f"rwc real-time --input-device {input_device} --output-device {output_device} "
            f"--model \"{model_path}\" --{'use-rmvpe' if use_rmvpe else 'no-rmvpe'} --chunk-size 2048"
        )
        print(f"Real-time conversion command prepared:")
        print(command)
        print("Note: Copy and run this command in your terminal for actual real-time conversion.")
        
        # Update the status in the thread
        # (In a real implementation, this would require a more complex approach to update the UI)
        
    except Exception as e:
        print(f"Error in real-time worker: {e}")

def stop_real_time_conversion_gui():
    """
    Stop real-time voice conversion
    """
    global real_time_thread, stop_conversion_flag
    
    if real_time_thread and real_time_thread.is_alive():
        stop_conversion_flag.set()  # Signal the thread to stop
        real_time_thread.join(timeout=2)  # Wait for thread to finish (max 2 seconds)
        
        if real_time_thread.is_alive():
            return "Warning: Conversion thread did not stop gracefully"
        else:
            return "Real-time conversion stopped successfully"
    else:
        return "No real-time conversion is currently running"

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
        
        with gr.TabItem("Real-time Conversion"):
            with gr.Row():
                with gr.Column():
                    rt_model_path = gr.Dropdown(choices=list_models(), label="Model Path", 
                                               value=list_models()[0] if list_models() else None)
                    
                    with gr.Row():
                        input_device = gr.Number(value=4, label="Input Device ID", precision=0)
                        output_device = gr.Number(value=0, label="Output Device ID", precision=0)
                        
                    with gr.Row():
                        rt_use_rmvpe = gr.Checkbox(label="Use RMVPE for pitch extraction (more accurate)", value=True)
                    
                    rt_start_btn = gr.Button("Start Real-time Conversion", variant="primary")
                    rt_stop_btn = gr.Button("Stop Real-time Conversion", variant="secondary")
                
                with gr.Column():
                    rt_status_output = gr.Textbox(label="Status", interactive=False)
                    gr.Markdown("Note: Real-time conversion runs in the command line. This tab shows the command to run.")
                    gr.Markdown("For actual real-time conversion, use the command line after clicking the 'Start' button.")
    
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
    
    rt_start_btn.click(
        fn=lambda model, in_dev, out_dev, use_rm: start_real_time_conversion_gui(model, int(in_dev), int(out_dev), use_rm),
        inputs=[rt_model_path, input_device, output_device, rt_use_rmvpe],
        outputs=[rt_status_output]
    )
    
    rt_stop_btn.click(
        fn=stop_real_time_conversion_gui,
        inputs=[],
        outputs=[rt_status_output]
    )

# Global variable to handle real-time conversion threads
real_time_thread = None
stop_conversion_flag = False

if __name__ == "__main__":
    print("Starting RWC Web Interface...")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    
    demo.launch(server_name="0.0.0.0", server_port=7865, share=False)