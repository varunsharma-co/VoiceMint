import threading
import tkinter as tk
import customtkinter as ctk

import config
import utils
from stt import start_listening, stop_listening

logger = utils.get_logger(__name__)

class VoiceMintUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Voice Typing by Varun")
        self.geometry("280x200")
        self.resizable(False, False)

        # UI state
        self.always_on_top = tk.BooleanVar(value=False)
        self.is_active = False

        self._setup_ui()
        self._poll_state()
        
    def _setup_ui(self):
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Status Label
        self.status_label = ctk.CTkLabel(self, text="Status: Stopped", font=("Helvetica", 14))
        self.status_label.grid(row=0, column=0, columnspan=2, pady=(15, 10))

        # Status Indicator (Color Square)
        self.indicator = ctk.CTkFrame(self, width=40, height=40, fg_color="red", corner_radius=0)
        self.indicator.grid(row=1, column=0, columnspan=2, pady=5)

        # Button Frame
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=2, column=0, columnspan=2, pady=15)

        # Start/Stop Buttons
        self.start_btn = ctk.CTkButton(self.button_frame, text="Start", width=80, command=self._on_start_clicked)
        self.start_btn.pack(side="left", padx=15)

        self.stop_btn = ctk.CTkButton(self.button_frame, text="Stop", width=80, command=self._on_stop_clicked)
        self.stop_btn.pack(side="right", padx=15)

        # Always on top Checkbox
        self.ontop_cb = ctk.CTkCheckBox(self, text="Always on Top", variable=self.always_on_top, command=self._toggle_always_on_top)
        self.ontop_cb.grid(row=3, column=0, columnspan=2, pady=5)

    def _toggle_always_on_top(self):
        self.attributes("-topmost", self.always_on_top.get())

    def _on_start_clicked(self):
        from ui.tray import get_tray_manager
        tray = get_tray_manager()
        if tray.handle_activation_request(activate=True):
            logger.info("UI: Start clicked")
            threading.Thread(target=start_listening, daemon=True).start()

    def _on_stop_clicked(self):
        from ui.tray import get_tray_manager
        tray = get_tray_manager()
        if tray.handle_activation_request(activate=False):
            logger.info("UI: Stop clicked")
            stop_listening()

    def _poll_state(self):
        """Poll the utils flags to update UI state and detect shutdown."""
        if not utils.app_running.is_set():
            logger.info("UI: Shutdown signaled. Closing window.")
            self.destroy()
            return

        currently_active = utils.is_listening.is_set()
        
        if currently_active != self.is_active:
            self.is_active = currently_active
            self._update_status_display()
            
        # Check again in 100ms
        self.after(100, self._poll_state)
        
    def _update_status_display(self):
        if self.is_active:
            self.status_label.configure(text="Status: Listening")
            self.indicator.configure(fg_color="green")
        else:
            self.status_label.configure(text="Status: Stopped")
            self.indicator.configure(fg_color="red")

def launch_ui():
    """Entry point to launch the floating GUI."""
    # Set default theme
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    app = VoiceMintUI()
    app.mainloop()
