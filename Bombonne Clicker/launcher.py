"""
Bombonne Clicker — Modern Launcher
Interface: LatenciaX-style WebView
Backend: Soda Clicker Logic
"""
import os
import sys
import json
import threading
import time
import types

# Set working directory to script location
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Mock DearPyGui to prevent import errors and GUI popups from main.py
dpg_mock = types.ModuleType('dearpygui')
dpg_mock.dearpygui = types.ModuleType('dearpygui.dearpygui')

# Mock common DPG functions that might be called at module level or during class init
def mock_func(*args, **kwargs): return None
dpg_mock.dearpygui.create_context = mock_func
dpg_mock.dearpygui.handler_registry = mock_func
dpg_mock.dearpygui.add_key_press_handler = mock_func
dpg_mock.dearpygui.set_item_label = mock_func
dpg_mock.dearpygui.delete_item = mock_func
dpg_mock.dearpygui.create_viewport = mock_func
dpg_mock.dearpygui.setup_dearpygui = mock_func
dpg_mock.dearpygui.show_viewport = mock_func
dpg_mock.dearpygui.start_dearpygui = mock_func
dpg_mock.dearpygui.bind_theme = mock_func
dpg_mock.dearpygui.theme = mock_func
dpg_mock.dearpygui.theme_component = mock_func
dpg_mock.dearpygui.get_value = mock_func
dpg_mock.dearpygui.set_value = mock_func
dpg_mock.dearpygui.configure_item = mock_func

sys.modules['dearpygui'] = dpg_mock
sys.modules['dearpygui.dearpygui'] = dpg_mock.dearpygui

# Now import the backend logic
import main
from main import soda

# Create the backend instance
# The soda() init starts all background threads (clicking, window listening, etc.)
sodaClass = soda()
main.sodaClass = sodaClass # Inject into main module so configListener finds it

# Inject helper to save settings (as main.py saves it in the dpg loop usually)
def saveSettings():
    if sodaClass.config.get("misc", {}).get("saveSettings", True):
        try:
            cfg_path = os.path.join(sodaClass.folder_path, "config.json")
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(sodaClass.config, f, indent=4)
            print(f"[Backend] Config saved to {cfg_path}")
        except Exception as e:
            print(f"[Backend] Save error: {e}")

sodaClass.saveSettings = saveSettings

# Start the Modern UI
from gui import launch_gui

if __name__ == '__main__':
    version = "2.2.0 (Premium Edition)"
    print(f"Starting Bombonne Premium v{version}...")
    try:
        launch_gui(sodaClass, version)
    except Exception as e:
        print(f"GUI Crash: {e}")
    finally:
        saveSettings()
        # Ensure all threads exit
        os._exit(0)
