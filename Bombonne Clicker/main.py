version = "2.0.0 (Bombonne Edition)"
configType = "dev"

import win32api, win32con, win32gui, win32process, psutil, time, threading, random, winsound, os, json, sys, asyncio, itertools, re, keyboard, webbrowser, math
import dearpygui.dearpygui as dpg
from pypresence import Presence
import ping3
import tkinter as tk
from tkinter import simpledialog, messagebox
refresh = False

# Globals for external launcher support
sodaClass = None
checkboxToggleLeftClicker = "checkboxToggleLeftClicker"
checkboxToggleRightClicker = "checkboxToggleRightClicker"
guiWindows = 0
class configListener(dict): # Detecting changes to config
    def __init__(self, initialDict):
        global refresh
        for k, v in initialDict.items():
            if isinstance(v, dict):
                initialDict[k] = configListener(v)

        super().__init__(initialDict)

        self.newver = False
        self.newverid = ""

    def __setitem__(self, item, value):
        if isinstance(value, dict):
            _value = configListener(value)
        else:
            _value = value

        super().__setitem__(item, _value)

        super().__setitem__(item, _value)

        # Wait for sodaClass to be initialized
        if sodaClass is None:
            return

        if hasattr(sodaClass, 'config') and "misc" in sodaClass.config and "saveSettings" in sodaClass.config["misc"]:
            if sodaClass.config["misc"]["saveSettings"]:
                try:
                     json.dump(sodaClass.config, open(os.path.join(sodaClass.folder_path, "config.json"), "w", encoding="utf-8"), indent=4)
                except:
                     pass


