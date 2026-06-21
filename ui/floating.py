import threading
import signal
import tkinter as tk
from tkinter import ttk, messagebox

import utils
from stt import start_listening, stop_listening
from ui.constants import (
    BUTTON_FONT,
    GLOBAL_FONT,
    MAIN_WINDOW_GEOMETRY,
    MIN_MAIN_WINDOW_SIZE,
    PAD_X,
    PAD_Y,
    SMALL_FONT,
    TITLE_FONT,
)
from ui.settings_ui import SettingsPanel

logger = utils.get_logger(__name__)

class VoiceMintUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("VoiceMint")
        self.geometry(MAIN_WINDOW_GEOMETRY)
        self.minsize(*MIN_MAIN_WINDOW_SIZE)
        self.resizable(False, False)
        
        # Register signal handler for single-instance "wake up"
        signal.signal(signal.SIGUSR1, self._handle_sigusr1)
        
        # Apply standard padding to the main window
        self.container = ttk.Frame(self, padding=(PAD_X, PAD_Y))
        self.container.pack(fill=tk.BOTH, expand=True)

        # UI state
        self.always_on_top = tk.BooleanVar(value=False)
        self.current_state = "stopped"

        # Set default font for ttk
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(".", font=GLOBAL_FONT)
        style.configure("TButton", font=BUTTON_FONT)
        style.configure("Small.TCheckbutton", font=SMALL_FONT)

        self._setup_ui()
        
        self.protocol("WM_DELETE_WINDOW", self._on_minimize_to_tray)
        
        from ui.tray import get_tray_manager
        get_tray_manager().set_restore_callback(self._restore_from_tray)

        self._poll_state()
        
    def _setup_ui(self):
        # 1. Status Label
        self.status_label = ttk.Label(self.container, text="Status: Stopped", font=TITLE_FONT)
        self.status_label.pack(pady=(0, 5))

        # 2. Status Indicator (Color Square since ttk doesn't have easy rounded frames)
        self.indicator = tk.Label(self.container, bg="#D9534F", width=4, height=2)
        self.indicator.pack(pady=(0, PAD_Y))

        # 3. Start and Stop Buttons
        self.button_frame = ttk.Frame(self.container)
        self.button_frame.pack(pady=(0, PAD_Y), fill=tk.X)
        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)

        self.start_btn = ttk.Button(self.button_frame, text="Start", width=10, command=self._on_start_clicked)
        self.start_btn.grid(row=0, column=0, padx=(0, 5), sticky=tk.EW)

        self.stop_btn = ttk.Button(self.button_frame, text="Stop", width=10, command=self._on_stop_clicked)
        self.stop_btn.grid(row=0, column=1, padx=(5, 0), sticky=tk.EW)

        # 4. Settings Button
        self.settings_btn = ttk.Button(
            self.container, text="⚙ Settings",
            command=self._open_settings
        )
        self.settings_btn.pack(fill=tk.X, pady=(0, PAD_Y))

        # 5. Always on Top Checkbox
        self.ontop_cb = ttk.Checkbutton(self.container, text="Always on Top", variable=self.always_on_top, style="Small.TCheckbutton", command=self._toggle_always_on_top)
        self.ontop_cb.pack(pady=(0, 0))


    def _open_settings(self):
        SettingsPanel(self)

    def _toggle_always_on_top(self):
        self.attributes("-topmost", self.always_on_top.get())

    def _on_minimize_to_tray(self):
        logger.info("UI: Minimizing to tray.")
        self.withdraw()

    def _restore_from_tray(self):
        logger.info("UI: Restoring from tray.")
        self.after(0, self.deiconify)
        self.after(0, self.focus_force)

    def _handle_sigusr1(self, signum, frame):
        """Called when a second instance tries to launch."""
        logger.info("UI: SIGUSR1 received. Restoring window.")
        self._restore_from_tray()
        messagebox.showinfo("VoiceMint", "VoiceMint is already running.")

    def _on_start_clicked(self):
        from ui.tray import get_tray_manager
        tray = get_tray_manager()
        if tray.handle_activation_request(activate=True):
            logger.info("UI: Start clicked")
            utils.is_listening.set()
            threading.Thread(target=start_listening, daemon=True).start()

    def _on_stop_clicked(self):
        from ui.tray import get_tray_manager
        tray = get_tray_manager()
        if tray.handle_activation_request(activate=False):
            logger.info("UI: Stop clicked")
            utils.is_listening.clear()
            stop_listening()

    def _poll_state(self):
        if not utils.app_running.is_set():
            logger.info("UI: Shutdown signaled. Closing window.")
            self.destroy()
            return

        listening = utils.is_listening.is_set()
        connected = utils.is_connected.is_set()

        if listening and not connected:
            state = "connecting"
        elif listening and connected:
            state = "listening"
        else:
            state = "stopped"
        
        if self.current_state != state:
            self.current_state = state
            self._update_status_display()
            
        self.after(100, self._poll_state)
        
    def _update_status_display(self):
        if self.current_state == "listening":
            self.status_label.config(text="Status: Listening")
            self.indicator.config(bg="#2FA572")
        elif self.current_state == "connecting":
            self.status_label.config(text="Status: Connecting...")
            self.indicator.config(bg="#F0AD4E")
        else:
            self.status_label.config(text="Status: Stopped")
            self.indicator.config(bg="#D9534F")

def launch_ui():
    app = VoiceMintUI()
    app.mainloop()
