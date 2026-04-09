import os
import shutil
import subprocess
import sys
import time

import gi

gi.require_version('Gtk', '3.0')
try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3
except (ImportError, ValueError):
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
from gi.repository import GLib, Gtk

import config
import utils

logger = utils.get_logger(__name__)

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
RAM_DIR = "/dev/shm/voicemint_assets"

ICON_ON = "icon-on-128.png"
ICON_OFF = "icon-off-128.png"
SOUND_START = "start.wav"
SOUND_STOP = "stop.wav"

class TrayManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TrayManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
            
        self.indicator = None
        self.ram_assets = {}
        self.is_active = False
        self.restore_callback = None
        
        # Load assets can stay here as it's just filesystem I/O
        self.load_assets_to_ram()
        self.initialized = True

    def set_restore_callback(self, callback):
        """Allows the UI to register a function to restore the window."""
        self.restore_callback = callback

    def load_assets_to_ram(self):
        """Copies assets to /dev/shm for zero-latency access, keeping fallback paths."""
        os.makedirs(RAM_DIR, exist_ok=True)
        
        for filename in [ICON_ON, ICON_OFF, SOUND_START, SOUND_STOP]:
            ssd_path = os.path.join(ASSETS_DIR, filename)
            ram_path = os.path.join(RAM_DIR, filename)
            
            try:
                shutil.copy2(ssd_path, ram_path)
                self.ram_assets[filename] = ram_path
                logger.info(f"Loaded {filename} to RAM.")
            except Exception as e:
                logger.error(f"Failed to copy {filename} to RAM: {e}. Falling back to SSD.")
                self.ram_assets[filename] = ssd_path

    def cleanup_ram_assets(self):
        """Deletes the assets from RAM."""
        try:
            if os.path.exists(RAM_DIR):
                shutil.rmtree(RAM_DIR)
                logger.info("Cleaned up RAM assets.")
        except Exception as e:
            logger.error(f"Failed to clean up RAM assets: {e}")

    def setup_indicator(self):
        """Initializes the GTK AppIndicator3 (Ayatana preferred)."""
        try:
            self.indicator = AppIndicator3.Indicator.new(
                "voicemint_indicator",
                self.ram_assets[ICON_OFF],
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            
            menu = Gtk.Menu()
            
            # Open VoiceMint item
            item_show = Gtk.MenuItem(label="Open VoiceMint")
            item_show.connect('activate', self.on_show_window)
            menu.append(item_show)
            
            # Separator
            separator = Gtk.SeparatorMenuItem()
            menu.append(separator)
            
            # Quit item
            item_quit = Gtk.MenuItem(label="Quit VoiceMint")
            item_quit.connect('activate', self.on_quit)
            menu.append(item_quit)
            
            menu.show_all()
            self.indicator.set_menu(menu)
            logger.info("GTK AppIndicator setup complete on thread.")
        except Exception as e:
            logger.error(f"Failed to setup GTK AppIndicator: {e}")

    def on_show_window(self, source):
        """Callback for the Open VoiceMint menu item."""
        if self.restore_callback:
            # Trigger the UI restoration callback
            self.restore_callback()
        else:
            logger.warning("Tray: Open VoiceMint clicked but no restore callback registered.")

    def on_quit(self, source):
        """Soft shutdown: Clear the running flag and stop the GTK loop."""
        logger.info("Tray: Quit requested. Signaling soft shutdown.")
        
        # If we are currently listening, trigger the deactivation feedback
        if self.is_active:
            self.handle_activation_request(activate=False)
            # Give a split second for the subprocesses to launch (aplay/notify-send)
            time.sleep(0.4)
            
        utils.app_running.clear()
        # Signal GTK to stop its own loop
        GLib.idle_add(Gtk.main_quit)

    def play_sound(self, sound_filename: str):
        """Plays a sound asynchronously using aplay."""
        sound_path = self.ram_assets.get(sound_filename)
        if sound_path and os.path.exists(sound_path):
            try:
                subprocess.Popen(
                    ["aplay", "-q", sound_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                logger.error(f"Failed to play sound {sound_filename}: {e}")

    def show_notification(self, summary: str, body: str, icon_filename: str = None):
        """Shows a system notification asynchronously using notify-send. Raw text only."""
        cmd = ["notify-send", summary, body]
        if icon_filename:
            icon_path = self.ram_assets.get(icon_filename)
            if icon_path and os.path.exists(icon_path):
                cmd.extend(["-i", icon_path])
                
        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def handle_activation_request(self, activate: bool, is_timeout: bool = False) -> bool:
        """
        Handles requests to turn voice typing on or off.
        Checks for redundant state and shows appropriate notifications.
        Returns True if the state actually changes, False if redundant.
        """
        if activate:
            if self.is_active:
                self.show_notification("VoiceMint", "Voice typing is already active.", ICON_ON)
                return False
            else:
                self.is_active = True
                provider_name = config.ACTIVE_STT_PROVIDER.value.capitalize()
                self.show_notification("VoiceMint Activated", f"Listening via {provider_name}...", ICON_ON)
                self.play_sound(SOUND_START)
                if self.indicator:
                    GLib.idle_add(self.indicator.set_icon_full, self.ram_assets[ICON_ON], "Active")
                return True
        else:
            if not self.is_active:
                self.show_notification("VoiceMint", "Voice typing is already stopped.", ICON_OFF)
                return False
            else:
                self.is_active = False
                if is_timeout:
                    self.show_notification("VoiceMint Deactivated", "Silence timeout reached. Stopped listening.", ICON_OFF)
                else:
                    self.show_notification("VoiceMint Deactivated", "Stopped Listening...", ICON_OFF)
                self.play_sound(SOUND_STOP)
                if self.indicator:
                    GLib.idle_add(self.indicator.set_icon_full, self.ram_assets[ICON_OFF], "Inactive")
                return True

    def run(self):
        """Starts the GTK main loop after ensuring initialization on the same thread."""
        self.setup_indicator()
        Gtk.main()

_tray_manager = None

def get_tray_manager() -> TrayManager:
    global _tray_manager
    if _tray_manager is None:
        _tray_manager = TrayManager()
    return _tray_manager
