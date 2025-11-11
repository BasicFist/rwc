"""
Enhanced RWC Terminal User Interface
Provides a navigable menu-driven experience for real-time voice conversion tasks.
"""
from dataclasses import dataclass, field
from typing import Callable, List, Optional
import os
import sys
import time
import shutil
import subprocess
import re

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

try:
    from colorama import Fore, Style, init

    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False

    class _ColorFallback:  # pragma: no cover - simple fallback
        RED = ""
        GREEN = ""
        YELLOW = ""
        BLUE = ""
        MAGENTA = ""
        CYAN = ""
        WHITE = ""
        BRIGHT = ""
        RESET = ""
        NORMAL = ""

    Fore = _ColorFallback()
    Style = _ColorFallback()

from rwc.core import VoiceConverter


def clear_screen():
    """Clear terminal output."""
    os.system("clear" if os.name == "posix" else "cls")


def print_colored(text: str, color=Fore.WHITE, style=Style.NORMAL):
    """Print text with optional color styling."""
    if COLORS_AVAILABLE:
        print(f"{color}{style}{text}")
    else:
        print(text)


@dataclass
class MenuItem:
    key: str
    label: str
    description: str
    handler: Callable[[], None]


@dataclass
class MenuScreen:
    title: str
    subtitle: Optional[str] = None
    items: List[MenuItem] = field(default_factory=list)
    show_back: bool = True

    def get_item(self, key: str) -> Optional[MenuItem]:
        key = key.lower()
        for item in self.items:
            if item.key.lower() == key:
                return item
        return None