class soda():
    def __init__(self):
        self.config = {
            "left": {
                "enabled": False,
                "mode": "Hold",
                "bind": 0,
                "averageCPS": 14,
                "onlyWhenFocused": False,
                "breakBlocks": "None",
                "RMBLock": False,
                "blockHit": False,
                "blockHitChance": 20,
                "bhType": "V2",
                "smartBH": 0,
                "shakeEffect": False,
                "shakeEffectForce": 5,
                "soundPath": "None",
                "workInMenus": False,
                "blatant": False,
                "AutoRod": False,
                "AutoRodChance": 10,
            },
            "right": {
                "enabled": False,
                "mode": "Hold",
                "bind": 0,
                "averageCPS": 14,
                "onlyWhenFocused": False,
                "LMBLock": False,
                "shakeEffect": False,
                "shakeEffectForce": False,
                "soundPath": "None",
                "workInMenus": False,
                "blatant": False,
                "items": False
            },
            "recorder": {
                "enabled": False,
                "record": [0.08] # Default 12 CPS
            },
            "overlay": {
                "enabled": False,
                "onlyWhenFocused": True,
                "x": 0,
                "y": 0
            },
            "misc": {
                "saveSettings": True,
                "guiHidden": False,
                "bindHideGUI": 0,
                "consoleFaker": "NullBind",
                "discordRichPresence": False,
                "switchDelay": 0.1,
                "rodBind": 0,
                "longRod": False,
                "rodDelay": 0.2,
                "rodSlot": "2",
                "pearlBind": 0,
                "pearlSlot": "8",
                "swordSlot": "1",
                "theme": "purple",
                "red": 0,
                "green": 0,
                "blue": 0,
                "toggleSounds": True,
                "ping": 230
            },
            "potions": {
                "enabled": False,
                "potBind": 0,
                "throwDelay": 0.7,
                "switchBackSlot": "1",
                "potResetBind": 0,
                "lowestSlot": 1,
                "highestSlot": 9,
            },
            "movement": {
                "autoWTap": False,
                "wTapMode": "chance",
                "wTapValue": 30,
                "autoSprint": False,
                "betterInput": False,
                "fastStop": False,
            },
            "filename": "config",
            "displayName": "Default",
            "description": "Default Config",
            "Author": "Antoine"
        }
        self.current_pot_slot = 0 

        self.newver = False
        self.newverid = ""

        # Check if the Soda Folder exists, if not create it
        self.folder_path = os.getcwd()

        # Only create folder if it doesn't exist
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path, exist_ok=True)
            print("Created Soda Folder in User Profile:", self.folder_path)

        #if not os.path.exists(os.path.join(folder_path, "resource")):
        # Removed auto-download logic for safety
        print("Using local resources.")

        # Load config if the file exists
        file_path = os.path.join(self.folder_path, "config.json")
        if os.path.isfile(file_path):
            try:
                with open(file_path, encoding="utf-8") as f:
                    config = json.load(f)
                print("Loaded config from:", file_path)
                isConfigOk = True
                for key in self.config:
                    if key not in config or len(self.config[key]) != len(config[key]) and key not in ["filename", "displayName", "description", "Author"]:
                        isConfigOk = False
                        print("Invalid Config, Reset at " + key + f" len({len(self.config[key])}) != " + f"len({len(config[key])})")
                        break

                if isConfigOk:
                    if not config["misc"]["saveSettings"]:
                        self.config["misc"]["saveSettings"] = False
                    else:
                        self.config = config
                        # Force onlyWhenFocused to False for testing purposes
                        self.config["left"]["onlyWhenFocused"] = False
                        self.config["right"]["onlyWhenFocused"] = False
            except Exception as e:
                print("Error loading config:", e)
                print("Using default config")

        print("====================\nBombonne Clicker - Antoine\n====================")
        print("Version:", version)
        print("====================")

        configs = []
        clickSounds = []
        self.config = configListener(self.config)
        self.lastBlockHit = 0

        self.lastRClick = 0

        self.inputData = {
            "w": False,
            "a": False,
            "s": False,
            "d": False
        }

        self.inputData2 = {
            "w": False,
            "a": False,
            "s": False,
            "d": False,
            "jump": 0
        }
        
        self.bIDate = 0

        self.record = itertools.cycle(self.config["recorder"]["record"])

        threading.Thread(target=self.discordRichPresence, daemon=True).start()
        
        threading.Thread(target=self.windowListener, daemon=True).start()
        threading.Thread(target=self.leftBindListener, daemon=True).start()
        threading.Thread(target=self.rightBindListener, daemon=True).start()
        threading.Thread(target=self.hideGUIBindListener, daemon=True).start()
        threading.Thread(target=self.bindListener, daemon=True).start()

        threading.Thread(target=self.wTapListener, daemon=True).start()
        threading.Thread(target=self.autoSprint, daemon=True).start()
        threading.Thread(target=self.betterInput, daemon=True).start()
        self.bIDate = 0
        threading.Thread(target=self.fastStopThread, daemon=True).start()   

        threading.Thread(target=self.leftClicker, daemon=True).start()
        threading.Thread(target=self.rightClicker, daemon=True).start()

        threading.Thread(target=self.smartBH, daemon=True).start()

    def discordRichPresence(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        try:
            discordRPC = Presence("1400790093312032808")
            discordRPC.connect()

            startTime = time.time()

            states = [
                "Bombonne V2",
                "Get good <3",
                "Clicks sponsored by Antoine",
                "Best Clicker",
                "Simply The Best",
                "Bombonne on Top",
                "I could use this for advertising 🤔",
                "Click click click",
                ":3",
                "Bombonne <3",
                "Download today!"
            ]

            while True:
                if self.config["misc"]["discordRichPresence"]:
                    discordRPC.update(state=random.choice(states), start=startTime, large_image="logo", large_text="Bombonne Clicker", buttons=[{"label": "Bombonne", "url": "https://github.com/Dream23322/Soda-Autoclicker/"}])
                else:
                    discordRPC.clear()

                time.sleep(15)
        except:
            print("Discord not found running or installed")
            return

    def windowListener(self):
        while True:
            currentWindow = win32gui.GetForegroundWindow()
            self.realTitle = win32gui.GetWindowText(currentWindow)
            self.window = win32gui.FindWindow("LWJGL", None)

            try:
                self.focusedProcess = psutil.Process(win32process.GetWindowThreadProcessId(currentWindow)[-1]).name()
            except:
                self.focusedProcess = ""

            time.sleep(0.5)

    def betterInput(self):
        while True:
            # Check enabled and the game is focused
            if(not self.config["movement"]["betterInput"] or not self.isFocused("left", "onlyWhenFocused", "workInMenus")):
                time.sleep(0.1)
                continue

            a_down = win32api.GetAsyncKeyState(0x41) & 0x8000
            d_down = win32api.GetAsyncKeyState(0x44) & 0x8000

 
            if self.inputData["a"] and d_down:
                win32api.keybd_event(0x41, 0, win32con.KEYEVENTF_KEYUP, 0)
                a_down = False
                self.bIDate = time.time()

            elif self.inputData["d"] and a_down:
                win32api.keybd_event(0x44, 0, win32con.KEYEVENTF_KEYUP, 0)
                d_down = False
                self.bIDate = time.time()

            self.inputData["a"] = a_down
            self.inputData["d"] = d_down

    def fastStopThread(self):
        while True:
            if(not self.config["movement"]["fastStop"] or not self.isFocused("left", "onlyWhenFocused", "workInMenus")):
                time.sleep(0.1)
                continue

            # Check if jump is pressed
            if win32api.GetAsyncKeyState(0x20) & 0x8000:
                self.inputData2["jump"] = time.time()

            w_down = win32api.GetAsyncKeyState(0x57) & 0x8000
            s_down = win32api.GetAsyncKeyState(0x53) & 0x8000
            a_down = win32api.GetAsyncKeyState(0x41) & 0x8000
            d_down = win32api.GetAsyncKeyState(0x44) & 0x8000

            if(time.time() - self.inputData2["jump"] > 0.7 and time.time() - self.bIDate > 0.7):
                skip = False
                if(not w_down and not s_down and self.inputData2["w"]):
                    # Tap S
                    win32api.keybd_event(0x53, 0, 0, 0)
                    time.sleep(0.045)
                    win32api.keybd_event(0x53, 0, win32con.KEYEVENTF_KEYUP, 0)
                    skip = True

                if(not s_down and not w_down and self.inputData2["s"]):
                    # Tap W
                    win32api.keybd_event(0x57, 0, 0, 0)
                    time.sleep(0.045)
                    win32api.keybd_event(0x57, 0, win32con.KEYEVENTF_KEYUP, 0)
                    skip = True

                if(not a_down and not d_down and self.inputData2["a"] and not skip):
                    # Tap D
                    win32api.keybd_event(0x44, 0, 0, 0)
                    time.sleep(0.045)
                    win32api.keybd_event(0x44, 0, win32con.KEYEVENTF_KEYUP, 0)

                if(not d_down and not a_down and self.inputData2["d"] and not skip):
                    # Tap A
                    win32api.keybd_event(0x41, 0, 0, 0)
                    time.sleep(0.045)
                    win32api.keybd_event(0x41, 0, win32con.KEYEVENTF_KEYUP, 0)

            self.inputData2["w"] = w_down
            self.inputData2["s"] = s_down
            self.inputData2["a"] = a_down
            self.inputData2["d"] = d_down


    def click(self):
        winsound.PlaySound(os.path.join(self.folder_path, self.config["left"]["soundPath"]), winsound.SND_ASYNC)

    def toggleSound(self, key):
        if self.config["misc"]["toggleSounds"]:
            if self.config[key]["enabled"]:
                if os.path.exists(os.path.join(self.folder_path, "resource", "notify_on.wav")):
                    winsound.PlaySound(os.path.join(self.folder_path, "resource", "notify_on.wav"), winsound.SND_ASYNC)
            else:
                if os.path.exists(os.path.join(self.folder_path, "resource", "notify_off.wav")):
                    winsound.PlaySound(os.path.join(self.folder_path, "resource", "notify_off.wav"), winsound.SND_ASYNC)

    def leftClicker(self):
        while True:
            if not self.config["recorder"]["enabled"]:
                if self.config["left"]["blatant"]:
                    delay = 1 / self.config["left"]["averageCPS"]
                else:
                    delay = random.random() % (2 / self.config["left"]["averageCPS"])
            else:
                delay = float(next(self.record))

            should_click = self.config["left"]["enabled"]
            
            if should_click and self.config["left"]["mode"] == "Hold":
                 smartBH_Active = self.config["left"]["smartBH"] != 0 and (win32api.GetAsyncKeyState(self.config["left"]["smartBH"]) & 0x8000)
                 if not (win32api.GetAsyncKeyState(0x01) & 0x8000) or smartBH_Active:
                     should_click = False

            if should_click:
                if self.config["left"]["RMBLock"]:
                    if win32api.GetAsyncKeyState(0x02) & 0x8000:
                        time.sleep(delay)

                        continue

                if self.config["left"]["onlyWhenFocused"]:
                    if not "java" in self.focusedProcess and not "AZ-Launcher" in self.focusedProcess:
                        time.sleep(delay)

                        continue

                    if not self.config["left"]["workInMenus"]:
                        cursorInfo = win32gui.GetCursorInfo()[1]
                        if cursorInfo > 50000 and cursorInfo < 100000:
                            time.sleep(delay)

                            continue

                if self.config["left"]["onlyWhenFocused"]:
                    self.leftClick(True)
                else:
                    self.leftClick(None)

            time.sleep(delay)
    def doRod(self, val):
        # Switch to the rod slot
        char_to_vk = {
            '0': 0x30,
            '1': 0x31,
            '2': 0x32,
            '3': 0x33,
            '4': 0x34,
            '5': 0x35,
            '6': 0x36,
            '7': 0x37,
            '8': 0x38,
            '9': 0x39,
        }
        # Use rodSlot to get the slot number
        VK_2 = char_to_vk.get(self.config["misc"]["rodSlot"], None)

        # Press the '2' key
        win32api.keybd_event(VK_2, 0, 0, 0)
        time.sleep(round(float(self.config["misc"]["rodDelay"]) / 10, 3))  # Brief pause to simulate a key press
        # Release the '2' key
        win32api.keybd_event(VK_2, 0, win32con.KEYEVENTF_KEYUP, 0)
        # Send Rod by right clicking
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
        time.sleep(0.001)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
        dly = float(self.config["misc"]["rodDelay"]) * 2 if val and self.config["misc"]["longRod"] else float(self.config["misc"]["rodDelay"])
        # dly = 0
        # if (val and self.config["misc"]["longRod"]):
        #     dly = float(self.config["misc"]["rodDelay"]) * 2
        # else:
        #     dly = float(self.config["misc"]["rodDelay"])
        time.sleep(dly)  # Brief pause to simulate a key press
        # Switch back to slot 1
        VK_2 = 0x31

        # Press the '2' key
        win32api.keybd_event(VK_2, 0, 0, 0)
        time.sleep(float(self.config["misc"]["rodDelay"]) / 10)  # Brief pause to simulate a key press
        # Release the '2' key
        win32api.keybd_event(VK_2, 0, win32con.KEYEVENTF_KEYUP, 0)

    def doPotion(self):
        if(self.config["potions"]["lowestSlot"] > self.current_pot_slot):
            self.current_pot_slot = self.config["potions"]["lowestSlot"]
        else:
            if(self.current_pot_slot <= self.config["potions"]["highestSlot"]):
                
                # Switch to the potion slot
                char_to_vk = {
                    '0': 0x30,
                    '1': 0x31,
                    '2': 0x32,
                    '3': 0x33,
                    '4': 0x34,
                    '5': 0x35,
                    '6': 0x36,
                    '7': 0x37,
                    '8': 0x38,
                    '9': 0x39,
                }
                VK_TO_SLOT = char_to_vk.get(str(self.current_pot_slot), None)

                # Press the slot key
                win32api.keybd_event(VK_TO_SLOT, 0, 0, 0)
                time.sleep(int(self.config["potions"]["throwDelay"]))

                win32api.keybd_event(VK_TO_SLOT, 0, win32con.KEYEVENTF_KEYUP, 0)
                # Send Rod by right clicking
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
                time.sleep(0.6)

                win32api.keybd_event(char_to_vk.get(self.config["misc"]["swordSlot"]), 0, 0, 0)
                self.current_pot_slot += 1



            else:
                print("No Potions Left!")

    def clickLeft(self):
        if self.config["left"]["breakBlocks"] == "Shift With Click" and win32api.GetAsyncKeyState(0x10) & 0x8000:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            time.sleep(0.001)
            return False
        if self.config["left"]["breakBlocks"] == "Shift No Click" and win32api.GetAsyncKeyState(0x10) & 0x8000:

            return False
        if self.config["left"]["breakBlocks"] == "Full":
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            time.sleep(0.001)
            return False
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        time.sleep(0.001)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        return True

    def blockHit(self):
        if self.config["left"]["blockHit"] and win32api.GetAsyncKeyState(0x01) < 0 and random.uniform(0, 1) <= self.config["left"]["blockHitChance"] / 100.0:
            if self.config["left"]["bhType"] == "V2" or self.config["left"]["bhType"] == "V3":
                # Always blockhit every ~ping ms
                ping_ms = self.config["left"].get("ping", 230)
                interval = ping_ms / 1000.0  # seconds

                now = time.time()

                interval = random.randint(450, 550) / 1000.0 if self.config["left"]["bhType"] == "V3" else interval
                if now - self.lastBlockHit >= interval:
                    self.lastBlockHit = now
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
                    delay = 0.02 if self.config["left"]["bhType"] == "V2" else 0.173
                    time.sleep(delay)
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)

            else:
                # Chance-based blockhit (old behavior)

                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)

    def leftClick(self, focused):
        print("hmmm")
        if focused != None:
            if(self.clickLeft()):
                print(" one")
                self.blockHit()
                if self.config["left"]["AutoRod"] or (self.config["left"]["AutoRod"] and self.config["right"]["enabled"] and self.config["right"]["RMBLock"] and not win32api.GetAsyncKeyState(0x01) < 0):
                    if random.uniform(0, 1) <= self.config["left"]["AutoRodChance"] / 100.0 and not win32api.GetAsyncKeyState(self.config["left"]["smartBH"]) != 0:
                        self.doRod(False)
        else:
            if(self.clickLeft()):
                self.blockHit()
                print(" two")
                if self.config["left"]["AutoRod"] or (self.config["left"]["AutoRod"] and self.config["right"]["enabled"] and self.config["right"]["RMBLock"] and not win32api.GetAsyncKeyState(0x01) < 0):
                    if random.uniform(0, 1) <= self.config["left"]["AutoRodChance"] / 100.0:
                        self.doRod(False)

        if self.config["left"]["soundPath"] != "" and os.path.isfile(os.path.join(self.folder_path, self.config["left"]["soundPath"])):
            threading.Thread(target=self.click, args=(), daemon=True).start()

        if self.config["left"]["shakeEffect"]:
            currentPos = win32api.GetCursorPos()
            direction = random.randint(0, 3)
            pixels = random.randint(-self.config["left"]["shakeEffectForce"], self.config["left"]["shakeEffectForce"])

            if direction == 0:
                win32api.SetCursorPos((currentPos[0] + pixels, currentPos[1] - pixels))
            elif direction == 1:
                win32api.SetCursorPos((currentPos[0] - pixels, currentPos[1] + pixels))
            elif direction == 2:
                win32api.SetCursorPos((currentPos[0] + pixels, currentPos[1] + pixels))
            elif direction == 3:
                win32api.SetCursorPos((currentPos[0] - pixels, currentPos[1] - pixels))

    def leftBindListener(self):
        while True:
            try:
                # Check key usage if bind is valid (not 0 and not NONE)
                bind = self.config["left"]["bind"]
                if bind != 0 and win32api.GetAsyncKeyState(bind) & 0x8000:
                    if not self.isFocused("left", "onlyWhenFocused", "workInMenus"):
                        time.sleep(0.1)
                        continue

                    # Toggle enabled state
                    self.config["left"]["enabled"] = not self.config["left"]["enabled"]
                    self.toggleSound('left')
                    self.saveSettings() # Persist state for UI
                    
                    if hasattr(self, 'refresh_gui'):
                        self.refresh_gui()

                    # Wait for key release to prevent rapid toggling
                    while win32api.GetAsyncKeyState(bind) & 0x8000:
                        time.sleep(0.01)
            except:
                pass
            time.sleep(0.01)

    def rightClicker(self):
        while True:
            if self.config["right"]["blatant"]:
                delay = 1 / self.config["right"]["averageCPS"]
            else:
                delay = random.random() % (2 / self.config["right"]["averageCPS"])

            should_click = self.config["right"]["enabled"]
            
            if should_click and self.config["right"]["mode"] == "Hold":
                 smartBH_Active = self.config["left"]["smartBH"] != 0 and (win32api.GetAsyncKeyState(self.config["left"]["smartBH"]) & 0x8000)
                 if not (win32api.GetAsyncKeyState(0x02) & 0x8000) or smartBH_Active:
                     should_click = False

            if should_click:
                if self.config["right"]["LMBLock"]:
                    if win32api.GetAsyncKeyState(0x01) & 0x8000:
                        time.sleep(delay)

                        continue

                if self.config["right"]["onlyWhenFocused"]:
                    if not "java" in self.focusedProcess and not "AZ-Launcher" in self.focusedProcess:
                        time.sleep(delay)

                        continue
            
                    if not self.config["right"]["workInMenus"]:
                        cursorInfo = win32gui.GetCursorInfo()[1]
                        if cursorInfo > 50000 and cursorInfo < 100000:
                            time.sleep(delay)

                            continue

                if self.config["right"]["onlyWhenFocused"]:
                    self.rightClick(True)
                else:
                    self.rightClick(None)

            time.sleep(delay)
    def doPearl(self):
        # Switch to the rod slot
        char_to_vk = {
            '0': 0x30,
            '1': 0x31,
            '2': 0x32,
            '3': 0x33,
            '4': 0x34,
            '5': 0x35,
            '6': 0x36,
            '7': 0x37,
            '8': 0x38,
            '9': 0x39,
        }
        # Use rodSlot to get the slot number
        VK_2 = char_to_vk.get(self.config["misc"]["pearlSlot"], None)
        # Press the '2' key
        win32api.keybd_event(VK_2, 0, 0, 0)
        time.sleep(0.06)  # Brief pause to simulate a key press
        # Release the '2' key
        win32api.keybd_event(VK_2, 0, win32con.KEYEVENTF_KEYUP, 0)
        # Send Rod by right clicking
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
        time.sleep(0.001)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
        # Switch back to slot 1
        VK_2 = char_to_vk.get(self.config["misc"]["swordSlot"], None)
        # Press the '2' key
        win32api.keybd_event(VK_2, 0, 0, 0)
        time.sleep(0.8)
        # Release the '2' key
        win32api.keybd_event(VK_2, 0, win32con.KEYEVENTF_KEYUP, 0)        
    def rightClick(self, focused):
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
        if not self.config["right"]["items"]:
            time.sleep(0.001)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)

        if self.config["right"]["soundPath"] != "" and os.path.isfile(os.path.join(self.folder_path, self.config["right"]["soundPath"])):
            threading.Thread(target=self.click, args=(), daemon=True).start()

        if self.config["right"]["shakeEffect"]:
            currentPos = win32api.GetCursorPos()
            direction = random.randint(0, 3)
            pixels = random.randint(-self.config["right"]["shakeEffectForce"], self.config["right"]["shakeEffectForce"])

            if direction == 0:
                win32api.SetCursorPos((currentPos[0] + pixels, currentPos[1] - pixels))
            elif direction == 1:
                win32api.SetCursorPos((currentPos[0] - pixels, currentPos[1] + pixels))
            elif direction == 2:
                win32api.SetCursorPos((currentPos[0] + pixels, currentPos[1] + pixels))
            elif direction == 3:
                win32api.SetCursorPos((currentPos[0] - pixels, currentPos[1] - pixels))

    def rightBindListener(self):
        while True:
            try:
                bind = self.config["right"]["bind"]
                if bind != 0 and win32api.GetAsyncKeyState(bind) & 0x8000:
                    if not self.isFocused("right", "onlyWhenFocused", "workInMenus"):
                        time.sleep(0.1)
                        continue

                    self.config["right"]["enabled"] = not self.config["right"]["enabled"]
                    self.toggleSound('right')
                    self.saveSettings()
                    
                    if hasattr(self, 'refresh_gui'):
                        self.refresh_gui()

                    while win32api.GetAsyncKeyState(bind) & 0x8000:
                        time.sleep(0.01)
            except:
                pass
            time.sleep(0.01)

    def smartBH(self):
        nums = [{0.21, 0.23, 0.24}, {0.05, 0.06}]
        lastClick = 0
        lastRClick = 0
        clickingL = False
        clickingR = False
        while True:
            if(not win32api.GetAsyncKeyState(self.config["left"]["smartBH"]) != 0 or not self.isFocused("left", "onlyWhenFocused", "workInMenus")):
                time.sleep(0.1)
                continue

            # # # left click
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            time.sleep(0.02)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

            time.sleep(0.1)

            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
            time.sleep(0.15)

            if(win32api.GetAsyncKeyState(self.config["left"]["smartBH"]) != 0):
                time.sleep(0.1)
                #time.sleep(random.choice(list(nums[0])))
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
                time.sleep(random.choice(list(nums[1])))
            else:
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
                time.sleep(0.1)

            # Temp, find hit timing
            # if(win32api.GetAsyncKeyState(0x01) < 0 and clickingL == False):
            #     clickingL = True

            # if(not win32api.GetAsyncKeyState(0x01) != 0 and clickingL == True):
            #     print("L : ", time.time() - lastClick)
            #     lastClick = time.time()
            #     clickingL = False
            
            # if(win32api.GetAsyncKeyState(0x02) < 0 and clickingR == False):
            #     clickingR = True
            #     print("Diff : ", time.time() - lastClick)

            # if(not win32api.GetAsyncKeyState(0x02) != 0 and clickingR == True):
            #     print("R : ", time.time() - lastRClick)
            #     lastRClick = time.time()
            #     clickingR = False
            


                
    def isFocused(self, config1: str, config2: str, config3: str):
        return ("java" in self.focusedProcess or "AZ-Launcher" in self.focusedProcess or not self.config[config1][config2])
    def bindListener(self):
        while True:
            if win32api.GetAsyncKeyState(self.config["misc"]["rodBind"]) != 0 and self.isFocused("left", "onlyWhenFocused", "workInMenus"):
                self.doRod(True)
            elif win32api.GetAsyncKeyState(self.config["misc"]["pearlBind"]) != 0 and self.isFocused("left", "onlyWhenFocused", "workInMenus"):
                self.doPearl()
            elif win32api.GetAsyncKeyState(self.config["potions"]["potBind"]) != 0 and self.isFocused("left", "onlyWhenFocused", "workInMenus"):
                self.doPotion()
                time.sleep(0.5)

            elif win32api.GetAsyncKeyState(self.config["potions"]["potResetBind"]) != 0:
                self.current_pot_slot = int(self.config["potions"]["lowestSlot"])

            time.sleep(0.001)
            
    def hideGUIBindListener(self):
        while True:
            if win32api.GetAsyncKeyState(self.config["misc"]["bindHideGUI"]) != 0:
                self.config["misc"]["guiHidden"] = not self.config["misc"]["guiHidden"]
                if(self.config["misc"]["consoleFaker"] == "NullBind"):
                    print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nNullBind - 1.0.4 Beta\n\n\n\n\n\n")
                elif(self.config["misc"]["consoleFaker"] == "Optimiser"):
                    print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nEntropy Optimiser - 1.0.4 Beta\n\n\n\n\n\n")
                else:
                    print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nBetterRGB - 1.0.4 Beta\n\n\n\n\n\n")
                if not self.config["misc"]["guiHidden"]:
                    if guiWindows: win32gui.ShowWindow(guiWindows, win32con.SW_SHOW)
                else:
                    if guiWindows: win32gui.ShowWindow(guiWindows, win32con.SW_HIDE)

                while win32api.GetAsyncKeyState(self.config["misc"]["bindHideGUI"]) != 0:
                    time.sleep(0.001)

            time.sleep(0.001)

    def wTapListener(self):
        lastMouseX = 0
        lastMouseY = 0
        while True:
            time.sleep(0.01)
            
            if not self.isFocused("left", "onlyWhenFocused", "workInMenus") or not win32api.GetAsyncKeyState(0x1) < 0 or not self.config["movement"]["autoWTap"]:
                time.sleep(0.5)
                continue

            validStrafe = (win32api.GetAsyncKeyState(0x41) < 0 or win32api.GetAsyncKeyState(0x44) < 0) and win32api.GetAsyncKeyState(0x57) < 0
            validAim = (win32api.GetCursorPos()[0] != lastMouseX or win32api.GetCursorPos()[1] != lastMouseY)

            if validStrafe and validAim and (random.uniform(0, 1) <= self.config["movement"]["wTapValue"] / 100.0 and self.config["movement"]["wTapMode"] == "chance" or self.config["movement"]["wTapMode"] == "delay"):
                win32api.keybd_event(0x57, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.05)
                win32api.keybd_event(0x57, 0, 0, 0)
                if(self.config["movement"]["wTapMode"] == "delay"):
                    time.sleep(self.config["movement"]["wTapValue"] / 100.0)
                
                

            lastMouseX, lastMouseY = win32api.GetCursorPos()
                
    def autoSprint(self):
        while True:
            if not self.isFocused("left", "onlyWhenFocused", "workInMenus") or not self.config["movement"]["autoSprint"]:
                time.sleep(0.5)
                continue
            time.sleep(0.01)
            if self.config["movement"]["autoSprint"] and (win32api.GetAsyncKeyState(0x57) < 0 or win32api.GetAsyncKeyState(0x41) < 0 or win32api.GetAsyncKeyState(0x44) < 0) and self.isFocused("left", "onlyWhenFocused", "workInMenus"):
                if not win32api.GetAsyncKeyState(0x11) < 0: 
                    win32api.keybd_event(0x11, 0, 0, 0) 
            else:
                if win32api.GetAsyncKeyState(0x11) < 0: 
                    win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)

    def getConfigs(self):
        configs = []
        folder = os.path.join(self.folder_path, 'dev')

        print("All files:", os.listdir(folder))

        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)

            if not file.endswith(".json"):
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    config = json.load(f)
                config["filename"] = os.path.splitext(file)[0] 
                configs.append(config)
                print("Loaded config:", file)
            except Exception as e:
                print(f"[!] Failed to load {file}: {e}")
        self.configs = configs
        return configs
    
    def loadConfig(self, sender, app_data, user_data):
        cid = user_data if user_data is not None else 0
        print("Config Amount", len(self.configs), "\nConfig ID", cid)
        if cid < 0 or cid >= len(self.configs):
            print(f"[!] Invalid config index: {cid}")
            return
        config = self.configs[cid]
        print(f"[!] Applying Config: {config['filename']}")
        file_path = os.path.join(self.folder_path, 'dev', f"{config['filename']}.json")
        if os.path.isfile(file_path):
            try:
                with open(file_path, encoding="utf-8") as f:
                    config = json.load(f)
                    self.config = config
                print("Loaded config from:", file_path)
                print("Config:")
                print(self.config)
                isConfigOk = True
                json.dump(self.config, open(os.path.join(self.folder_path, "config.json"), "w", encoding="utf-8"), indent=4)
                
            except Exception as e:
                print(f"Failed to load config from {file_path}: {e}")
                isConfigOk = False

    def getClickSounds(self):
        clickSounds = []
        clickSounds.append("None")
        folder = os.path.join(self.folder_path, 'resource')

        print("All files:", os.listdir(folder))

        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)

            if not file.endswith(".wav") or file == "notify_on.wav" or file == "notify_off.wav":
                continue
            clickSounds.append(file)
            #print("Loaded " + file.title)
        self.clickSounds = clickSounds
        return clickSounds

    def openConfigFolder(self):
        folder_path = os.path.join(self.folder_path, 'dev')
        if os.path.exists(folder_path):
            try:
                os.startfile(folder_path)
                print("Opened config folder:", folder_path)
            except Exception as e:
                print(f"Failed to open config folder: {e}")
        else:
            print("[!] Config folder does not exist:", folder_path)

