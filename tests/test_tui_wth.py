import sys
from unittest.mock import MagicMock
import pytest

# Mock the pyaudio and rwc.streaming modules
sys.modules['pyaudio'] = MagicMock()
sys.modules['rwc.streaming'] = MagicMock()

from textual.pilot import Pilot
from rwc.tui_wth import TuiWth, QuitScreen, MainMenuScreen, FileConversionScreen, AlertScreen, RealTimeConversionScreen

@pytest.mark.anyio
async def test_tui_wth_navigation():
    """Test that the TUI can navigate between screens."""
    app = TuiWth()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Should start on MainMenuScreen
        assert isinstance(app.screen, MainMenuScreen)

        # Press "f" to go to FileConversionScreen
        await pilot.press("f")
        await pilot.pause()

        # Check that we are on the file conversion screen
        assert isinstance(app.screen, FileConversionScreen)

        # Press "b" to go back
        await pilot.press("b")
        await pilot.pause()
        assert isinstance(app.screen, MainMenuScreen)

@pytest.mark.anyio
async def test_tui_wth_quit_dialog():
    """Test that the quit dialog appears and can be cancelled."""
    app = TuiWth()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("q")
        assert isinstance(app.screen, QuitScreen)
        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, MainMenuScreen)

@pytest.mark.anyio
async def test_tui_wth_file_conversion_input():
    """Test that the file conversion screen correctly handles user input."""
    app = TuiWth()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f")
        await pilot.pause()

        # Enter text into the input fields
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("tab")
        for char in "input.wav":
            await pilot.press(char)
        await pilot.press("tab")
        for char in "output.wav":
            await pilot.press(char)
        await pilot.press("tab")
        for char in "12":
            await pilot.press(char)
        await pilot.press("tab")
        for char in "0.5":
            await pilot.press(char)

        # Check that the input fields have the correct values
        assert app.screen.query_one("#input_path").value == "input.wav"
        assert app.screen.query_one("#output_path").value == "output.wav"
        assert app.screen.query_one("#pitch_change").value == "12"
        assert app.screen.query_one("#index_rate").value == "0.5"

@pytest.mark.anyio
async def test_tui_wth_file_conversion_no_model():
    """Test that the file conversion screen correctly handles the case where no model is selected."""
    app = TuiWth()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f")
        await pilot.pause()

        # Press convert without selecting a model
        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, AlertScreen)
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, FileConversionScreen)

@pytest.mark.anyio
async def test_tui_wth_file_conversion_invalid_input():
    """Test that the file conversion screen correctly handles invalid input."""
    app = TuiWth()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f")
        await pilot.pause()

        # Enter invalid text into the input fields
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("tab")
        for char in "abc":
            await pilot.press(char)

        # Press convert
        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, AlertScreen)
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, FileConversionScreen)

@pytest.mark.anyio
async def test_tui_wth_real_time_conversion_no_model():
    """Test that the real-time conversion screen correctly handles the case where no model is selected."""
    app = TuiWth()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()

        # Press start without selecting a model
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, AlertScreen)
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, RealTimeConversionScreen)

@pytest.mark.anyio
async def test_tui_wth_real_time_conversion_invalid_input():
    """Test that the real-time conversion screen correctly handles invalid input."""
    app = TuiWth()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()

        # Enter invalid text into the input fields
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.press("tab")
        for char in "abc":
            await pilot.press(char)

        # Press start
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, AlertScreen)
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, RealTimeConversionScreen)
