"""
Bombonne Clicker — Modern WebView GUI Bridge
Match JS names for seamless integration.
"""
import webview
import json
import os
import sys
import threading
import time
import win32api
import itertools

class BombonneAPI:
    def __init__(self, soda):
        self.soda = soda
        self.soda.refresh_gui = self.refresh
        self._window = None
        self.recording = False
        self.recorded_clicks = []
    
    def refresh(self):
        if self._window:
            self._window.evaluate_js("initUI()")

    def set_window(self, window):
        self._window = window

    # --- Config Management ---
    def get_config(self):
        return self.soda.config

    def set_value(self, section, key, value):
        try:
            if section in self.soda.config and key in self.soda.config[section]:
                self.soda.config[section][key] = value
                self.soda.saveSettings()
                return True
        except Exception as e:
            print(f"Error set_value: {e}")
        return False

    def get_configs(self):
        try:
            return self.soda.getConfigs()
        except:
            return []

    def loadConfig(self, index):
        try:
            configs = self.soda.configs if hasattr(self.soda, 'configs') else self.soda.getConfigs()
            if 0 <= index < len(configs):
                config = configs[index]
                file_path = os.path.join(self.soda.folder_path, 'dev', f"{config['filename']}.json")
                if os.path.isfile(file_path):
                    with open(file_path, encoding="utf-8") as f:
                        self.soda.config = json.load(f)
                    self.soda.saveSettings()
                    if self._window: self._window.evaluate_js("initUI()")
                    return True
        except Exception as e:
            print(f"Error loadConfig: {e}")
        return False

    def saveConfig(self):
        self.soda.saveSettings()

    def openConfigFolder(self):
        try: os.startfile(os.path.join(self.soda.folder_path, 'dev'))
        except: pass

    # --- Clicker Assets ---
    def get_click_sounds(self):
        try:
            items = []
            for file in os.listdir(os.path.join(self.soda.folder_path, 'resource')):
                if file.endswith('.wav'):
                    items.append(file)
            return items
        except:
            return []

    # --- Keybinds ---
    def start_bind(self, bind_type):
        def listen():
            time.sleep(0.3)
            while True:
                for vk in range(1, 255):
                    if vk in (1, 2): continue
                    if win32api.GetAsyncKeyState(vk) & 0x8000:
                        key_name = chr(vk) if 32 <= vk <= 126 else f"VK{vk}"
                        map = {
                            'left': ('left', 'bind'), 'right': ('right', 'bind'),
                            'pot': ('potions', 'potBind'), 'potReset': ('potions', 'potResetBind'),
                            'rod': ('misc', 'rodBind'), 'pearl': ('misc', 'pearlBind')
                        }
                        if bind_type in map:
                            sec, key = map[bind_type]
                            self.soda.config[sec][key] = vk
                            self.soda.saveSettings()
                        
                        if self._window:
                            self._window.evaluate_js(f"document.getElementById('{bind_type}Bind').textContent='{key_name}';document.getElementById('{bind_type}Bind').classList.remove('listening')")
                        return
                time.sleep(0.01)
        threading.Thread(target=listen, daemon=True).start()

    # --- Recorder ---
    def startRecording(self):
        if self.recording: return
        self.recording = True
        self.recorded_clicks = []
        
        def record_loop():
            start_time = time.time()
            while self.recording:
                if win32api.GetAsyncKeyState(0x01) < 0:
                    delta = time.time() - start_time
                    self.recorded_clicks.append(delta)
                    start_time = time.time()
                    if self._window:
                        self._window.evaluate_js(f"document.getElementById('recorderStatus').textContent='Recording: {len(self.recorded_clicks)} clicks'")
                    while win32api.GetAsyncKeyState(0x01) < 0:
                        time.sleep(0.001)
                time.sleep(0.005)

        threading.Thread(target=record_loop, daemon=True).start()
        if self._window: self._window.evaluate_js("document.getElementById('recorderStatus').textContent='Recording started...'")

    def stopRecording(self):
        self.recording = False
        if len(self.recorded_clicks) > 1:
            self.recorded_clicks[0] = 0
            self.soda.config["recorder"]["record"] = self.recorded_clicks
            self.soda.record = itertools.cycle(self.recorded_clicks)
            self.soda.saveSettings()
            
            total = sum(self.recorded_clicks)
            cps = round(len(self.recorded_clicks) / total, 2) if total > 0 else 0
            if self._window:
                self._window.evaluate_js(f"document.getElementById('recorderStatus').textContent='Idle'; document.getElementById('recorderCPS').textContent='{cps} CPS'")
        else:
            if self._window: self._window.evaluate_js("document.getElementById('recorderStatus').textContent='Idle (Record too short)'")

    # --- System ---
    def toggleOnTop(self, value):
        if self._window: self._window.on_top = value

    def selfDestruct(self):
        try: os._exit(0)
        except: pass

def launch_gui(soda, version):
    api = BombonneAPI(soda)
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui', 'index.html')
    
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')
    
    window = webview.create_window(
        f'Bombonne Clicker {version}',
        url=ui_path,
        js_api=api,
        width=980,
        height=720,
        background_color='#0a0a0e',
        resizable=True
    )
    # pywebview uses set_window_icon but icon can also be passed in create_window in some versions
    # We'll stick to a standard path check
    api.set_window(window)
    webview.start()
