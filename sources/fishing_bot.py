import pyautogui
import pyaudio
import audioop
import threading
import time
import win32api
import configparser
import random
import numpy as np
import cv2
import dearpygui.dearpygui as dpg
from windowcapture import WindowCapture
import random

class FishermanBot:
    def __init__(self, bobber, bar, region=None, settings_file='settings.ini'):
        # Initialization of the bot with basic settings
        # bobber: image of the fishing bobber
        # bar: image of the minigame bar
        # region: screen area for capture
        # settings_file: settings file
        
        self.bobber = bobber
        self.bar = bar
        self.region = region
        self.settings_file = settings_file
        self.parser = configparser.ConfigParser()
        self.parser.read(self.settings_file)

        # Load settings from the .ini file
        self.debug_mode = self.parser.getboolean('Settings', 'debug')
        self.max_volume = self.parser.getint('Settings', 'Volume_Threshold')
        self.detection_threshold = self.parser.getfloat('Settings', 'detection_threshold')

        # Define tracking area on the screen
        screen_area = self.parser.get('Settings', 'tracking_zone').strip('()')
        cordies = screen_area.split(',')
        self.screen_area = tuple(map(int, cordies))

        # Bot state variables
        self.coords = []  # Coordinates of fishing spots
        self.total = 0    # Total audio volume
        self.STATE = "IDLE"  # Current state of the bot
        self.stop_button = False  # Stop control
        self.state_left = win32api.GetKeyState(0x01)  # State of the left mouse button
        self.state_right = win32api.GetKeyState(0x02) # State of the right mouse button
        self.fish_count = 0      # Count of caught fish
        self.bait_counter = 0    # Count of baits used
        self.food_timer = 0      # Timer for eating
        self.minigame_counter = 0  # Minigame counter
        self.bait_item_coords = None  # Coordinates of the bait item
        self.use_button_coords = None  # Coordinates of the use button
        self.bait_amount = self.parser.getint('Settings', 'bait_amount')  # Amount of baits
        self.bait_counter = 0  # Count of baits used
        self.last_minigame_time = time.time()  # Stores the time of the last minigame entry
        self.check_interval = 600  # 10 minutes in seconds
        self.use_bait_boolean = True # Checks whether to use baits or not
        # Initializes window capture for Albion
        self.wincap = WindowCapture('Albion Online Client')

    def check_volume(self):
        # Monitors audio volume to detect when a fish bites the bait
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=2, rate=44100, input=True, frames_per_buffer=1024)
        while not self.stop_button:
            self.total = 0
            for _ in range(2):
                data = stream.read(1024)
                reading = audioop.max(data, 2)
                self.total += reading
                if self.total > self.max_volume and self.STATE not in ["MINIGAME", "DELAY", "CASTING", "EATING", "BAIT"]:
                    self.do_minigame()

    def get_new_spot(self):
        # Randomly selects a new fishing spot
        return random.choice(self.coords)

    def cast_hook(self):
        # Function to cast the fishing line
        # Manages the casting and waiting cycle
        while not self.stop_button:
            if self.STATE in ["CASTING", "STARTED"]:
                time.sleep(random.uniform(1.2, 3.0))
                if self.fish_count % 10 == 0 and self.use_bait_boolean == True:  # Every 10 fish, use bait
                    # Checks if there are enough baits before using
                    if self.bait_counter < self.bait_amount:
                        self.log_info("Not enough baits to use.")
                    else:
                        self.use_bait()  # Calls the function to use baits
                        time.sleep(0.2)
                # Process of casting the line
                pyautogui.mouseUp()
                x, y = self.get_new_spot()
                pyautogui.moveTo(x, y, tween=pyautogui.linear, duration=0.2)
                time.sleep(0.2)
                pyautogui.mouseDown()
                time.sleep(random.uniform(0.3, 0.9))
                pyautogui.mouseUp()
                self.log_info(f"STATE {self.STATE}")
                time.sleep(2.5)
                self.STATE = "CAST"
            elif self.STATE == "CAST":
                time.sleep(20)
                if self.STATE == "CAST":
                    self.log_info("Seems to be stuck on cast. Recasting.")
                    pyautogui.press('s')
                    self.STATE = "CASTING"

    def eat_food(self):
        # Function to manage food consumption
        # Executes every 30 minutes (1800 seconds)
        while not self.stop_button:
            time.sleep(1800)
            self.STATE = "EATING"
            if self.STATE == "EATING":
                self.log_info("EATING FOOD")
                pyautogui.press('2')
                self.STATE = "CASTING"

    def use_bait(self):
        """
        Function to use baits in the game.
        Opens the menu, selects the first item, and clicks the use button.
        """
        self.STATE = "BAIT"  # Changes state to "BAIT" (using bait)
        self.log_info(f"STATE {self.STATE}")  # Logs the current state

        if self.bait_counter >= self.bait_amount:
            self.log_info("Not enough baits to use.")
            self.STATE = "CASTING"  # Changes state to "CASTING" (casting)
            return

        # Selects the bait item
        if self.bait_item_coords:
            pyautogui.press('i')  # Example: 'i' for inventory
            time.sleep(0.5)  # Waits for the menu to open
            pyautogui.moveTo(self.bait_item_coords[0], self.bait_item_coords[1], duration=0.2)
            pyautogui.click()
            time.sleep(0.5)  # Waits for selection
            
        # Clicks the use button
        if self.use_button_coords:
            pyautogui.moveTo(self.use_button_coords[0], self.use_button_coords[1])
            pyautogui.click()
            time.sleep(0.2)  # Waits for the action to complete
            self.bait_counter += 1  # Increments the count of used baits
            self.log_info(f"Bait used, {self.bait_amount - self.bait_counter} remaining")

        # Closes the menu
        pyautogui.press('i')  # Example: 'i' for inventory
        time.sleep(0.2)  # Waits for the menu to close
        pyautogui.press('s')  # Stops all actions
        self.STATE = "CASTING"  # Changes state to "CASTING" (casting)

    def do_minigame(self):
        # Executes the fishing minigame when a fish is hooked
        # Controls the mouse based on the position of the bobber

        # Checks if the bot is not in casting, started, eating, or bait states
        if self.STATE not in ["CASTING", "STARTED", "EATING", "BAIT"]:
            self.STATE = "MINIGAME"  # Changes state to "MINIGAME" (solving)
            self.log_info(f"STATE {self.STATE}")  # Logs the current state
            pyautogui.mouseDown()  # Simulates pressing the mouse button
            pyautogui.mouseUp()    # Simulates releasing the mouse button
            time.sleep(0.2)        # Waits 200 milliseconds to stabilize

            # Calls the detect_bobber function to check the position of the bobber
            valid, location, size = self.detect_bobber()
            
            # If the bobber is successfully detected
            if valid == True:
                self.last_minigame_time = time.time()  # Updates the timestamp
                self.fish_count += 1  # Increments the count of caught fish
                
                while True:  # Continuous loop to monitor the bobber
                    valid, location, size = self.detect_bobber()  # Checks the bobber again
                    
                    # min_limit = int(size[1] * 0.3)
                    # max_limit = int(size[1] * 0.7)

                    # If the bobber is still valid
                    if valid == True:
                        # If the position of the bobber is in the left half of the bar
                        if location <= int(size[1] / 2):
                            pyautogui.mouseDown()  # Presses the mouse button (captures)
                        # If the position of the bobber is in the right half of the bar
                        elif location >= int(size[1] / 2):
                            pyautogui.mouseUp()  # Releases the mouse button (releases)
                    else:
                        # If the bobber is no longer detected and is not in casting state
                        if self.STATE != "CASTING":
                            self.STATE = "CASTING"  # Changes state to "CASTING"
                            time.sleep(0.3) # Waits 300 milliseconds
                            pyautogui.mouseUp()  # Releases the mouse button
                            break  # Exits the loop
            else:
                self.STATE = "CASTING"  # If the bobber is not detected, changes state to "CASTING"
    
    def monitor_bot(self):
        """
        Monitors the bot's behavior and stops if necessary.
        """
        while not self.stop_button:
            current_time = time.time()
            if current_time - self.last_minigame_time > self.check_interval:
                self.log_info("The bot has not entered the minigame in 10 minutes. Stopping the bot.")
                self.stop_bot()  # Calls the function to stop the bot
            time.sleep(60)  # Checks every 60 seconds

    def generate_coords(self):
        # Generates coordinates for fishing spots
        # User defines the spots by pressing space
        amount_of_coords = dpg.get_value("Amount Of Spots")
        if amount_of_coords == 0:
            amount_of_coords = 1
        for n in range(amount_of_coords):
            self.log_info(f"[spot: {n + 1}] | Press Spacebar over the spot you want")
            time.sleep(1)
            while True:
                if win32api.GetKeyState(0x20) < 0:
                    x, y = pyautogui.position()
                    self.coords.append([x, y])
                    self.log_info(f"Position: {n + 1} Saved. | {x, y}")
                    break
                time.sleep(0.001)

    def grab_screen(self):
        # Defines the tracking area on the screen
        # User selects two points to define the region
        image_coords = []
        while True:
            if win32api.GetKeyState(0x20) < 0:
                x, y = pyautogui.position()
                image_coords.append([x, y])
                if len(image_coords) == 2:
                    break
            time.sleep(0.001)
        start_point, end_point = image_coords
        self.screen_area = start_point[0], start_point[1], end_point[0], end_point[1]
        self.log_info(f"Updated area {self.screen_area}")

    def detect_minigame(self, screenshot, bar):
        # Detects if the minigame is active
        # Uses template matching to find the minigame bar
        result = cv2.matchTemplate(screenshot, bar, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        if max_val >= self.detection_threshold:
            return True
        return False

    def set_bait_item_coords(self):
        """
        Allows the user to set the coordinates of the bait item.
        """
        self.log_info("Press Space over the bait item.")
        while True:
            if win32api.GetKeyState(0x20) < 0:  # 0x20 is the space key
                self.bait_item_coords = pyautogui.position()
                self.log_info(f"Bait item coordinates saved: {self.bait_item_coords}")
                break
            time.sleep(0.001)

    def set_use_button_coords(self):
        """
        Allows the user to set the coordinates of the use button.
        """
        self.log_info("Press Space over the use button.")
        while True:
            if win32api.GetKeyState(0x20) < 0:  # 0x20 is the space key
                self.use_button_coords = pyautogui.position()
                self.log_info(f"Use button coordinates saved: {self.use_button_coords}")
                break
            time.sleep(0.001)

    def detect_bobber(self):
        # Detects the position of the bobber on the screen
        # Returns if valid, location, and size
        screenshot = self.wincap.get_screenshot(region=self.region)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        bobber = cv2.imread(self.bobber)
        bar = cv2.imread(self.bar)
        result = cv2.matchTemplate(screenshot, bobber, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        return [self.detect_minigame(screenshot, bar), max_loc[0] + bobber.shape[1] // 2, screenshot.shape]
    
    def log_info(self, message):
        # Function for logging messages in the interface
        current_logs = dpg.get_value("LogWindow")
        updated_logs = f"{current_logs}\n{message}" if current_logs else message
        dpg.set_value("LogWindow", updated_logs)

    def save_settings(self):
        # Saves the settings in the .ini file
        with open(self.settings_file, 'w') as configfile:
            self.parser.set('Settings', 'Volume_Threshold', str(self.max_volume))
            self.parser.set('Settings', 'tracking_zone', str(self.screen_area))
            self.parser.set('Settings', 'detection_threshold', str(self.detection_threshold))
            self.parser.set('Settings', 'bait_amount', str(self.bait_amount))
            self.parser.set('Settings', 'use_bait_boolean', str(self.use_bait_boolean))
            self.parser.write(configfile)
        self.log_info("Saved New Settings to settings.ini")

    def start_bot(self):
        # Starts the bot and its threads
        self.log_info("Bot started successfully.")
        self.stop_button = False
        time.sleep(3)
        threading.Thread(target=self.eat_food).start()
        threading.Thread(target=self.check_volume).start()
        threading.Thread(target=self.cast_hook).start()
        time.sleep(2)
        pyautogui.press('s')
        time.sleep(2)
        self.STATE = "STARTED"

    def stop_bot(self):
        # Stops the execution of the bot
        self.log_info("Bot stopped.")
        self.stop_button = True
        self.STATE = "STOPPED"

    def update_use_bait_boolean(self, sender, app_data):
        """
        Updates the use_bait_boolean variable with the value from the checkbox.
        """
        self.use_bait_boolean = app_data  # app_data will be True or False
        self.log_info(f"Bait boolean set to: {self.use_bait_boolean}")

        # Shows or hides the buttons for bait item and use coordinates
        if self.use_bait_boolean:
            dpg.show_item("bait_use")
            # dpg.show_item(self.set_bait_amount)
            # dpg.show_item(self.bait_item_button)
            # dpg.show_item(self.use_button_button)
            dpg.configure_item("bait", height=150)
        else:
            dpg.hide_item("bait_use")
            dpg.configure_item("bait", height=50)
            # dpg.hide_item(self.set_bait_amount)
            # dpg.hide_item(self.bait_item_button)
            # dpg.hide_item(self.use_button_button)

    def init_gui(self):
        """
        Initializes the graphical interface with all controls.
        """
        dpg.create_context()
        dpg.create_viewport(title="Fisherman", width=700, height=500)

        with dpg.window(label="Fisherman Window", width=684, height=460):
            with dpg.group():
                # Interface controls
                dpg.add_input_int(label="Amount Of Spots", tag="Amount Of Spots", 
                                  max_value=10, min_value=1, default_value=1, width=120)
                dpg.add_input_int(label="Set Volume Threshold", tag="Set Volume Threshold", 
                                  max_value=100000, min_value=0, default_value=self.max_volume, width=120)
                dpg.add_input_float(label="Set Detection Threshold", tag="Set Detection Threshold", 
                                    min_value=0.1, max_value=1.0, default_value=self.detection_threshold, width=120)
                
            with dpg.group(tag="baits", horizontal=True):
                with dpg.child_window(tag="bait", width=520, height=150):
                    dpg.add_checkbox(label="Use Bait", default_value=self.use_bait_boolean, callback=self.update_use_bait_boolean)
                    with dpg.child_window(tag="bait_use", width=400, height=100):
                        self.set_bait_amount = dpg.add_input_int(label="Set Bait Amount", width=80, max_value=100, min_value=0, default_value=self.bait_amount)
                        self.bait_item_button = dpg.add_button(label="Set Bait Item Location", callback=self.set_bait_item_coords)
                        self.use_button_button = dpg.add_button(label="Set Use Button Location", callback=self.set_use_button_coords)

            # Control buttons
            dpg.add_button(label="Set Fishing Spots", callback=self.generate_coords)
            dpg.add_button(label="Set Tracking Zone", callback=self.grab_screen)
            dpg.add_button(label="Start Bot", callback=self.start_bot)
            dpg.add_button(label="Stop Bot", callback=self.stop_bot)
            dpg.add_button(label="Save Settings", callback=self.save_settings)

            # Log area
            dpg.add_text("Log Messages:")
            dpg.add_input_text(multiline=True, readonly=True, 
                               width=650, height=150, tag="LogWindow", 
                               default_value="")

        # Initializes the interface
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()