class TerminalApp:
    """Menu-driven terminal application for RWC."""

    def __init__(self):
        self.running = True
        self.screen_stack: List[MenuScreen] = []

    # ---------- Navigation helpers ----------
    def run(self):
        """Start the main event loop."""
        self.navigate(self.build_main_menu())

        while self.running and self.screen_stack:
            screen = self.screen_stack[-1]
            self.render_screen(screen)
            choice = input(
                f"{Fore.YELLOW}Select option "
                f"(key, {'b to back, ' if screen.show_back else ''}q to quit): "
                f"{Fore.RESET}"
            ).strip()

            if not choice:
                continue

            if choice.lower() in {"q", "quit"}:
                self.running = False
                break

            if screen.show_back and choice.lower() in {"b", "back"}:
                self.go_back()
                continue

            item = screen.get_item(choice)
            if item:
                try:
                    item.handler()
                except KeyboardInterrupt:
                    print_colored("\nInterrupted. Returning to menu...", Fore.YELLOW)
                    time.sleep(1.5)
                except Exception as exc:
                    print_colored(f"\nError: {exc}", Fore.RED)
                    self.pause("\nPress Enter to continue...")
            else:
                print_colored("Invalid selection. Try again.", Fore.RED)
                time.sleep(1.2)

        clear_screen()
        print_colored("👋 Exiting RWC Terminal Interface. See you soon!", Fore.GREEN)

    def navigate(self, screen: MenuScreen):
        """Push a new menu screen onto the navigation stack."""
        self.screen_stack.append(screen)

    def go_back(self):
        """Return to the previous menu."""
        if len(self.screen_stack) > 1:
            self.screen_stack.pop()
        else:
            self.running = False

    def render_screen(self, screen: MenuScreen):
        """Render the current menu."""
        clear_screen()
        self.print_header()
        print_colored(screen.title, Fore.CYAN, Style.BRIGHT)
        if screen.subtitle:
            print_colored(screen.subtitle, Fore.WHITE)
        print()

        for item in screen.items:
            print_colored(f"[{item.key}] {item.label}", Fore.GREEN, Style.BRIGHT)
            print_colored(f"    {item.description}", Fore.WHITE)

        if screen.show_back:
            print_colored("\n[b] Back to previous menu", Fore.MAGENTA)
        print_colored("[q] Quit", Fore.RED)
        print()

    @staticmethod
    def print_header():
        print_colored("=" * 60, Fore.CYAN, Style.BRIGHT)
        print_colored(
            "              RWC - Real-time Voice Conversion", Fore.MAGENTA, Style.BRIGHT
        )
        print_colored("        Enhanced Navigable Terminal Interface", Fore.CYAN)
        print_colored("=" * 60, Fore.CYAN, Style.BRIGHT)
        print()

    @staticmethod
    def pause(message: str = "Press Enter to return..."):
        input(f"{Fore.CYAN}{message}{Fore.RESET}")

    # ---------- Model helpers ----------
    @staticmethod
    def list_available_models() -> List[str]:
        models_dir = "models"
        if not os.path.exists(models_dir):
            return []

        collected: List[str] = []
        for root, _, files in os.walk(models_dir):
            for file in files:
                if not file.endswith((".pth", ".onnx", ".pt")):
                    continue
                lowered = file.lower()
                if any(skip in lowered for skip in ("hubert", "rmvpe")):
                    continue
                collected.append(os.path.join(root, file))
        return sorted(collected)

    def display_model_catalog(self, models: List[str]):
        if not models:
            print_colored("No models found. Download or link models first.", Fore.RED)
            return

        print_colored(f"Available models ({len(models)}):", Fore.YELLOW, Style.BRIGHT)
        for idx, model in enumerate(models, 1):
            parts = model.split(os.sep)
            summary = "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
            print_colored(f"{idx:2d}. {summary}", Fore.GREEN)
            print_colored(f"    {model}", Fore.BLUE)

    def prompt_model_selection(self) -> Optional[str]:
        models = self.list_available_models()
        if not models:
            print_colored("No models detected. Use Download Models first.", Fore.RED)
            return None

        while True:
            clear_screen()
            self.print_header()
            print_colored("Select a model for conversion", Fore.CYAN, Style.BRIGHT)
            self.display_model_catalog(models)
            print_colored("\n[c] Custom path", Fore.MAGENTA)
            print_colored("[b] Cancel", Fore.RED)
            choice = input(
                f"\n{Fore.YELLOW}Enter model number or key: {Fore.RESET}"
            ).strip()

            if not choice:
                continue
            if choice.lower() in {"b", "back"}:
                return None
            if choice.lower() in {"c", "custom"}:
                custom = input(
                    f"{Fore.YELLOW}Enter full path to model file: {Fore.RESET}"
                ).strip()
                return custom or None

            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(models):
                    return models[idx - 1]
            print_colored("Invalid selection. Try again.", Fore.RED)
            time.sleep(1.2)

    # ---------- Audio helpers ----------
    @staticmethod
    def get_audio_devices() -> List[dict]:
        if not PYAUDIO_AVAILABLE:
            return []

        devices = []
        pa = pyaudio.PyAudio()
        try:
            for idx in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(idx)
                devices.append(
                    {
                        "index": idx,
                        "name": info.get("name", f"Device {idx}"),
                        "max_input": info.get("maxInputChannels", 0),
                        "max_output": info.get("maxOutputChannels", 0),
                        "default_rate": int(info.get("defaultSampleRate", 0) or 0),
                    }
                )
        finally:
            pa.terminate()
        return devices

    @staticmethod
    def detect_default_devices() -> tuple[Optional[int], Optional[int]]:
        if not PYAUDIO_AVAILABLE:
            return None, None
        pa = pyaudio.PyAudio()
        input_idx = output_idx = None
        try:
            try:
                input_idx = pa.get_default_input_device_info().get("index")
            except Exception:
                input_idx = None
            try:
                output_idx = pa.get_default_output_device_info().get("index")
            except Exception:
                output_idx = None
        finally:
            pa.terminate()
        return input_idx, output_idx

    def render_device_overview(self):
        if not PYAUDIO_AVAILABLE:
            print_colored(
                "PyAudio is not installed. Install with `pip install pyaudio`.", Fore.RED
            )
            return

        devices = self.get_audio_devices()
        if not devices:
            print_colored("No audio devices reported by PortAudio.", Fore.RED)
            return

        print_colored("Detected audio devices:", Fore.YELLOW, Style.BRIGHT)
        for device in devices:
            tags = []
            if device["max_input"] > 0:
                tags.append("Input")
            if device["max_output"] > 0:
                tags.append("Output")
            badge = "/".join(tags) if tags else "Unavailable"
            print_colored(
                f"  [{device['index']}] {badge:<12} {device['name']}", Fore.GREEN
            )
            print_colored(
                f"       Rate: {device['default_rate']} Hz | "
                f"In: {device['max_input']} | Out: {device['max_output']}",
                Fore.BLUE,
            )

    # ---------- Input utilities ----------
    @staticmethod
    def prompt_int(prompt: str, default: Optional[int] = None) -> Optional[int]:
        raw = input(prompt).strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            print_colored("Please enter a valid number.", Fore.RED)
            return None

    @staticmethod
    def prompt_float(prompt: str, default: Optional[float] = None) -> Optional[float]:
        raw = input(prompt).strip()
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError:
            print_colored("Please enter a valid number.", Fore.RED)
            return None

    @staticmethod
    def get_pipewire_nodes():
        nodes = {"sinks": [], "sources": []}
        if shutil.which("wpctl") is None:
            return nodes
        try:
            result = subprocess.run(
                ["wpctl", "status"],
                capture_output=True,
                text=True,
                check=True,
            )
        except Exception:
            return nodes

        current = None
        for raw_line in result.stdout.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue

            if "Sinks:" in stripped:
                current = "sinks"
                continue
            if "Sources:" in stripped:
                current = "sources"
                continue
            if stripped.startswith("├─") or stripped.startswith("└─"):
                # Other sub-sections reset the context
                if "Sink endpoints" in stripped or "Source endpoints" in stripped:
                    current = None
                continue

            if current in ("sinks", "sources"):
                clean = stripped.lstrip("│").strip()
                is_default = clean.startswith("*")
                if is_default:
                    clean = clean[1:].strip()

                match = re.match(r"(\d+)\.\s*(.+)", clean)
                if not match:
                    continue

                node_id = int(match.group(1))
                name = match.group(2).split("[", 1)[0].strip()
                nodes[current].append(
                    {"id": node_id, "name": name, "default": is_default}
                )

        return nodes

    def prompt_pipewire_node(
        self, nodes: List[dict], label: str
    ) -> Optional[int]:
        if not nodes:
            print_colored(f"No PipeWire {label.lower()}s detected. Using default.", Fore.YELLOW)
            return None

        print_colored(f"\nAvailable PipeWire {label}s:", Fore.CYAN, Style.BRIGHT)
        for node in nodes:
            marker = "*" if node["default"] else " "
            print_colored(
                f"  {marker} {node['id']:>4} - {node['name']}",
                Fore.GREEN if node["default"] else Fore.WHITE,
            )
        default_id = next((n["id"] for n in nodes if n["default"]), None)
        prompt_default = default_id if default_id is not None else "system default"

        while True:
            raw = input(
                f"{Fore.YELLOW}Select {label} ID (Enter for {prompt_default}): {Fore.RESET}"
            ).strip()
            if not raw:
                return default_id
            if raw.lower() in {"d", "default"}:
                return default_id
            try:
                choice = int(raw)
            except ValueError:
                print_colored("Please enter a numeric ID or leave blank for default.", Fore.RED)
                continue
            if any(node["id"] == choice for node in nodes):
                return choice
            print_colored("Invalid node ID. Try again.", Fore.RED)

    # ---------- Menu builders ----------
    def build_main_menu(self) -> MenuScreen:
        return MenuScreen(
            title="Main Menu",
            subtitle="Use the keys to navigate between workflows.",
            show_back=False,
            items=[
                MenuItem(
                    key="1",
                    label="File Conversion",
                    description="Convert an audio file using an RVC model.",
                    handler=self.action_file_conversion,
                ),
                MenuItem(
                    key="2",
                    label="Real-time Conversion",
                    description="Stream microphone input through the selected model.",
                    handler=self.action_real_time_conversion,
                ),
                MenuItem(
                    key="3",
                    label="Audio Devices",
                    description="Inspect available input/output devices.",
                    handler=self.action_list_devices,
                ),
                MenuItem(
                    key="4",
                    label="Model Catalog",
                    description="List discovered RVC models.",
                    handler=self.action_list_models,
                ),
                MenuItem(
                    key="5",
                    label="System Information",
                    description="GPU, audio, and environment diagnostics.",
                    handler=self.action_system_info,
                ),
                MenuItem(
                    key="6",
                    label="Download Models",
                    description="Fetch baseline or community models via scripts.",
                    handler=self.action_download_models,
                ),
                MenuItem(
                    key="7",
                    label="Help & Tips",
                    description="Quick guidance for working with the TUI.",
                    handler=self.action_help,
                ),
                MenuItem(
                    key="8",
                    label="Exit",
                    description="Close the terminal interface.",
                    handler=self.action_exit,
                ),
            ],
        )

    # ---------- Actions ----------
    def action_file_conversion(self):
        clear_screen()
        self.print_header()
        print_colored("File Conversion Workflow", Fore.CYAN, Style.BRIGHT)

        model_path = self.prompt_model_selection()
        if not model_path:
            print_colored("No model selected.", Fore.YELLOW)
            time.sleep(1.2)
            return

        if not os.path.exists(model_path):
            print_colored(f"Model not found: {model_path}", Fore.RED)
            self.pause()
            return

        input_path = input(
            f"{Fore.YELLOW}Enter input audio path: {Fore.RESET}"
        ).strip()
        if not input_path:
            print_colored("Conversion canceled: no input provided.", Fore.YELLOW)
            time.sleep(1.0)
            return
        if not os.path.exists(input_path):
            print_colored(f"Input file not found: {input_path}", Fore.RED)
            self.pause()
            return

        output_path = input(
            f"{Fore.YELLOW}Enter output path (default output.wav): {Fore.RESET}"
        ).strip() or "output.wav"

        pitch_change = None
        while pitch_change is None:
            pitch_change = self.prompt_int(
                f"{Fore.YELLOW}Pitch change (-24 to 24, default 0): {Fore.RESET}",
                default=0,
            )
        if not (-24 <= pitch_change <= 24):
            print_colored("Pitch change must be between -24 and 24.", Fore.RED)
            self.pause()
            return

        index_rate = None
        while index_rate is None:
            index_rate = self.prompt_float(
                f"{Fore.YELLOW}Index rate (0.0 to 1.0, default 0.75): {Fore.RESET}",
                default=0.75,
            )
        if not (0.0 <= index_rate <= 1.0):
            print_colored("Index rate must be between 0.0 and 1.0.", Fore.RED)
            self.pause()
            return

        use_rmvpe = input(
            f"{Fore.YELLOW}Use RMVPE for pitch extraction? (Y/n): {Fore.RESET}"
        ).strip().lower() in {"", "y", "yes"}

        print_colored("\nRunning conversion...", Fore.CYAN)
        try:
            converter = VoiceConverter(model_path, use_rmvpe=use_rmvpe)
            result_path = converter.convert_voice(
                input_path,
                output_path,
                pitch_change=pitch_change,
                index_rate=index_rate,
            )
            print_colored(
                f"\n✓ Conversion complete. Output saved to: {result_path}",
                Fore.GREEN,
                Style.BRIGHT,
            )
        except Exception as exc:
            print_colored(f"\n✗ Conversion failed: {exc}", Fore.RED)

        self.pause()

    def action_real_time_conversion(self):
        clear_screen()
        self.print_header()
        print_colored("Real-time Conversion Workflow", Fore.CYAN, Style.BRIGHT)

        use_pwcat = shutil.which("pw-cat") is not None
        if not PYAUDIO_AVAILABLE and not use_pwcat:
            print_colored(
                "PyAudio is not available and pw-cat was not found. Install PyAudio or PipeWire CLI tools first.",
                Fore.RED,
            )
            self.pause()
            return

        pipewire_source_id = None
        pipewire_sink_id = None

        if use_pwcat:
            print_colored(
                "\n✔ pw-cat detected. Streaming will use PipeWire devices.",
                Fore.GREEN,
            )
            nodes = self.get_pipewire_nodes()
            pipewire_source_id = self.prompt_pipewire_node(nodes["sources"], "Source")
            pipewire_sink_id = self.prompt_pipewire_node(nodes["sinks"], "Sink")
            input_device = output_device = 0
        else:
            self.render_device_overview()
            default_in, default_out = self.detect_default_devices()
            prompt_in = (
                f"{Fore.YELLOW}Input device ID "
                f"(default {default_in if default_in is not None else 'required'}): "
                f"{Fore.RESET}"
            )
            prompt_out = (
                f"{Fore.YELLOW}Output device ID "
                f"(default {default_out if default_out is not None else 'required'}): "
                f"{Fore.RESET}"
            )

            input_device = None
            while input_device is None:
                input_device = self.prompt_int(prompt_in, default=default_in)

            output_device = None
            while output_device is None:
                output_device = self.prompt_int(prompt_out, default=default_out)

        model_path = self.prompt_model_selection()
        if not model_path:
            print_colored("No model selected.", Fore.YELLOW)
            time.sleep(1.0)
            return
        if not os.path.exists(model_path):
            print_colored(f"Model not found: {model_path}", Fore.RED)
            self.pause()
            return

        use_rmvpe = input(
            f"{Fore.YELLOW}Use RMVPE for pitch extraction? (Y/n): {Fore.RESET}"
        ).strip().lower() in {"", "y", "yes"}

        print_colored("\nStarting real-time conversion...", Fore.CYAN)
        try:
            converter = VoiceConverter(model_path, use_rmvpe=use_rmvpe)
            converter.real_time_convert(
                input_device=input_device,
                output_device=output_device,
                show_meter=True,
                pipewire_source=pipewire_source_id,
                pipewire_sink=pipewire_sink_id,
            )
        except KeyboardInterrupt:
            print_colored("\nReal-time conversion stopped by user.", Fore.YELLOW)
        except Exception as exc:
            print_colored(f"\n✗ Error during real-time conversion: {exc}", Fore.RED)
        finally:
            self.pause()

    def action_list_devices(self):
        clear_screen()
        self.print_header()
        print_colored("Audio Devices", Fore.CYAN, Style.BRIGHT)
        self.render_device_overview()
        self.pause()

    def action_list_models(self):
        clear_screen()
        self.print_header()
        print_colored("Model Catalog", Fore.CYAN, Style.BRIGHT)
        models = self.list_available_models()
        self.display_model_catalog(models)
        self.pause()

    def action_system_info(self):
        clear_screen()
        self.print_header()
        print_colored("System Diagnostics", Fore.CYAN, Style.BRIGHT)

        try:
            import torch
        except ImportError:
            torch = None

        print_colored("\nCUDA Information:", Fore.YELLOW, Style.BRIGHT)
        if torch and torch.cuda.is_available():
            print_colored("  ✓ CUDA available", Fore.GREEN)
            print_colored(f"  ✓ GPU: {torch.cuda.get_device_name(0)}", Fore.GREEN)
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print_colored(f"  ✓ VRAM: {vram:.1f} GB", Fore.GREEN)
        else:
            print_colored("  ✗ CUDA unavailable or torch missing", Fore.RED)

        print_colored("\nAudio Stack:", Fore.YELLOW, Style.BRIGHT)
        if PYAUDIO_AVAILABLE:
            print_colored("  ✓ PyAudio installed", Fore.GREEN)
            devices = self.get_audio_devices()
            inputs = sum(1 for d in devices if d["max_input"] > 0)
            outputs = sum(1 for d in devices if d["max_output"] > 0)
            print_colored(f"  ✓ Input devices: {inputs}", Fore.GREEN)
            print_colored(f"  ✓ Output devices: {outputs}", Fore.GREEN)
        else:
            print_colored("  ✗ PyAudio not installed", Fore.RED)

        print_colored("\nModels:", Fore.YELLOW, Style.BRIGHT)
        models = self.list_available_models()
        print_colored(f"  ✓ Discovered models: {len(models)}", Fore.GREEN)

        print_colored("\nPaths:", Fore.YELLOW, Style.BRIGHT)
        print_colored(f"  • Working directory: {os.getcwd()}", Fore.CYAN)
        print_colored(f"  • Python executable: {sys.executable}", Fore.CYAN)

        self.pause()

    def action_download_models(self):
        submenu = MenuScreen(
            title="Model Downloads",
            subtitle="Choose which helper script to run.",
            show_back=True,
            items=[
                MenuItem(
                    key="1",
                    label="Download baseline models",
                    description="Fetch HuBERT, vocoders, and essentials.",
                    handler=lambda: self.run_download_script("bash download_models.sh"),
                ),
                MenuItem(
                    key="2",
                    label="Download community models",
                    description="Grab the extended collection (includes Homer).",
                    handler=lambda: self.run_download_script(
                        "bash download_additional_models.sh"
                    ),
                ),
                MenuItem(
                    key="3",
                    label="Back to main menu",
                    description="Return without downloading.",
                    handler=self.go_back,
                ),
            ],
        )
        self.navigate(submenu)

    def run_download_script(self, command: str):
        clear_screen()
        self.print_header()
        print_colored(f"Running `{command}`", Fore.CYAN, Style.BRIGHT)
        print_colored("Output will stream below. Press Ctrl+C to abort.\n", Fore.YELLOW)
        try:
            exit_code = os.system(command)
            if exit_code == 0:
                print_colored("\n✓ Download completed successfully.", Fore.GREEN)
            else:
                print_colored(
                    f"\n✗ Script exited with status {exit_code}.", Fore.RED
                )
        except KeyboardInterrupt:
            print_colored("\nDownload canceled by user.", Fore.YELLOW)
        finally:
            self.pause()
            # After script finishes, return to previous menu
            if self.screen_stack and self.screen_stack[-1].title == "Model Downloads":
                self.go_back()

    def action_help(self):
        clear_screen()
        self.print_header()
        print_colored("Help & Tips", Fore.CYAN, Style.BRIGHT)
        print_colored(
            """
📁 File Conversion
  • Converts existing audio files with an RVC model.
  • RMVPE pitch extraction delivers higher quality transitions.

🎤 Real-time Conversion
  • Streams microphone input through the model in real-time.
  • Watch the on-screen mic meter to confirm signal presence.

🔧 Audio Devices
  • Consult device IDs before launching real-time sessions.

📦 Download Models
  • Use helper scripts to populate required checkpoints.

Tips:
  • Keep large model files out of git.
  • Ensure CUDA drivers are current for GPU acceleration.
            """,
            Fore.WHITE,
        )
        self.pause()

    def action_exit(self):
        self.running = False


def main_tui():
    app = TerminalApp()
    app.run()


if __name__ == "__main__":
    main_tui()
