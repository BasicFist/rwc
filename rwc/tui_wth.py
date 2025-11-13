"""
RWC Terminal User Interface (TUI) powered by Textual.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np
import pyaudio
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import (Button, DirectoryTree, Footer, Header, Input,
                           Label, Static)
from textual.worker import Worker, get_current_worker

from rwc.core import VoiceConverter
from rwc.streaming import (BatchConverter, BufferConfig, ConversionConfig,
                           StreamingPipeline)
from rwc.utils.audio_devices import list_audio_devices


class BaseScreen(Screen):
    """Base screen with common components."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()


class QuitScreen(ModalScreen):
    """Screen with a dialog to quit."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Are you sure you want to quit?"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()

    def action_quit(self) -> None:
        self.app.exit()

    def action_cancel(self) -> None:
        self.app.pop_screen()


class AlertScreen(ModalScreen):
    """Screen with a dialog to show an alert."""

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Container(
            Label(self.message),
            Button("OK", variant="primary", id="ok"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()


class FileConvertWorker(Worker):
    """Worker for file conversion."""

    def __init__(
        self,
        model_path: str,
        input_path: str,
        output_path: str,
        pitch_change: int,
        index_rate: float,
    ) -> None:
        super().__init__()
        self.model_path = model_path
        self.input_path = input_path
        self.output_path = output_path
        self.pitch_change = pitch_change
        self.index_rate = index_rate

    def run(self) -> None:
        try:
            converter = VoiceConverter(self.model_path)
            result_path = converter.convert_voice(
                self.input_path,
                self.output_path,
                pitch_shift=self.pitch_change,
                index_rate=self.index_rate,
            )
            self.post_message(f"Conversion successful: {result_path}")
        except Exception as e:
            self.post_message(f"Error: {e}")


class RealTimeConvertWorker(Worker):
    """Worker for real-time conversion."""

    def __init__(
        self,
        model_path: str,
        input_device: int,
        output_device: int,
    ) -> None:
        super().__init__()
        self.model_path = model_path
        self.input_device = input_device
        self.output_device = output_device

    def run(self) -> None:
        worker = get_current_worker()
        p = None
        stream_in = None
        stream_out = None
        pipeline = None
        try:
            p = pyaudio.PyAudio()

            CHUNK = 1024
            FORMAT = pyaudio.paFloat32
            CHANNELS = 1
            RATE = 48000

            conversion_config = ConversionConfig(
                model_path=self.model_path,
                pitch_shift=0,
                index_rate=0.75,
                sample_rate=RATE,
                use_rmvpe=True,
                chunk_size=4096,
            )
            buffer_config = BufferConfig(
                chunk_size=4096, sample_rate=RATE, channels=CHANNELS
            )
            backend = BatchConverter(conversion_config)
            pipeline = StreamingPipeline(backend, buffer_config)
            pipeline.start()

            stream_in = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=self.input_device,
                frames_per_buffer=CHUNK,
            )
            stream_out = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                output_device_index=self.output_device,
                frames_per_buffer=CHUNK,
            )

            while not worker.is_cancelled:
                data = stream_in.read(CHUNK, exception_on_overflow=False)
                audio_array = np.frombuffer(data, dtype=np.float32)
                pipeline.process_input(audio_array)
                processed_audio = pipeline.get_output(CHUNK)
                if processed_audio is None:
                    processed_audio = np.zeros(CHUNK, dtype=np.float32)
                output_data = processed_audio.astype(np.float32).tobytes()
                stream_out.write(output_data)
        except Exception as e:
            self.post_message(f"Error: {e}")
        finally:
            if pipeline:
                pipeline.stop()
            if stream_in:
                stream_in.stop_stream()
                stream_in.close()
            if stream_out:
                stream_out.stop_stream()
                stream_out.close()
            if p:
                p.terminate()


class FileConversionScreen(BaseScreen):
    """Screen for file conversion."""

    BINDINGS = [
        ("c", "convert", "Convert"),
        ("b", "back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.model_path: Optional[str] = None

    def compose(self) -> ComposeResult:
        super().compose()
        yield Container(
            Label("File Conversion"),
            Static("Select a model:"),
            DirectoryTree("./models", id="model_tree"),
            Input(placeholder="Enter input file path", id="input_path"),
            Input(placeholder="Enter output file path", id="output_path"),
            Input(placeholder="Enter pitch change (e.g., 0)", id="pitch_change"),
            Input(placeholder="Enter index rate (e.g., 0.75)", id="index_rate"),
            Button("Convert", id="convert"),
            Button("Back", id="back"),
        )

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        self.model_path = str(event.path)
        self.query_one(Static).update(f"Selected model: {os.path.basename(self.model_path)}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "convert":
            self.action_convert()
        elif event.button.id == "back":
            self.action_back()

    def action_convert(self) -> None:
        if not self.model_path:
            self.app.push_screen(AlertScreen("Please select a model first."))
            return

        input_path = self.query_one("#input_path", Input).value
        output_path = self.query_one("#output_path", Input).value

        try:
            pitch_change = int(self.query_one("#pitch_change", Input).value or 0)
            index_rate = float(self.query_one("#index_rate", Input).value or 0.75)
        except ValueError:
            self.app.push_screen(AlertScreen("Pitch and index rate must be numbers."))
            return

        worker = FileConvertWorker(
            self.model_path, input_path, output_path, pitch_change, index_rate
        )
        worker.watch(self, "on_worker_state_changed")
        worker.start()
        self.app.push_screen(AlertScreen("Conversion started..."))

    def action_back(self) -> None:
        self.app.pop_screen()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.is_finished:
            self.app.pop_screen() # pop the "Conversion started..." screen
            self.app.push_screen(AlertScreen(str(event.worker.result)))


class RealTimeConversionScreen(BaseScreen):
    """Screen for real-time conversion."""

    BINDINGS = [
        ("s", "start", "Start"),
        ("t", "stop", "Stop"),
        ("b", "back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.model_path: Optional[str] = None
        self.worker: Optional[Worker] = None

    def compose(self) -> ComposeResult:
        super().compose()
        yield Container(
            Label("Real-time Conversion"),
            Static("Select a model:"),
            DirectoryTree("./models", id="model_tree"),
            Input(placeholder="Enter input device ID", id="input_device"),
            Input(placeholder="Enter output device ID", id="output_device"),
            Button("Start", id="start"),
            Button("Stop", id="stop"),
            Button("Back", id="back"),
        )

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        self.model_path = str(event.path)
        self.query_one(Static).update(f"Selected model: {os.path.basename(self.model_path)}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self.action_start()
        elif event.button.id == "stop":
            self.action_stop()
        elif event.button.id == "back":
            self.action_back()

    def action_start(self) -> None:
        if self.worker is not None and self.worker.is_running:
            self.app.push_screen(AlertScreen("Conversion is already running."))
            return
        if not self.model_path:
            self.app.push_screen(AlertScreen("Please select a model first."))
            return
        try:
            input_device = int(self.query_one("#input_device", Input).value)
            output_device = int(self.query_one("#output_device", Input).value)
        except ValueError:
            self.app.push_screen(AlertScreen("Device IDs must be numbers."))
            return

        self.worker = RealTimeConvertWorker(self.model_path, input_device, output_device)
        self.worker.start()
        self.app.push_screen(AlertScreen("Real-time conversion started."))

    def action_stop(self) -> None:
        if self.worker is not None and self.worker.is_running:
            self.worker.cancel()
            self.worker = None
            self.app.push_screen(AlertScreen("Real-time conversion stopped."))
        else:
            self.app.push_screen(AlertScreen("Conversion is not running."))

    def action_back(self) -> None:
        if self.worker is not None and self.worker.is_running:
            self.worker.cancel()
            self.worker = None
        self.app.pop_screen()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.is_finished and event.worker.error:
            self.app.push_screen(AlertScreen(str(event.worker.error)))


class ListAudioDevicesScreen(BaseScreen):
    """Screen for listing audio devices."""

    def compose(self) -> ComposeResult:
        super().compose()
        devices = list_audio_devices()
        yield VerticalScroll(Static(devices if devices else "No audio devices found."))
        yield Button("Back", id="back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()


class ListModelsScreen(BaseScreen):
    """Screen for listing models."""

    def compose(self) -> ComposeResult:
        super().compose()
        yield DirectoryTree("./models")
        yield Button("Back", id="back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()


class TuiWth(App):
    """A Textual app for RWC."""

    CSS_PATH = "tui_wth.css"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "request_quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.push_screen(MainMenuScreen())

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())


class MainMenuScreen(BaseScreen):
    """The main menu screen."""

    BINDINGS = [
        ("f", "file_conversion", "File Conversion"),
        ("r", "real_time_conversion", "Real-time Conversion"),
        ("a", "list_audio_devices", "List Audio Devices"),
        ("m", "list_models", "List Models"),
    ]

    def compose(self) -> ComposeResult:
        super().compose()
        yield Container(
            Button("File Conversion", id="file_conversion"),
            Button("Real-time Conversion", id="real_time_conversion"),
            Button("List Audio Devices", id="list_audio_devices"),
            Button("List Models", id="list_models"),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "file_conversion":
            self.app.push_screen(FileConversionScreen())
        elif event.button.id == "real_time_conversion":
            self.app.push_screen(RealTimeConversionScreen())
        elif event.button.id == "list_audio_devices":
            self.app.push_screen(ListAudioDevicesScreen())
        elif event.button.id == "list_models":
            self.app.push_screen(ListModelsScreen())

    def action_file_conversion(self) -> None:
        self.app.push_screen(FileConversionScreen())

    def action_real_time_conversion(self) -> None:
        self.app.push_screen(RealTimeConversionScreen())

    def action_list_audio_devices(self) -> None:
        self.app.push_screen(ListAudioDevicesScreen())

    def action_list_models(self) -> None:
        self.app.push_screen(ListModelsScreen())


if __name__ == "__main__":
    app = TuiWth()
    app.run()