if __name__ == "__main__":
    try:
        if os.name != "nt":
            input("Bombonne Clicker is only working on Windows.")
            os._exit(0)

        currentWindow = win32gui.GetForegroundWindow()
        processName = psutil.Process(win32process.GetWindowThreadProcessId(currentWindow)[-1]).name()
        # Removed console hiding for safety

        sodaClass = soda()
        dpg.create_context()

        def toggleLeftClicker(id: int, value: bool):
            sodaClass.config["left"]["enabled"] = value

        waitingForKeyLeft = False
        def statusBindLeftClicker(id: int):
            global waitingForKeyLeft

            if not waitingForKeyLeft:
                with dpg.handler_registry(tag="Left Bind Handler"):
                    dpg.add_key_press_handler(callback=setBindLeftClicker)

                dpg.set_item_label(buttonBindLeftClicker, "...")

                waitingForKeyLeft = True

        def setBindLeftClicker(id: int, value: str):
            global waitingForKeyLeft
            if waitingForKeyLeft:
                key = keyboard.read_event(suppress=True).name  # Get actual key name
                virtual_key = ord(key.upper())  # Convert to virtual key code
                sodaClass.config["left"]["bind"] = virtual_key
                dpg.set_item_label(buttonBindLeftClicker, f"Bind: {key.upper()}")
                dpg.delete_item("Left Bind Handler")
                waitingForKeyLeft = False

        def statusBindSmartBH(id: int):
            global waitingForKeyLeft

            if not waitingForKeyLeft:
                with dpg.handler_registry(tag="Smart BH Bind Handler"):
                    dpg.add_key_press_handler(callback=setBindSmartBH)

                dpg.set_item_label(buttonBindSmartBH, "...")

                waitingForKeyLeft = True

        def setBindSmartBH(id: int, value: str):
            global waitingForKeyLeft
            if waitingForKeyLeft:
                key = keyboard.read_event(suppress=True).name  # Get actual key name
                virtual_key = ord(key.upper())  # Convert to virtual key code
                sodaClass.config["left"]["smartBH"] = virtual_key
                dpg.set_item_label(buttonBindSmartBH, f"Bind: {key.upper()}")
                dpg.delete_item("Smart BH Bind Handler")
                waitingForKeyLeft = False

        def setLeftMode(id: int, value: str):
            sodaClass.config["left"]["mode"] = value

        def setLeftAverageCPS(id: int, value: int):
            sodaClass.config["left"]["averageCPS"] = value

        def toggleLeftOnlyWhenFocused(id: int, value:bool):
            sodaClass.config["left"]["onlyWhenFocused"] = value

        def setLeftBreakBlocks(id: int, value: str):
            sodaClass.config["left"]["breakBlocks"] = value

        def toggleLeftRMBLock(id: int, value: bool):
            sodaClass.config["left"]["RMBLock"] = value

        def toggleLeftBlockHit(id: int, value: bool):
            sodaClass.config["left"]["blockHit"] = value

        def setLeftBlockHitChance(id: int, value: int):
            sodaClass.config["left"]["blockHitChance"] = value

        def toggleLeftBlockHitHold(id: int, value: str):
            sodaClass.config["left"]["bhType"] = value

        def toggleLeftShakeEffect(id: int, value: bool):
            sodaClass.config["left"]["shakeEffect"] = value

        def setLeftShakeEffectForce(id: int, value: int):
            sodaClass.config["left"]["shakeEffectForce"] = value

        def setLeftClickSoundPath(id: int, value: str):
            sodaClass.config["left"]["soundPath"] = "resource\\" + value

        def toggleLeftWorkInMenus(id: int, value: bool):
            sodaClass.config["left"]["workInMenus"] = value

        def toggleLeftBlatantMode(id: int, value: bool):
            sodaClass.config["left"]["blatant"] = value

        def toggleRightClicker(id: int, value: bool):
            sodaClass.config["right"]["enabled"] = value

        def toggleLeftAutoRod(id: int, value: bool):
            sodaClass.config["left"]["AutoRod"] = value

        def setLeftAutoRodChance(id: int, value: int):
            sodaClass.config["left"]["AutoRodChance"] = value

        def toggleWTap(id: int, value: bool):
            sodaClass.config["movement"]["autoWTap"] = value

        def setWTapValue(id: int, value: int):
            sodaClass.config["movement"]["wTapValue"] = value

        def setWTapMode(id: int, value: str):
            sodaClass.config["movement"]["wTapMode"] = value

        
        def setToggleSounds(id: int, value: bool):
            sodaClass.config["misc"]["toggleSounds"] = value

        def toggleAutoSprint(id: int, value: bool):
            sodaClass.config["movement"]["autoSprint"] = value

        def toggleBetterInput(id: int, value: bool):
            sodaClass.config["movement"]["betterInput"] = value

        def toggleFastStop(id: int, value: bool):
            sodaClass.config["movement"]["fastStop"] = value

        waitingForKeyRight = False
        def statusBindRightClicker(id: int):
            global waitingForKeyRight

            if not waitingForKeyRight:
                with dpg.handler_registry(tag="Right Bind Handler"):
                    dpg.add_key_press_handler(callback=setBindRightClicker)

                dpg.set_item_label(buttonBindRightClicker, "...")

                waitingForKeyRight = True

        def setBindRightClicker(id: int, value: str):
            global waitingForKeyRight
            if waitingForKeyRight:
                key = keyboard.read_event(suppress=True).name
                virtual_key = ord(key.upper())
                sodaClass.config["right"]["bind"] = virtual_key
                dpg.set_item_label(buttonBindRightClicker, f"Bind: {key.upper()}")
                dpg.delete_item("Right Bind Handler")
                waitingForKeyRight = False
        def statusBindRod(id: int):
            global waitingForKeyRight

            if not waitingForKeyRight:
                with dpg.handler_registry(tag="Rod Bind Handler"):
                    dpg.add_key_press_handler(callback=setBindRod)

                dpg.set_item_label(buttonBindRodKey, "...")

                waitingForKeyRight = True

        def setBindRod(id: int, value: str):
            global waitingForKeyRight
            if waitingForKeyRight:
                key = keyboard.read_event(suppress=True).name
                virtual_key = ord(key.upper())
                sodaClass.config["misc"]["rodBind"] = virtual_key
                dpg.set_item_label(buttonBindRodKey, f"Bind: {key.upper()}")
                dpg.delete_item("Rod Bind Handler")
                waitingForKeyRight = False

        def statusBindPearl(id: int):
            global waitingForKeyRight
            if not waitingForKeyRight:
                with dpg.handler_registry(tag="Pearl Bind Handler"):
                    dpg.add_key_press_handler(callback=setBindPearl)

                dpg.set_item_label(buttonBindPearlKey, "...")

                waitingForKeyRight = True
        
        def setBindPearl(id: int, value: str):
            global waitingForKeyRight
            if waitingForKeyRight:
                key = keyboard.read_event(suppress=True).name
                virtual_key = ord(key.upper())
                sodaClass.config["misc"]["pearlBind"] = virtual_key
                dpg.set_item_label(buttonBindPearlKey, f"Bind: {key.upper()}")
                dpg.delete_item("Pearl Bind Handler")
                waitingForKeyRight = False

        def statusBindPot(id: int):
            global waitingForKeyRight
            if not waitingForKeyRight:
                with dpg.handler_registry(tag="Pot Bind Handler"):
                    dpg.add_key_press_handler(callback=setBindPot)

                dpg.set_item_label(buttonBindPotKey, "...")

                waitingForKeyRight = True
        
        def setBindPot(id: int, value: str):
            global waitingForKeyRight
            if waitingForKeyRight:
                key = keyboard.read_event(suppress=True).name
                virtual_key = ord(key.upper())
                sodaClass.config["potions"]["potBind"] = virtual_key
                dpg.set_item_label(buttonBindPotKey, f"Bind: {key.upper()}")
                dpg.delete_item("Pot Bind Handler")
                waitingForKeyRight = False

        def statusBindPotReset(id: int):
            global waitingForKeyRight
            if not waitingForKeyRight:
                with dpg.handler_registry(tag="Pot Reset Bind Handler"):
                    dpg.add_key_press_handler(callback=setBindPotReset)

                dpg.set_item_label(buttonBindPotResetKey, "...")

                waitingForKeyRight = True

        def setBindPotReset(id: int, value: str):
            global waitingForKeyRight
            if waitingForKeyRight:
                key = keyboard.read_event(suppress=True).name
                virtual_key = ord(key.upper())
                sodaClass.config["potions"]["potResetBind"] = virtual_key
                dpg.set_item_label(buttonBindPotResetKey, f"Bind: {key.upper()}")
                dpg.delete_item("Pot Reset Bind Handler")
                waitingForKeyRight = False
        def setRodSlot(id: int, value: str):
            sodaClass.config["misc"]["rodSlot"] = value
        def setSwordSlot(id: int, value: str):
            sodaClass.config["misc"]["swordSlot"] = value
        def setPearlSlot(id: int, value: str):
            sodaClass.config["misc"]["pearlSlot"] = value
        def setRightMode(id: int, value: str):
            sodaClass.config["right"]["mode"] = value
        def setPotDelay(id: int, value: float):
            sodaClass.config["potions"]["throwDelay"] = value
        def setRightAverageCPS(id: int, value: int):
            sodaClass.config["right"]["averageCPS"] = value
        def toggleRightOnlyWhenFocused(id: int, value: int):
            sodaClass.config["right"]["onlyWhenFocused"] = True

        def toggleRightLMBLock(id: int, value: bool):
            sodaClass.config["right"]["LMBLock"] = value

        def toggleRightShakeEffect(id: int, value: bool):
            sodaClass.config["right"]["shakeEffect"] = value

        def setRightShakeEffectForce(id: int, value: int):
            sodaClass.config["right"]["shakeEffectForce"] = value

        def setRightClickSoundPath(id: int, value: str):
            sodaClass.config["right"]["soundPath"] = "resource\\" + value

        def toggleRightWorkInMenus(id: int, value: bool):
            sodaClass.config["right"]["workInMenus"] = value

        def toggleRightBlatantMode(id: int, value: bool):
            sodaClass.config["right"]["blatant"] = value

        def toggleRightItems(id: int, value: bool):
            sodaClass.config["right"]["items"] = value

        def toggleRecorder(id: int, value: bool):
            sodaClass.config["recorder"]["enabled"] = value

        recording = False
        def recorder():
            global recording

            recording = True
            dpg.set_value(recordingStatusText, f"Recording: True")

            recorded = []
            start = 0

            while True:
                if not recording:
                    if len(recorded) < 2: # Avoid saving a record with 0 click
                        recorded[0] = 0.08
                    else:
                        recorded[0] = 0 # No delay for the first click

                        del recorded[-1] # Deleting last record time because that's when you click on stop button and it can take some time

                    sodaClass.config["recorder"]["record"] = recorded

                    sodaClass.record = itertools.cycle(recorded)

                    totalTime = 0
                    for clickTime in recorded:
                        totalTime += float(clickTime)

                    dpg.set_value(averageRecordCPSText, f"Average CPS of previous Record: {round(len(recorded) / totalTime, 2)}")

                    break

                if win32api.GetAsyncKeyState(0x01) < 0:
                    recorded.append(time.time() - start)

                    dpg.set_value(recordingStatusText, f"Recording: True - Recorded clicks: {len(recorded)}")

                    start = time.time()

                    while win32api.GetAsyncKeyState(0x01) < 0:
                        time.sleep(0.001)
        def setRodDelay(id: int, value: float):
            sodaClass.config["misc"]["rodDelay"] = value

        def setLongRod(id: int, value: bool):
            sodaClass.config["misc"]["longRod"] = value

        def setLowestSlot(id: int, value: int):
            sodaClass.config["potions"]["lowestSlot"] = value

        def setHighestSlot(id: int, value: int):
            sodaClass.config["potions"]["highestSlot"] = value

        def setSwitchDelay(id: int, value: float):
            sodaClass.config["potions"]["switchDelay"] = value
        def startRecording():
            if not recording:
                threading.Thread(target=recorder, daemon=True).start()

        def togglePotions(id:int, value: bool):
            sodaClass.config["potions"]["enabled"] = value

        def setTheme(id: int, value: str):
            sodaClass.config["misc"]["theme"] = value

        def setConsoleFaker(id: int, value: str):
            sodaClass.config["misc"]["consoleFaker"] = value

        def stopRecording():
            global recording

            recording = False

            dpg.set_value(recordingStatusText, f"Recording: False")

        def selfDestruct():
            dpg.destroy_context()

        waitingForKeyHideGUI = False
        def statusBindHideGUI():
            global waitingForKeyHideGUI

            if not waitingForKeyHideGUI:
                with dpg.handler_registry(tag="Hide GUI Bind Handler"):
                    dpg.add_key_press_handler(callback=setBindHideGUI)

                dpg.set_item_label(buttonBindHideGUI, "...")

                waitingForKeyHideGUI = True

        # set RGB
        def setRed(id: int, value: int):
            sodaClass.config["misc"]["red"] = value

        def setGreen(id: int, value: int):
            sodaClass.config["misc"]["green"] = value

        def setBlue(id: int, value: int):
            sodaClass.config["misc"]["blue"] = value 
        def setBindHideGUI(id: int, value: str):
            global waitingForKeyHideGUI
            if waitingForKeyHideGUI:
                key = keyboard.read_event(suppress=True).name
                virtual_key = ord(key.upper())
                sodaClass.config["misc"]["bindHideGUI"] = virtual_key
                dpg.set_item_label(buttonBindHideGUI, f"Bind: {key.upper()}")
                dpg.delete_item("Hide GUI Bind Handler")
                waitingForKeyHideGUI = False


        def setPing(id: int, value: int):
            sodaClass.config["misc"]["ping"] = value
        
        def autoPing(id: int):
            # get ping to hypixel (speedtest.chicago.linode.com is used bc hypixel uses proxy servers)
            try:
                ping = ping3.ping("speedtest.chicago.linode.com", unit='ms')
                if ping is not None:
                    ping += 10
                    sodaClass.config["misc"]["ping"] = int(ping)
                    dpg.set_value(pingSlider, int(ping))
            except Exception as e:
                print(f"[!] Failed to ping: {e}")
                sodaClass.config["misc"]["ping"] = 100

        def toggleSaveSettings(id: int, value: bool):
            sodaClass.config["misc"]["saveSettings"] = value

        def toggleLeftBreakShift(id: int, value: bool):
            sodaClass.config["left"]["breakShift"] = value


        def configEditor(id: int):
            currentConfig = sodaClass.config

            def save():
                #savebutton = tk.Button(root, text="Save", command=nope).pack(pady=10)
                sodaClass.config["displayName"] = name_var.get()
                sodaClass.config["Author"] = author_var.get()
                sodaClass.config["description"] = desc_var.get()
                sodaClass.config["filename"] = filename_var.get()
                file_path = os.path.join(sodaClass.folder_path, 'dev', f"{sodaClass.config['filename']}.json")
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(sodaClass.config, f, indent=4)
                    messagebox.showinfo("Config Editor", f"Saved config: {sodaClass.config['filename']}.json")
                    root.destroy()
                except Exception as e:
                    messagebox.showerror("Config Editor", f"Failed to save config: {e}")
                    time.sleep(3)

                time.sleep(1)

            root = tk.Tk()
            root.title("Config Editor")
            root.geometry("400x300")
            root.resizable(False, False)

            tk.Label(root, text="Config Editor").pack(pady=5)

            tk.Label(root, text="Name").pack()
            name_var = tk.StringVar(value=currentConfig.get("displayName", ""))
            tk.Entry(root, textvariable=name_var).pack()

            tk.Label(root, text="Author").pack()
            author_var = tk.StringVar(value=currentConfig.get("Author", ""))
            tk.Entry(root, textvariable=author_var).pack()

            tk.Label(root, text="Description").pack()
            desc_var = tk.StringVar(value=currentConfig.get("description", ""))
            tk.Entry(root, textvariable=desc_var).pack()

            tk.Label(root, text="Filename").pack()
            filename_var = tk.StringVar(value=currentConfig.get("filename", ""))
            tk.Entry(root, textvariable=filename_var).pack()

            savebutton = tk.Button(root, text="Save", command=save, ).pack(pady=10)

            root.mainloop()

        def toggleAlwaysOnTop(id: int, value: bool):
            if value:
                win32gui.SetWindowPos(guiWindows, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            else:
                win32gui.SetWindowPos(guiWindows, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

        def toggleDiscordRPC(id: int, value: bool):
            sodaClass.config["misc"]["discordRichPresence"] = value
        try:
            dpg.create_context()

            dpg.create_viewport(title=f"Bombonne Clicker {version}", width=900, height=700, small_icon="bombonne.ico", large_icon="bombonne.ico")

            def add_info(text):
                dpg.add_text("[?]", color=(88, 0, 230))
                with dpg.tooltip(dpg.last_item()):
                    dpg.add_text(text, wrap=350, color=(180, 180, 195))

            with dpg.window(tag="Primary Window"):
                # ═══ BRANDED HEADER ═══
                with dpg.group(horizontal=True):
                    dpg.add_text("BOMBONNE", color=(120, 40, 255))
                    dpg.add_text(f"  v{version}", color=(90, 90, 110))
                dpg.add_separator()
                dpg.add_spacer(height=6)

                clicks = sodaClass.getClickSounds()
                with dpg.tab_bar():
                    with dpg.tab(label="  Left Clicker  "):
                        dpg.add_spacer(height=6)
                        
                        with dpg.group(horizontal=True):
                            checkboxToggleLeftClicker = dpg.add_checkbox(label="Toggle", default_value=sodaClass.config["left"]["enabled"], callback=toggleLeftClicker)
                            buttonBindLeftClicker = dpg.add_button(label="Click to Bind", callback=statusBindLeftClicker)
                            dropdownLeftMode = dpg.add_combo(items=["Hold", "Always"], width=100, default_value=sodaClass.config["left"]["mode"], callback=setLeftMode)
                            add_info("Hold: Click while holding left mouse button\nAlways: Click regardless of mouse state")

                            bind = sodaClass.config["left"]["bind"]
                            if bind != 0:
                                dpg.set_item_label(buttonBindLeftClicker, f"Bind: {chr(bind)}")

                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            sliderLeftAverageCPS = dpg.add_slider_int(label="Average CPS", default_value=sodaClass.config["left"]["averageCPS"], min_value=1, max_value=50, width=250, callback=setLeftAverageCPS)
                            add_info("Clicks Per Second (Average)")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            checkboxLeftBlockHit = dpg.add_checkbox(label="BlockHit", default_value=sodaClass.config["left"]["blockHit"], callback=toggleLeftBlockHit)
                            add_info("Randomly right clicks to do a blockhit (MC version < 1.8.9).\nHelpful for reducing damage taken.")

                        with dpg.group(horizontal=True):
                            sliderLeftBlockHitChance = dpg.add_slider_int(label="BlockHit Chance", default_value=sodaClass.config["left"]["blockHitChance"], min_value=1, max_value=100, width=200, callback=setLeftBlockHitChance)

                        with dpg.group(horizontal=True):
                            dpg.add_combo(label="BlockHit Type", items=["V1", "V2", "V3"], width=100, default_value=sodaClass.config["left"]["bhType"], callback=toggleLeftBlockHitHold)
                            add_info("V1: Normal\nV2: Ping based (Better)\nV3: Hold based")
                        
                        with dpg.group(horizontal=True):
                            buttonBindSmartBH = dpg.add_button(label="Smart BH Bind", callback=statusBindSmartBH)
                            bind = sodaClass.config["left"]["smartBH"]
                            if bind != 0:
                                dpg.set_item_label(buttonBindSmartBH, f"Bind: {chr(bind)}")

                        dpg.add_spacer(width=125)

                        with dpg.group(horizontal=True):
                            checkboxLeftShakeEffect = dpg.add_checkbox(label="Shake Effect", default_value=sodaClass.config["left"]["shakeEffect"], callback=toggleLeftShakeEffect)
                            add_info("Adds random movement to cursor to simulate human error/jitter.")
                            
                        with dpg.group(horizontal=True):
                            sliderLeftShakeEffectForce = dpg.add_slider_int(label="Shake Force", default_value=sodaClass.config["left"]["shakeEffectForce"], min_value=1, max_value=20, width=200, callback=setLeftShakeEffectForce)

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            dropDownLeftClickSound = dpg.add_combo(label="Click Sound", items=clicks, width=150, default_value=sodaClass.config["left"]["soundPath"], callback=setLeftClickSoundPath)
                            add_info("Play a sound for every click generated.")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            checkboxLeftOnlyWhenFocused = dpg.add_checkbox(label="Only In Game", default_value=sodaClass.config["left"]["onlyWhenFocused"], callback=toggleLeftOnlyWhenFocused)
                            add_info("Only click when Minecraft is the active window.")
                        
                        with dpg.group(horizontal=True):
                            checkboxLeftRMBLock = dpg.add_checkbox(label="RMB-Lock", default_value=sodaClass.config["left"]["RMBLock"], callback=toggleLeftRMBLock)
                            add_info("Stop clicking when Right Mouse Button is held.")
                        
                        with dpg.group(horizontal=True):
                            checkboxLeftWorkInMenus = dpg.add_checkbox(label="Work in Menus", default_value=sodaClass.config["left"]["workInMenus"], callback=toggleLeftWorkInMenus)
                            add_info("Allow clicking while in inventory/menus.")
                        
                        with dpg.group(horizontal=True):
                            checkboxLeftBlatantMode = dpg.add_checkbox(label="Blatant Mode", default_value=sodaClass.config["left"]["blatant"], callback=toggleLeftBlatantMode)
                            add_info("Removes randomization for perfectly consistent clicks (Risky!)")
                    
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            dropdownBreakBlocks = dpg.add_combo(label="Break Blocks", items=["None", "Full", "Shift With Click", "Shift No Click"], width=150, default_value=sodaClass.config["left"]["breakBlocks"], callback=setLeftBreakBlocks)
                            add_info("Handle block breaking:\nNone: Ignored\nFull: Always break\nShift: Only when shifting")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            checkboxLeftAutoRod = dpg.add_checkbox(label="Auto Rod", default_value=sodaClass.config["left"]["AutoRod"], callback=toggleLeftAutoRod)
                            add_info("Automatically switches to rod and uses it.")

                        with dpg.group(horizontal=True):
                            sliderLeftAutoRodChance = dpg.add_slider_int(label="Auto Rod Chance", default_value=sodaClass.config["left"]["AutoRodChance"], min_value=1, max_value=100, width=200, callback=setLeftAutoRodChance)

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        creditsText = dpg.add_text(default_value="Credits: Antoine (Developer)")
                        githubText = dpg.add_text(default_value="Bombonne Clicker")
                    with dpg.tab(label="  Right Clicker  "):
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            checkboxToggleRightClicker = dpg.add_checkbox(label="Toggle", default_value=sodaClass.config["right"]["enabled"], callback=toggleRightClicker)
                            buttonBindRightClicker = dpg.add_button(label="Click to Bind", callback=statusBindRightClicker)
                            dropdownRightMode = dpg.add_combo(items=["Hold", "Always"], width=100, default_value=sodaClass.config["right"]["mode"], callback=setRightMode)
                            add_info("Hold: Click while holding right mouse button\nAlways: Click regardless of mouse state")

                            bind = sodaClass.config["right"]["bind"]
                            if bind != 0:
                                dpg.set_item_label(buttonBindRightClicker, f"Bind: {chr(bind)}")

                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                             sliderRightAverageCPS = dpg.add_slider_int(label="Average CPS", default_value=sodaClass.config["right"]["averageCPS"], min_value=1, width=200, callback=setRightAverageCPS)
                             add_info("Clicks Per Second (Average)")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            checkboxRightShakeEffect = dpg.add_checkbox(label="Shake Effect", default_value=sodaClass.config["right"]["shakeEffect"], callback=toggleRightShakeEffect)
                            add_info("Adds random movement to cursor to simulate human error/jitter.")

                        with dpg.group(horizontal=True):
                            sliderRightShakeEffectForce = dpg.add_slider_int(label="Shake Force", default_value=sodaClass.config["right"]["shakeEffectForce"], min_value=1, max_value=20, width=200, callback=setRightShakeEffectForce)

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            dropdownRightClickSound = dpg.add_combo(label="Click Sound", items=clicks, width=150, default_value=sodaClass.config["right"]["soundPath"], callback=setRightClickSoundPath)
                            add_info("Plays a sound when you click!")
    
                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            checkboxRightLMBLock = dpg.add_checkbox(label="LMB-Lock", default_value=sodaClass.config["right"]["LMBLock"], callback=toggleRightLMBLock)
                            add_info("Stop clicking when Left Mouse Button is held.")

                        with dpg.group(horizontal=True):
                            checkboxRightOnlyWhenFocused = dpg.add_checkbox(label="Only In Game", default_value=sodaClass.config["right"]["onlyWhenFocused"], callback=toggleRightOnlyWhenFocused)
                            add_info("Only click when Minecraft is the active window.")

                        with dpg.group(horizontal=True):
                            checkboxRightWorkInMenus = dpg.add_checkbox(label="Work in Menus", default_value=sodaClass.config["right"]["workInMenus"], callback=toggleRightWorkInMenus)
                            add_info("Allow clicking while in inventory/menus.")

                        with dpg.group(horizontal=True):
                            checkboxRightBlatantMode = dpg.add_checkbox(label="Blatant Mode", default_value=sodaClass.config["right"]["blatant"], callback=toggleRightBlatantMode)
                            add_info("Removes randomization for perfectly consistent clicks (Risky!)")

                        with dpg.group(horizontal=True):
                            checkboxRightItems = dpg.add_checkbox(label="Items", default_value=sodaClass.config["right"]["items"], callback=toggleRightItems)
                            add_info("Allow clicking while holding items.")
                        dpg.add_spacer(width=75)    
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        creditsText = dpg.add_text(default_value="Credits: Antoine (Developer)")
                        githubText = dpg.add_text(default_value="Bombonne Clicker")                
                    with dpg.tab(label="  Recorder  "):
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            dpg.add_text("Recorder Guide")
                            add_info("Records your legit way of clicking to produce undetectable clicks.\n1. Press Start\n2. Click naturally for a few seconds\n3. Press Stop\nOnly works for Left Click.")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        checkboxRecorderEnabled = dpg.add_checkbox(label="Enabled", default_value=sodaClass.config["recorder"]["enabled"], callback=toggleRecorder)

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            buttonStartRecording = dpg.add_button(label="Start Recording", callback=startRecording)
                            buttonStopRecording = dpg.add_button(label="Stop Recording", callback=stopRecording)

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        averageRecordCPSText = dpg.add_text(default_value="Average CPS of previous Record: ")
                        
                        totalTime = 0
                        for clickTime in sodaClass.config["recorder"]["record"]:
                            totalTime += float(clickTime)

                        dpg.set_value(averageRecordCPSText, f"Average CPS of previous Record: {round(len(sodaClass.config['recorder']['record']) / totalTime, 2)}")

                        recordingStatusText = dpg.add_text(default_value="Recording: ")
                        dpg.set_value(recordingStatusText, f"Recording: {recording}")
                        dpg.add_spacer(width=75)    
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        creditsText = dpg.add_text(default_value="Credits: Antoine (Developer)")
                        githubText = dpg.add_text(default_value="Bombonne Clicker")                    
                    with dpg.tab(label="  Misc  "):
                        dpg.add_spacer(width=75)
                        dpg.add_button(label="Antoine's Profile", callback=lambda: print("Bombonne by Antoine"))
                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        buttonSelfDestruct = dpg.add_button(label="Destruct", callback=selfDestruct)
                        add_info("Completely remove traces of the clicker.")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            buttonBindHideGUI = dpg.add_button(label="Click to Bind", callback=statusBindHideGUI)
                            add_info("Hide GUI Keybind")
                            bind = sodaClass.config["misc"]["bindHideGUI"]
                            if bind != 0:
                                dpg.set_item_label(buttonBindHideGUI, f"Bind: {chr(bind)}")

                        consoleFaker = dpg.add_combo(label="Console Faker", default_value=sodaClass.config["misc"]["consoleFaker"], items=["NullBind", "Optimiser", "CustomRGB"], callback=setConsoleFaker)
                        add_info("Disguise the console window title/text.")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                             saveSettings = dpg.add_checkbox(label="Save Settings", default_value=sodaClass.config["misc"]["saveSettings"], callback=toggleSaveSettings)
                             add_info("Attempts to save settings on close.")

                        with dpg.group(horizontal=True):
                            checkboxAlwaysOnTop = dpg.add_checkbox(label="Always On Top", callback=toggleAlwaysOnTop)
                            add_info("Makes the GUI always on top.")

                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            checkboxDiscordRPC = dpg.add_checkbox(label="Discord RPC", default_value=sodaClass.config["misc"]["discordRichPresence"], callback=toggleDiscordRPC)
                            add_info("Shows your activity status as using Bombonne Clicker")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            buttonBindRodKey = dpg.add_button(label="Rod Bind", callback=statusBindRod)
                            bind = sodaClass.config["misc"]["rodBind"]
                            if bind != 0:
                                dpg.set_item_label(buttonBindRodKey, f"Bind: {chr(bind)}")
                            add_info("Press to throw a rod.")

                        with dpg.group(horizontal=True):
                            dpg.add_checkbox(label="Long Rod", default_value=sodaClass.config["misc"]["longRod"], callback=setLongRod)
                            add_info("Doubles the rod delay for longer throws.")

                        with dpg.group(horizontal=True):
                            rodSlot = dpg.add_combo(label="Rod Slot", items=["1", "2", "3", "4", "5", "6", "7", "8", "9"], width=50, default_value=sodaClass.config["misc"]["rodSlot"], callback=setRodSlot)
                            add_info("Slot to switch to when throwing rod.")

                        with dpg.group(horizontal=True):
                            rodDelay = dpg.add_input_float(label="Rod Delay", default_value=sodaClass.config["misc"]["rodDelay"], min_value=0, max_value=2, step=0.1, width=100, callback=setRodDelay)
                            add_info("Duration to hold rod (Range)")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            buttonBindPearlKey = dpg.add_button(label="Pearl Bind", callback=statusBindPearl)
                            bind = sodaClass.config["misc"]["pearlBind"]
                            if bind != 0:
                                dpg.set_item_label(buttonBindPearlKey, f"Bind: {chr(bind)}")
                            add_info("Press to throw a pearl.")

                        with dpg.group(horizontal=True):
                            dpg.add_combo(label="Pearl Slot", items=["1", "2", "3", "4", "5", "6", "7", "8", "9"], width=50, default_value=sodaClass.config["misc"]["pearlSlot"], callback=setPearlSlot)
                            add_info("Slot to switch to when throwing pearl.")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            dpg.add_combo(label="Sword Slot", items=["1", "2", "3", "4", "5", "6", "7", "8", "9"], width=50, default_value=sodaClass.config["misc"]["swordSlot"], callback=setSwordSlot)
                            add_info("Slot to switch back to after auto-throwing.")
                        
                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            dpg.add_checkbox(label="Toggle Sounds", default_value=sodaClass.config["misc"]["toggleSounds"], callback=setToggleSounds)
                            add_info("Sound when toggling clicker on/off.")
                        
                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                           pingSlider = dpg.add_slider_int(label="Ping", default_value=sodaClass.config["misc"]["ping"], min_value=1, max_value=1000, width=150, callback=setPing)
                           dpg.add_button(label="Auto", callback=autoPing)
                           add_info("Ping for autoblocking timing.")
                        
                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        creditsText = dpg.add_text(default_value="Credits: Antoine (Developer)")
                        githubText = dpg.add_text(default_value="Bombonne Clicker")

                    with dpg.tab(label="  Potions  "):
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            dpg.add_checkbox(label="Enable Potions", default_value=sodaClass.config["potions"]["enabled"], callback=togglePotions)
                            add_info("Tools for potions, includes throwbind.")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            buttonBindPotKey = dpg.add_button(label="Throw Bind", callback=statusBindPot)
                            bind = sodaClass.config["potions"]["potBind"]
                            if bind != 0:
                                dpg.set_item_label(buttonBindPotKey, f"Bind: {chr(bind)}")
                            add_info("Keybind to throw potion.")

                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            buttonBindPotResetKey = dpg.add_button(label="Reset Bind", callback=statusBindPotReset)
                            bind = sodaClass.config["potions"]["potResetBind"]
                            if bind != 0:
                                dpg.set_item_label(buttonBindPotResetKey, f"Bind: {chr(bind)}")
                            add_info("Keybind to reset potion data (Set next slot to start).")

                        dpg.add_spacer(width=75)    
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            dpg.add_slider_int(label="Low Slot", default_value=sodaClass.config["potions"]["lowestSlot"], min_value=1, max_value=9, width=150, callback=setLowestSlot)
                            add_info("First slot to throw from.")

                        dpg.add_spacer(width=75)
                        with dpg.group(horizontal=True):
                            dpg.add_slider_int(label="High Slot", default_value=sodaClass.config["potions"]["highestSlot"], min_value=1, max_value=9, width=150, callback=setHighestSlot)
                            add_info("Max slot to switch to.")

                        dpg.add_spacer(width=75)
                        with dpg.group(horizontal=True):
                             potDelay = dpg.add_input_float(label="Pot Delay", default_value=sodaClass.config["potions"]["throwDelay"], min_value=0, max_value=2, width=100, callback=setPotDelay)
                             add_info("Wait time after switching to throw.")
                        
                        dpg.add_spacer(width=75)    
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        creditsText = dpg.add_text(default_value="Credits: Antoine (Developer)")
                        githubText = dpg.add_text(default_value="Bombonne Clicker")
                    
                    with dpg.tab(label="  Movement  "):
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            dpg.add_checkbox(label="Auto W Tap", default_value=sodaClass.config["movement"]["autoWTap"], callback=toggleWTap)
                            add_info("Automatically W-Taps when clicking (Combo helper).")
                        
                        with dpg.group(horizontal=True):
                            dpg.add_slider_int(label="W Tap Value", default_value=sodaClass.config["movement"]["wTapValue"], min_value=1, max_value=100, width=150, callback=setWTapValue)

                        with dpg.group(horizontal=True):
                            dpg.add_combo(label="W Tap Mode", items=["chance", "delay"], width=100, default_value=sodaClass.config["movement"]["wTapMode"], callback=setWTapMode)

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            dpg.add_checkbox(label="Auto Sprint", default_value=sodaClass.config["movement"]["autoSprint"], callback=toggleAutoSprint)
                            add_info("Automatically sprints when moving.")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            dpg.add_checkbox(label="Better Input", default_value=sodaClass.config["movement"]["betterInput"], callback=toggleBetterInput)
                            add_info("NullBind script (like SnapTap) for perfect strafing.")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)

                        with dpg.group(horizontal=True):
                            dpg.add_checkbox(label="Fast Stop", default_value=sodaClass.config["movement"]["fastStop"], callback=toggleFastStop)
                            add_info("Stops you faster when on ground.")

                        dpg.add_spacer(width=75)
                        dpg.add_separator()
                        dpg.add_spacer(width=75)
                    with dpg.tab(label="  Config  "):
                        # Load all configs from the config folder

                        dpg.add_spacer(width=75)
                        dpg.add_text(default_value="Config Manager")
                        dpg.add_separator()
                        dpg.add_spacer(width=100)

                        dpg.add_text(default_value="Current Config: " + sodaClass.config["displayName"])
                        
                        configs = sodaClass.getConfigs()

                        if len(configs) == 0:
                            dpg.add_text(default_value="No configs found!")
                        else:
                            dpg.add_text(default_value="Configs found:")
                            dpg.add_spacer(width=75)
                            dpg.add_separator()
                            dpg.add_spacer(width=75)
                            for idx, config in enumerate(configs):
                                with dpg.group():
                                    # Display name
                                    dpg.add_text(default_value=config["displayName"])
                                    dpg.add_text(default_value=f"Author: {config['Author']}")
                                    dpg.add_text(default_value=f"Description: {config['description']}")
                                    dpg.add_button(label="Load", callback=sodaClass.loadConfig, user_data=idx)
                                    dpg.add_spacer(width=75)
                                    dpg.add_separator()
                                    dpg.add_spacer(width=75)

                        dpg.add_spacer(width=75)

                        dpg.add_text(default_value="Requires restart to apply changes!")

                        dpg.add_spacer(width=75)

                        dpg.add_button(label="Open Config Folder", callback=sodaClass.openConfigFolder)
                        dpg.add_button(label="Save Config", callback=configEditor)
                    if sodaClass.newver:
                        with dpg.tab(label="Update"):
                            dpg.add_spacer(width=75)
                            dpg.add_text(default_value="A new version of Bombonne is available!")
                            dpg.add_text(default_value=f"Current version: {version}")
                            dpg.add_text(default_value=f"Latest version: {sodaClass.newverid}")

                            dpg.add_text(default_value="You can download it from the GitHub repository.")
                            dpg.add_button(label="Download", callback=lambda: webbrowser.open("https://github.com/Dream23322/Soda-Autoclicker/releases"))

            with dpg.theme() as global_theme:
                with dpg.theme_component(dpg.mvAll):
                    # Spacing & Rounding - Vape V4 style
                    dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)
                    dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1)
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                    dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 4)
                    dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 14)
                    dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 2)
                    dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 6)
                    dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 4)
                    dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 6)
                    dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 6, 4)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 12)
                    dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 10)
                    dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 6)
                    dpg.add_theme_style(dpg.mvStyleVar_TabBarBorderSize, 1)
                    
                    # Dark Background Palette
                    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (10, 10, 14))
                    dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (16, 16, 22))
                    dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (18, 18, 24))
                    dpg.add_theme_color(dpg.mvThemeCol_Border, (40, 40, 55))
                    dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))
                    
                    # Frame (inputs, sliders, combos)
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (28, 28, 38))
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (38, 38, 52))
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (50, 40, 70))
                    
                    # Title Bar
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (8, 8, 12))
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (8, 8, 12))
                    
                    # Tabs - Vape accent
                    dpg.add_theme_color(dpg.mvThemeCol_Tab, (18, 18, 26))
                    dpg.add_theme_color(dpg.mvThemeCol_TabActive, (88, 0, 230))
                    dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (110, 20, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, (14, 14, 20))
                    dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, (60, 0, 160))
                    
                    # Buttons
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (30, 30, 42))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (88, 0, 230))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (70, 0, 190))
                    
                    # Interactive elements
                    dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (120, 40, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (88, 0, 230))
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (130, 50, 255))
                    
                    # Headers & Collapsibles
                    dpg.add_theme_color(dpg.mvThemeCol_Header, (30, 30, 42))
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (44, 44, 60))
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (55, 40, 80))
                    
                    # Scrollbar
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (12, 12, 18))
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (50, 50, 70))
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (88, 0, 230))
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (120, 40, 255))
                    
                    # Separator
                    dpg.add_theme_color(dpg.mvThemeCol_Separator, (35, 35, 50))
                    dpg.add_theme_color(dpg.mvThemeCol_SeparatorHovered, (88, 0, 230))
                    dpg.add_theme_color(dpg.mvThemeCol_SeparatorActive, (120, 40, 255))
                    
                    # Text
                    dpg.add_theme_color(dpg.mvThemeCol_Text, (210, 210, 220))
                    dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (90, 90, 110))

            dpg.bind_theme(global_theme)


            dpg.setup_dearpygui()
            dpg.show_viewport()
            
            guiWindows = win32gui.GetForegroundWindow()

            dpg.set_primary_window("Primary Window", True)
            dpg.start_dearpygui()
        
        except AttributeError as e:
            print(f"Error with current config: {e}")
            print(f"{os.path.join(sodaClass.folder_path, 'config.json')} is not a valid config file.")
            # delete config.json from resource folder
            if os.path.exists(os.path.join(sodaClass.folder_path, "config.json")):
                print("Deleting config.json...")
                os.remove(os.path.join(sodaClass.folder_path, "config.json"))
            print("Removed current config, please restart the program to generate a new one.")

        selfDestruct()
    except KeyboardInterrupt:
        os._exit(0)