import json
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import ttk

import config
import utils
from history.history import get_recent_history
from ui.constants import (
    GLOBAL_FONT,
    HISTORY_WINDOW_GEOMETRY,
    MIN_HISTORY_WINDOW_SIZE,
    PAD_X,
    PAD_Y,
    SETTINGS_WINDOW_GEOMETRY,
)

logger = utils.get_logger(__name__)

class SettingsPanel(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("VoiceMint Settings")
        self.geometry(SETTINGS_WINDOW_GEOMETRY)
        self.resizable(False, False)

        self.config_path = config.CONFIG_PATH
        self.current_config = self._load_config_json()

        self._setup_ui()

        # Make modal - safe to grab here, but wait until window is mapped just in case
        self.transient(parent)
        self.bind("<Map>", self._on_map)

    def _on_map(self, event):
        self.grab_set()
        self.unbind("<Map>")

    def _load_config_json(self) -> dict:
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config.json for settings UI: {e}")
            return {}

    def _save_config_json(self, new_config: dict):
        try:
            with open(self.config_path, "w") as f:
                json.dump(new_config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config.json: {e}")
            return False

    def _setup_ui(self):
        container = ttk.Frame(self, padding=(PAD_X, PAD_Y))
        container.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, PAD_Y))

        self.tab_app = ttk.Frame(self.notebook, padding=(PAD_X, PAD_Y))
        self.tab_hotkeys = ttk.Frame(self.notebook, padding=(PAD_X, PAD_Y))
        self.tab_history = ttk.Frame(self.notebook, padding=(PAD_X, PAD_Y))
        self.tab_clipboard = ttk.Frame(self.notebook, padding=(PAD_X, PAD_Y))

        self.notebook.add(self.tab_app, text="Application")
        self.notebook.add(self.tab_hotkeys, text="Hotkeys")
        self.notebook.add(self.tab_history, text="History")
        self.notebook.add(self.tab_clipboard, text="Clipboard Injection")

        self._build_app_tab()
        self._build_hotkeys_tab()
        self._build_history_tab()
        self._build_clipboard_tab()

        # Bottom section
        bottom_frame = ttk.Frame(container)
        bottom_frame.pack(fill=tk.X)

        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(pady=(0, 5))

        self.save_btn = ttk.Button(btn_frame, text="Save & Exit", command=self._on_save)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        self.close_btn = ttk.Button(btn_frame, text="Close", command=self.destroy)
        self.close_btn.pack(side=tk.LEFT, padx=5)

        note_label = ttk.Label(
            bottom_frame, 
            text="Note: Click 'Save & Exit' to apply changes.\nYou will need to relaunch VoiceMint manually.",
            justify=tk.CENTER,
            foreground="gray"
        )
        note_label.pack()

    def _build_app_tab(self):
        ttk.Label(self.tab_app, text="STT Provider:").grid(row=0, column=0, padx=(0, PAD_X), pady=PAD_Y, sticky=tk.W)
        stt_val = self.current_config.get("ACTIVE_STT_PROVIDER", "soniox").capitalize()
        self.stt_var = tk.StringVar(value=stt_val)
        self.stt_menu = ttk.Combobox(self.tab_app, textvariable=self.stt_var, values=["Soniox", "Deepgram", "Assemblyai"], state="readonly")
        self.stt_menu.grid(row=0, column=1, pady=PAD_Y, sticky=tk.EW)

        ttk.Label(self.tab_app, text="Injection Method:").grid(row=1, column=0, padx=(0, PAD_X), pady=PAD_Y, sticky=tk.W)
        inj_val = self.current_config.get("ACTIVE_INJECTION_METHOD", "uinput").capitalize()
        self.injection_var = tk.StringVar(value=inj_val)
        self.injection_menu = ttk.Combobox(self.tab_app, textvariable=self.injection_var, values=["Uinput", "Clipboard"], state="readonly")
        self.injection_menu.grid(row=1, column=1, pady=PAD_Y, sticky=tk.EW)

        ttk.Label(self.tab_app, text="Silence Timeout (sec):").grid(row=2, column=0, padx=(0, PAD_X), pady=PAD_Y, sticky=tk.W)
        silence_val = self.current_config.get("SILENCE_TIMEOUT_SECONDS", 45.0)
        try:
            silence_str = str(int(float(silence_val))) if float(silence_val).is_integer() else str(silence_val)
        except (ValueError, TypeError):
            silence_str = str(silence_val)
        self.silence_var = tk.StringVar(value=silence_str)
        self.silence_entry = ttk.Entry(self.tab_app, textvariable=self.silence_var)
        self.silence_entry.grid(row=2, column=1, pady=PAD_Y, sticky=tk.EW)

        self.tab_app.columnconfigure(1, weight=1)

    def _build_hotkeys_tab(self):
        ttk.Label(self.tab_hotkeys, text="Start Hotkey:").grid(row=0, column=0, padx=(0, PAD_X), pady=PAD_Y, sticky=tk.W)
        start_frame = ttk.Frame(self.tab_hotkeys)
        start_frame.grid(row=0, column=1, pady=PAD_Y, sticky=tk.W)
        ttk.Label(start_frame, text="Super + ").pack(side=tk.LEFT)
        start_val = self.current_config.get("HOTKEY_START", "<cmd>+u").replace("<cmd>+", "")
        self.start_hotkey_var = tk.StringVar(value=start_val)
        self.start_entry = ttk.Entry(start_frame, textvariable=self.start_hotkey_var, width=5)
        self.start_entry.pack(side=tk.LEFT)

        ttk.Label(self.tab_hotkeys, text="Stop Hotkey:").grid(row=1, column=0, padx=(0, PAD_X), pady=PAD_Y, sticky=tk.W)
        stop_frame = ttk.Frame(self.tab_hotkeys)
        stop_frame.grid(row=1, column=1, pady=PAD_Y, sticky=tk.W)
        ttk.Label(stop_frame, text="Super + ").pack(side=tk.LEFT)
        stop_val = self.current_config.get("HOTKEY_STOP", "<cmd>+i").replace("<cmd>+", "")
        self.stop_hotkey_var = tk.StringVar(value=stop_val)
        self.stop_entry = ttk.Entry(stop_frame, textvariable=self.stop_hotkey_var, width=5)
        self.stop_entry.pack(side=tk.LEFT)

        self.tab_hotkeys.columnconfigure(1, weight=1)

    def _build_history_tab(self):
        ttk.Label(self.tab_history, text="Max History Messages:").grid(row=0, column=0, padx=(0, PAD_X), pady=PAD_Y, sticky=tk.W)
        self.max_history_var = tk.StringVar(value=str(self.current_config.get("MAX_HISTORY_MESSAGES", "5")))
        self.max_history_entry = ttk.Entry(self.tab_history, textvariable=self.max_history_var)
        self.max_history_entry.grid(row=0, column=1, pady=PAD_Y, sticky=tk.EW)

        ttk.Label(self.tab_history, text="History Save Interval (min):").grid(row=1, column=0, padx=(0, PAD_X), pady=PAD_Y, sticky=tk.W)
        history_val = self.current_config.get("HISTORY_SAVE_INTERVAL_MINUTES", 60.0)
        try:
            history_str = str(int(float(history_val))) if float(history_val).is_integer() else str(history_val)
        except (ValueError, TypeError):
            history_str = str(history_val)
        self.history_interval_var = tk.StringVar(value=history_str)
        self.history_interval_entry = ttk.Entry(self.tab_history, textvariable=self.history_interval_var)
        self.history_interval_entry.grid(row=1, column=1, pady=PAD_Y, sticky=tk.EW)

        ttk.Separator(self.tab_history, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        self.view_history_btn = ttk.Button(self.tab_history, text="View Last 3 Messages", command=self._open_history_viewer)
        self.view_history_btn.grid(row=3, column=0, columnspan=2, pady=(0, PAD_Y))

        self.tab_history.columnconfigure(1, weight=1)

    def _open_history_viewer(self):
        HistoryViewerWindow(self)

    def _build_clipboard_tab(self):
        ttk.Label(self.tab_clipboard, text="Ideal Flush Word Count:").grid(row=0, column=0, padx=(0, PAD_X), pady=PAD_Y, sticky=tk.W)
        self.flush_word_var = tk.StringVar(value=str(self.current_config.get("IDEAL_FLUSH_WORD_COUNT", "8")))
        self.flush_word_entry = ttk.Entry(self.tab_clipboard, textvariable=self.flush_word_var)
        self.flush_word_entry.grid(row=0, column=1, pady=PAD_Y, sticky=tk.EW)

        ttk.Label(self.tab_clipboard, text="Failsafe Flush Multiplier:").grid(row=1, column=0, padx=(0, PAD_X), pady=PAD_Y, sticky=tk.W)
        self.flush_multi_var = tk.StringVar(value=str(self.current_config.get("FAILSAFE_FLUSH_MULTIPLIER", "1.6")))
        self.flush_multi_entry = ttk.Entry(self.tab_clipboard, textvariable=self.flush_multi_var)
        self.flush_multi_entry.grid(row=1, column=1, pady=PAD_Y, sticky=tk.EW)

        ttk.Label(self.tab_clipboard, text="Clipboard Restore Delay (sec):").grid(row=2, column=0, padx=(0, PAD_X), pady=PAD_Y, sticky=tk.W)
        self.clip_delay_var = tk.StringVar(value=str(self.current_config.get("CLIPBOARD_RESTORE_DELAY_SEC", "0.5")))
        self.clip_delay_entry = ttk.Entry(self.tab_clipboard, textvariable=self.clip_delay_var)
        self.clip_delay_entry.grid(row=2, column=1, pady=PAD_Y, sticky=tk.EW)

        self.tab_clipboard.columnconfigure(1, weight=1)

    def _on_save(self):
        try:
            new_config = self.current_config.copy()
            new_config["ACTIVE_STT_PROVIDER"] = self.stt_var.get().lower()
            new_config["ACTIVE_INJECTION_METHOD"] = self.injection_var.get().lower()
            new_config["SILENCE_TIMEOUT_SECONDS"] = float(self.silence_var.get())
            new_config["HOTKEY_START"] = f"<cmd>+{self.start_hotkey_var.get()}"
            new_config["HOTKEY_STOP"] = f"<cmd>+{self.stop_hotkey_var.get()}"
            new_config["MAX_HISTORY_MESSAGES"] = int(self.max_history_var.get())
            new_config["HISTORY_SAVE_INTERVAL_MINUTES"] = float(self.history_interval_var.get())
            new_config["IDEAL_FLUSH_WORD_COUNT"] = int(self.flush_word_var.get())
            new_config["FAILSAFE_FLUSH_MULTIPLIER"] = float(self.flush_multi_var.get())
            new_config["CLIPBOARD_RESTORE_DELAY_SEC"] = float(self.clip_delay_var.get())

            if self._save_config_json(new_config):
                self._do_restart()
            else:
                messagebox.showerror("Error", "Failed to save settings to config.json.")
        except ValueError as e:
            # Simple error dialog if user typed bad numbers
            messagebox.showerror("Validation Error", f"Invalid input format: {e}")

    def _do_restart(self):
        utils.app_running.clear()
        self.destroy()
        try:
            from ui.tray import get_tray_manager
            get_tray_manager().on_quit(None)
        except Exception:
            pass


class HistoryViewerWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Session History")
        self.geometry(HISTORY_WINDOW_GEOMETRY)
        self.minsize(*MIN_HISTORY_WINDOW_SIZE)
        
        self.transient(parent)
        self.bind("<Map>", self._on_map)
        
        self._setup_ui()
        
    def _on_map(self, event):
        self.grab_set()
        self.unbind("<Map>")
        
    def _setup_ui(self):
        container = ttk.Frame(self, padding=(PAD_X, PAD_Y))
        container.pack(fill=tk.BOTH, expand=True)

        # Bottom Frame for the Close button
        bottom_frame = ttk.Frame(container)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        close_btn = ttk.Button(bottom_frame, text="Close", command=self.destroy)
        close_btn.pack(anchor=tk.CENTER)
        
        # Frame for the messages
        messages_frame = ttk.Frame(container)
        messages_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        history_msgs = get_recent_history(3)
        history_msgs.reverse() # newest first
        
        if not history_msgs:
            ttk.Label(messages_frame, text="No messages in current session.").pack(pady=20)
            return
            
        for i, msg in enumerate(history_msgs):
            card = ttk.LabelFrame(messages_frame, text=f"Message {i+1} (Newest)" if i == 0 else f"Message {i+1}")
            card.pack(fill=tk.X, pady=(0, 10))
            
            # Main content frame inside card
            content_frame = ttk.Frame(card, padding=5)
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            # Text and scrollbar frame
            text_frame = ttk.Frame(content_frame)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            text_widget = tk.Text(text_frame, height=3, wrap="word", font=GLOBAL_FONT)
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.insert("1.0", msg)
            text_widget.configure(state=tk.DISABLED)
            
            # Button frame below text
            btn_frame = ttk.Frame(content_frame)
            btn_frame.pack(fill=tk.X, pady=(5, 0))
            
            copy_btn = ttk.Button(btn_frame, text="Copy", width=8)
            copy_btn.configure(command=lambda m=msg, b=copy_btn: self._copy_text(m, b))
            copy_btn.pack(side=tk.LEFT)
            
    def _copy_text(self, text, btn):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        
        original_text = btn.cget("text")
        btn.configure(text="Copied!")
        self.after(1500, lambda: btn.configure(text=original_text))
