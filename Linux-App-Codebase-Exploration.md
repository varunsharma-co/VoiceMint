# Codebase Exploration — Old VoiceMint (Linux)

Explored 2026-11-23 from `refs/Old-VoiceMint-Linux/`. This machine is macOS. The app was not installed, not run, and not modified. API keys were not copied into this document. Personal dictated text in `history/history.json` was not copied either.

The archive is the Linux Mint Cinnamon voice-typing app, plus the previous browser-based app, plus a copied template kit that is not part of the product.

---

## 1. What the product is

VoiceMint is a Wispr Flow-style dictation tool. The user focuses any window, hits a global hotkey (or a Start button), speaks, and finalized speech-to-text lands at the cursor. A silence timer stops the session. The concatenated finals of that session are kept as history.

The desktop path never sends text through an LLM. Cleanup and rewriting live in a separate Chrome extension. The extension talks to a localhost WebSocket that the same Python process starts. The user pastes or selects text, picks a prompt, and Gemini Flash 2.5 Lite rewrites it.

The app the author actually ran, according to `config.json` and the logs, was:

- Speech provider: Soniox (`stt-rt-v5`), English, 16 kHz mono PCM.
- Injection: clipboard ghost-paste (Shift+Insert), not key-by-key typing.
- Hotkeys: Super+W start, Super+Q stop, Super+H paste the last history entry.
- Silence stop: 30 seconds with no transcript.
- History: last 5 session strings, flushed to disk every 120 minutes.
- LLM: present and listening on `127.0.0.1:6468`, unused in the saved logs.

Code defaults differ from that lived config. Defaults are uinput injection, Super+U / Super+I, a 45 second silence timer, and an 8-word clipboard flush. See section 5.

The README prices the cloud STT path at about $1/month and contrasts it with local Whisper. That figure is a claim in the README, not something measured here.

Target environment, stated in `GEMINI.md` and the install docs: Linux Mint Cinnamon, one Python 3.10+ process (the logs show 3.12), a venv named `voicemint`, X11 first, with some Wayland clipboard branches.

---

## 2. What is in the folder

`refs/Old-VoiceMint-Linux/` mixes three layers.

### The product (repo root of that folder)

| Path | Role |
|---|---|
| `main.py` | Process entry. Wires keyboard, injector, history timer, transcript consumer, LLM server, tray, hotkeys, Tk window. |
| `config.py`, `config.json` | Import-time settings. JSON is the user overlay. `.env` holds API keys and is not in this tree. |
| `utils.py` | Process flags, transcript queue, logging, single-instance lock, paste-last-message. |
| `stt/` | Microphone, silence watchdog, Soniox / AssemblyAI / Modulate. |
| `text_injection/` | Virtual keyboard, uinput typer, clipboard paster. |
| `ui/` | Tk window, settings, history viewer, pynput hotkeys, GTK tray. |
| `history/` | RAM buffer plus `history.json`. |
| `llm/` | Prompt modules, Gemini call, WebSocket server. |
| `chrome_extension/` | Manifest V3 popup and context menu. |
| `assets/` | Tray icons, start/stop wavs, unused images, a demo video. |
| `requirements.txt` | Unpinned Python packages. `evdev` is imported and not listed. |
| `README.md`, `USER_GUIDE.md`, `GEMINI.md`, `Installation_Deep_Dive.md`, `Adding_New_STT_Provider.md` | Human docs. Several are stale. Section 15. |

### The ancestor

`ai_docs/refs/Old-Voice-Typing-App/` is the previous generation: a mic client, a FastAPI server on port 8642, a Tk process supervisor, and a Chrome extension that typed into web fields. Section 11.

### Not the product

- `ai_docs/shipkit_templates/` and `ai_docs/refs/rag-simple/` are a copied Next.js / RAG “Shipkit” kit (document Q&A SaaS, Drizzle, landing-page templates). They are not VoiceMint.
- `ai_docs/dev_templates/python_agent.md` and `task_template.md` are authoring templates for the coding agent. They are not runtime code.
- `ai_docs/tasks/001` through `018` are the build diary (2026-04-05 to 2026-04-11).
- `Varun Working Files/` holds the author’s specs, permission notes, and the text-injection experiments.
- `logs/` is real runtime output from the Mint machine, 14 Jun 2026 through 10 Jul 2026.

---

## 3. How a dictation session works

```
Hotkey or Start button
        │
        ▼
TrayManager.handle_activation_request(True)
  icon → connecting, is_connecting = True
        │
        ▼
utils.is_listening.set()
daemon thread → stt.start_listening()
        │
        ├─ SilenceDetector armed (reset on every partial and final)
        ├─ get_transcriber(ACTIVE_STT_PROVIDER, api_key, callback)
        ├─ blocking WebSocket handshake
        ├─ utils.is_connected.set()
        ├─ tray: listening icon, notify-send, aplay start.wav
        ├─ send_loop daemon pulls audio_queue
        └─ sounddevice.InputStream, 16 kHz, mono, int16, 100 ms blocks
                │
                ▼
        PortAudio callback → audio_queue → provider.send_audio_chunk (binary WS frame)
                │
                ▼
        provider thread → callback(text, is_final)
                │
                ├─ always: reset silence timer, print a 60-char preview
                └─ only if is_final: utils.transcript_queue.put(text)
                        │
                        ▼
        queue_consumer (non-daemon thread)
          injector.inject(text)
          append into session_text
                        │
        Stop, silence timeout, or quit
          is_listening.clear()
          injector.flush() if clipboard
          history.add_session(session_text)
          close WebSocket, release mic
          tray: stopped icon, notify-send, aplay stop.wav
```

Partials never reach the injector and never reach the window. The floating UI only shows Stopped / Connecting / Listening. It does not show the words.

The LLM server starts with the process and stays idle unless the extension connects. It is not on this path.

---

## 4. Process, startup, and shutdown

One Python process. No `multiprocessing`, no FastAPI, no bash IPC. Coordination is `threading.Event`, `queue.Queue`, and one WebSocket.

Flags in `utils.py`:

- `app_running` — process lifetime. Clear this to quit.
- `is_listening` — user wants a session, including the connecting phase.
- `is_connected` — STT socket is up.
- `transcript_queue` — `queue.Queue[str]` of finalized strings only.

### Threads

| Thread | Daemon | Work |
|---|---|---|
| Main | — | `VoiceMintUI.mainloop()`. 100 ms poll of the two events. Owns `SIGUSR1`. |
| Tray | yes | `Gtk.main()` after the indicator is created. |
| Hotkeys | yes | `pynput.keyboard.GlobalHotKeys`. |
| `queue_consumer` | no | Inject finals, flush clipboard, write history. |
| LLM | yes | `asyncio` loop, `websockets.serve` on `127.0.0.1:6468`. |
| History timer | yes | Sleep N minutes, `flush_history`. |
| Per session | yes | `start_listening` blocks on the mic. Inner daemons: `send_loop`, provider receiver, silence `threading.Timer`. |

Tk stays on the main thread. GTK runs on the tray thread. `import ui` still imports GTK on the main thread before that.

### Startup order in `main.py`

Imports already do work, before the lock:

1. `config.py` calls `load_dotenv()` with no path (walks upward from the process cwd, not from the file). Then it reads or creates `config.json` next to `config.py`.
2. `utils.py` creates `logs/` in the cwd and attaches a midnight rotating file handler.
3. `history.py` registers `atexit` → `flush_history`.
4. Importing `text_injection` imports `evdev`.
5. Importing `ui` imports GTK 3 and Ayatana AppIndicator (or legacy AppIndicator3). A missing typelib kills the process here.
6. Importing `stt` imports `sounddevice`.

Then `main`:

1. `enforce_single_instance()` — flock on `/tmp/voicemint.lock`, write PID.
2. `app_running.set()`.
3. `with VirtualKeyboard() as vkb` — always opens `/dev/uinput`, even when the injection method is clipboard. `PermissionError` aborts startup. The error string suggests sudo. The docs say sudo breaks the user’s mic (PulseAudio / PipeWire session).
4. `get_injector(vkb)` — one engine for the life of the process.
5. History timer thread.
6. Consumer thread.
7. LLM thread.
8. Copy icons and wavs to `/dev/shm/voicemint_assets`, then start the tray thread.
9. Hotkey listener. A bad hotkey string is logged and the app continues with no listener.
10. `launch_ui()` blocks on Tk.

Listening does not start at launch. The user presses Start or the hotkey.

### Single instance

`utils.enforce_single_instance()`:

- Opens `/tmp/voicemint.lock` with `O_CREAT | O_RDWR` and `fcntl.flock(LOCK_EX | LOCK_NB)`.
- Winner writes its PID and keeps the fd open. The lock is the flock, not the file’s existence. A dead process releases the flock, so a leftover file does not block the next start. `USER_GUIDE.md` still tells the user to delete a stale lock.
- Loser reads the PID, sends `SIGUSR1`, prints a line, and exits 0 even if `kill` fails.

The handler is installed only inside `VoiceMintUI.__init__`, which is after the other threads have started. `_handle_sigusr1` deiconifies the window (via `after`) and calls `messagebox.showinfo` directly from the signal handler. Before the window exists, `SIGUSR1` is still the default terminate signal. A second launch during startup can kill the first process.

There is no `SIGTERM` or `SIGHUP` handler. Ctrl+C is caught only around `launch_ui()`.

On the way out, `main` deletes the lock file and does not close the fd. Unlinking while the flock is held drops the directory entry. A new process can create a new inode and lock it while the old process is still exiting.

### Shutdown

“Soft shutdown” clears `app_running`. The Tk poll sees it and `destroy()`s, so `mainloop()` returns. Triggers:

- Tray item “Quit VoiceMint”.
- Settings “Save & Exit”.
- Ctrl+C.

Closing the window does not quit. `WM_DELETE_WINDOW` calls `withdraw()`. Restore is the tray item “Open VoiceMint”, or a second launch’s `SIGUSR1`.

Cleanup, still inside `with VirtualKeyboard()`:

1. Sleep 0.5 s, clear `app_running`.
2. `stt.stop_listening()`.
3. Join consumer (2 s) and LLM thread (2 s).
4. `close_injector()` — clipboard `close()` can still flush.
5. Stop the hotkey listener.
6. `shutil.rmtree("/dev/shm/voicemint_assets")`.
7. Remove the lock file.
8. `VirtualKeyboard.__exit__` closes the `UInput` device.

`_do_restart` does not exec a new process. The user relaunches by hand.

The consumer is non-daemon. If `join` times out, the interpreter stays up until that thread finishes. `SIGKILL` skips `atexit`, lock removal, and RAM cleanup. The kernel still drops the flock and the uinput fd. History still sitting in RAM is lost.

### Desktop launcher

Freedesktop `.desktop` file, not DBus activation.

- Template: `ui/desktop_app/voicemint.desktop.template`
- Personal copy: `ui/desktop_app_VARUN/voicemint.desktop`

The personal file points at the Mint checkout:

```
Exec=/home/varun/Desktop/Projects/Python/Portfolio/VoiceMint/voicemint/bin/python3 .../main.py
Icon=.../assets/icon-on-128.png
```

`Terminal=false`, `Type=Application`, `Categories=Utility;AudioVideo;`, `StartupNotify=true`, `X-GNOME-Autostart-enabled=true`. No `Path=`, so the session manager picks the working directory, often `$HOME`. That matters because `load_dotenv()` and `logs/` are cwd-relative. A menu launch can miss the project `.env` and write logs in the wrong place. `print()` output is discarded.

Install docs copy the file to `~/.local/share/applications/` and optionally `~/.config/autostart/`. There is no systemd user unit.

---

## 5. Configuration and secrets

`config.py` holds code defaults, enum parsing, and constants that never enter JSON. `config.json` is the persisted overlay. There is no hot reload. Names are bound once at import. The settings window writes the file and then quits the process.

Load rules: start from `_DEFAULT_CONFIG`, `dict.update` with the JSON file. A missing file is created from the defaults. A corrupt file prints an error and keeps the defaults. A bad enum string falls back without rewriting the file: STT → Soniox, injection → uinput, LLM → Gemini Flash 2.5 Lite. A bad numeric type crashes import.

`config.json` is gitignored (`.gitignore` line 22) but present in this snapshot. It contains no secrets.

### Settings

| Key | Code default | This `config.json` | Who uses it | In the settings window? |
|---|---|---|---|---|
| `ACTIVE_STT_PROVIDER` | `soniox` | `soniox` | `get_transcriber` | Yes. Soniox, Modulate, Assemblyai |
| `ACTIVE_INJECTION_METHOD` | `uinput` | `clipboard` | `get_injector` | Yes. Uinput, Clipboard |
| `SILENCE_TIMEOUT_SECONDS` | `45.0` | `30.0` | `SilenceDetector` | Yes |
| `SAMPLE_RATE` | `16000` | `16000` | Mic and STT connect | No |
| `HOTKEY_START` | `<cmd>+u` | `<cmd>+w` | pynput | Yes, stored as `<cmd>+` plus what the user types |
| `HOTKEY_STOP` | `<cmd>+i` | `<cmd>+q` | pynput | Yes |
| `HOTKEY_COPY_LAST` | `<cmd>+h` | absent, so the `.get` fallback applies | `paste_last_message` | No. A save does not add the missing key |
| `MAX_HISTORY_MESSAGES` | `5` | `5` | RAM cap and file cap | Yes |
| `HISTORY_SAVE_INTERVAL_MINUTES` | `60.0` | `120.0` | Flush timer. Task 004 asked for 30 | Yes |
| `IDEAL_FLUSH_WORD_COUNT` | `8` | `2` | Clipboard ideal flush. Task 003 asked for 25 | Yes |
| `FAILSAFE_FLUSH_MULTIPLIER` | `1.6` | `1.6` | Flush with no punctuation | Yes |
| `CLIPBOARD_RESTORE_DELAY_SEC` | `0.5` | `0.5` | Sleep before restoring the clipboard. Task 003 asked for 1.0 | Yes |
| `LOG_KEEP_DAYS` | `7` | `7` | Log rotation. Read only when logging is set up | No |
| `DEFAULT_LLM_PROVIDER` | `gemini_flash_2_5_lite` | same | Extension `init` / `format` fallback | No |

Code-only, not in `config.json`:

- `SPEECH_ENDPOINT_DELAY_MS = 1000`. Soniox `max_endpoint_delay_ms` and AssemblyAI `end_utterance_silence_threshold`. Modulate does not send it. Comment says 500–3000 ms. Nothing enforces the range.
- `WEBSOCKET_PING_INTERVAL = 20`, `WEBSOCKET_PING_TIMEOUT = 30`. Passed into all three STT sockets. `GEMINI.md` says client pings can be disabled because audio every 100 ms is enough. The code still sets both, and the only logged errors are keepalive ping timeouts.

The settings UI loads and saves the raw JSON file, not a merged schema. Unknown keys already in the file survive. Keys absent from the file are not backfilled. Validation is `int()` / `float()` plus a message box. No ranges, no empty-hotkey check, no duplicate-hotkey check. “Save & Exit” writes, clears `app_running`, and quits. “Close” discards edits. Dropdown labels are `.capitalize()`, so AssemblyAI displays as “Assemblyai”, which round-trips through `.lower()`.

Hotkeys are registered once at process start from the imported constants. Saving does not rebind them.

### API keys

Not in `config.json`. `config.py` builds `STT_API_KEYS` from the environment:

- `SONIOX_API_KEY`
- `MODULATE_API_KEY`
- `ASSEMBLYAI_API_KEY`

`GEMINI_API_KEY` is read later inside `llm/providers/gemini_flash_2_5_lite.py` with `os.getenv`. It is not part of `STT_API_KEYS`.

Flow, from `Varun Working Files/Flow_of_API_variables.md`, still true in `stt/mic.py`:

```
.env → config.STT_API_KEYS[ACTIVE_STT_PROVIDER]
     → get_transcriber(provider, api_key, callback)
     → provider.self.api_key
```

A missing STT key raises `ValueError` inside `get_transcriber` when listening starts, not at process start. `.env.example` has placeholders for the four names. This checkout has no `.env`.

`GEMINI.md` calls the Assembly key `ASSEMBLY_API_KEY`. The code and `.env.example` use `ASSEMBLYAI_API_KEY`.

`load_dotenv()` runs because `config.py` is imported, and it searches from the cwd. A `.desktop` file with no `Path=` can fail to find the project `.env`.

---

## 6. Speech to text

`stt/mic.py` owns the microphone. Providers own the socket. Providers never open an audio device.

### Contract

```
BaseTranscriber                         stt/stt_providers/base.py
├── SonioxTranscriber                   soniox.py
├── AssemblyAITranscriber               assembly.py
└── ModulateTranscriber                 modulate.py
```

`TranscriptCallback = Callable[[str, bool], None]`.

Each provider implements:

- `start_connection(sample_rate: int)` — handshake, then start the receiver thread.
- `send_audio_chunk(audio_chunk: bytes)` — one raw PCM chunk as a binary frame.
- `close_connection()` — idempotent teardown.

Factory `get_transcriber()` in `stt/stt_providers/manager.py` raises `ValueError` if the key is missing or the enum value is not one of the three. There is no manager class and no `switch()` method. The active provider is `config.ACTIVE_STT_PROVIDER`, parsed once. An invalid string becomes Soniox.

`Adding_New_STT_Provider.md` matches the code for the enum, the env var, the subclass, the factory, and the settings combobox. It is behind the code on Modulate: the comparison table and the sample snippets show Soniox and Assembly only. The checklist says every provider must send `SPEECH_ENDPOINT_DELAY_MS`. Modulate does not.

### Shared socket behavior

All three use `websockets.sync.client.connect`. No REST, no batch mode, no reconnect. Ping interval 20 s, ping timeout 30 s.

Audio from the mic, unchanged by the provider: mono PCM s16le, 16 kHz, about 100 ms per chunk (1600 frames, 3200 bytes). `int16` native endian is little-endian on x86_64 and on Apple Silicon.

The receiver loops while the stop event is clear and `app_running` is set, `recv` with a 1 s timeout. A server error or `done` sets the stop event so later sends no-op. It does not clear `is_listening`, does not clear `is_connected`, and does not close the mic. The session then sits until the silence timer or a manual stop, with the mic still open.

`send` and `recv` run on two threads with no application lock. `websockets` is unpinned in `requirements.txt`.

### Soniox

- URL: `wss://stt-rt.soniox.com/transcribe-websocket`.
- Auth: first text frame includes `"api_key"`. Later frames are binary audio.
- Model `stt-rt-v5` (the ancestor used `stt-rt-v4`). `language_hints: ["en"]`, strict, language ID off, diarization off, endpoint detection on, `max_endpoint_delay_ms: 1000`, `pcm_s16le`, 1 channel.
- Tokens: drop literal `"<end>"` and empty text. Final tokens accumulate. The callback string is the joined finals plus the current interim (cumulative for this endpoint, not a delta). `is_final=True` only when this message added at least one final and left no non-finals. The buffer is then cleared, so the queue receives one endpoint’s text.
- Close sends no end-of-audio frame. The last partial can be discarded.
- `error_code` or `finished` ends the receiver.

This is correct only if Soniox does not resend tokens it already marked final. The code does not track token ids. A resend would duplicate injected text.

### AssemblyAI

- URL: `wss://streaming.assemblyai.com/v3/ws` (the task doc specified v2 `wss://api.assemblyai.com/v2/realtime/ws`).
- Query: `sample_rate`, `end_utterance_silence_threshold=1000`, `speech_model=universal-streaming-english`. A comment mentions `u3-rt-pro`, which is not active.
- Auth header: `Authorization: <api_key>` with no `Bearer` prefix.
- v2 names `PartialTranscript` / `FinalTranscript` are still handled. v3 `Turn` calls `callback(transcript, end_of_turn)`. Empty text is not delivered, so it does not reset the watchdog.
- Close sends `{"terminate_session": True}`, which is the v2 shutdown shape, on a v3 socket.

### Modulate

- URL: `wss://platform.modulate.ai/api/velma-2-stt-streaming-english-v2`. Model and language are the path.
- Auth: `api_key` query parameter (can land in proxy logs). Also `audio_format=s16le`, `sample_rate`, `num_channels=1`, `endpointing=true`. No millisecond delay.
- `partial_utterance` → interim. `utterance` → final. `error` or `done` ends the receiver.
- Close sends an empty text frame `""` as end-of-stream.

`IMPORTANT_tweak_for_later.txt` still says to get Modulate running first because it is the cheapest, then look at Inword, Grok, Speechmatics, Fal, Groq, and Gladia. Modulate is already in the factory and the settings dropdown. The others are not. Deepgram existed in the ancestor and in task 001, and it is absent here: no module, no enum, no `DEEPGRAM_API_KEY`.

### Microphone

`sounddevice` (PortAudio), default input device. No `device=`, no device picker, no `latency=`.

- Session thread blocks inside `sd.InputStream`.
- `audio_callback` runs on the PortAudio thread and does `audio_queue.put(indata.tobytes())` when listening, the app is running, and a transcriber exists.
- `send_loop` is the only caller of `send_audio_chunk`.
- `audio_queue` is unbounded. The provider doc’s “under 200 KB” cap is not implemented. A stalled sender grows the queue by about 32 KB/s.
- Overflow status is printed and the chunk is still queued.

### Silence

`SilenceDetector` in `stt/silence.py` is not an energy or WebRTC VAD. It is a resettable `threading.Timer`. Any transcript callback, partial or final, restarts the full timeout. No transcript for `SILENCE_TIMEOUT_SECONDS` calls `_on_silence_timeout`: tray deactivates with the timeout notification and `stop.wav`, then `stop_listening()`.

The timer starts only after the socket connects, so a session that never receives a transcript also dies after one full timeout. Audio is streamed until then. That timer is the billing cutoff.

`SPEECH_ENDPOINT_DELAY_MS` is a different knob. It tells Soniox and Assembly when a phrase becomes final. `GEMINI.md` calls it a local VAD threshold. It is not.

A model that keeps emitting partials on noise never auto-stops. Speech the model never transcribes is treated as silence.

### State, as the UI sees it

There is no STT state enum. `VoiceMintUI._poll_state` every 100 ms:

| Condition | Label | Square |
|---|---|---|
| not `is_listening` | Status: Stopped | `#D9534F` |
| listening, not connected | Status: Connecting... | `#F0AD4E` |
| both set | Status: Listening | `#2FA572` |

`is_listening` is set by the UI or the hotkey before `start_listening` runs, so the window sits on Connecting during the handshake.

### STT failure modes that matter

- Missing key or unknown provider: `start_listening` prints and returns without clearing `is_listening` and without telling the tray. The UI stays on Connecting. The consumer will not flush history, because it waits for `is_listening` to clear.
- Handshake failure does recover: the `except` path deactivates the tray and calls `stop_listening()`.
- Dead socket mid-session: sends stop, mic stays open, `is_connected` stays set, until silence or a manual stop. No reconnect.
- Stop during `start_connection` can race. After the handshake returns, the code sets `is_connected` and opens the mic without rechecking `is_listening`.
- Tail audio still in `audio_queue` at stop is dropped. Soniox is closed with no end frame, so the server may never finalize the last partial.
- `close_connection`’s closed-flag is not locked. User stop and the `finally` block can both enter it.
- `KeyboardInterrupt` inside `start_listening` almost never runs. That function is on a daemon. Ctrl+C is handled on the main thread.

---

## 7. Putting text on the screen

One injector, chosen at startup. There is no per-string fallback and no “if uinput fails, try clipboard” chain. The README’s “clipboard fallback” wording does not match the code.

`BaseInjector.inject(text) -> bool`. The consumer ignores the return value. `get_injector(vkb)` caches the instance. A later call returns the cache. `ClipboardInjector` is not re-exported from `text_injection/__init__.py`. `evdev` is imported by `virtual_keyboard.py`, `uinput_engine.py`, and `clipboard_engine.py`, so `import text_injection` cannot load on a machine without Linux `evdev`. `evdev` is not in `requirements.txt`.

Nothing in this path looks up a window id. Keystrokes and the paste chord hit whatever has keyboard focus. If VoiceMint’s own window is focused, they land there.

### Virtual keyboard (always)

`VirtualKeyboard` in `text_injection/virtual_keyboard.py`. Device name `"voicemint-virtual-keyboard"`.

- Capabilities: `EV_KEY` only. Every `KEY_*` code whose value is `< 256`. The experiment comment says higher codes raise kernel `Errno 22`.
- `__enter__` creates `evdev.UInput`, then sleeps 0.5 s so the desktop registers the new keyboard.
- `write_event` holds a `threading.Lock`, writes, and `syn()`s.
- `simulate_shift_insert`: Left Shift down, Insert down+up, Left Shift up, one lock around the chord, no sleep.
- `__exit__` closes the device.

Task 018 (2026-04-11) consolidated this so both engines share one device. Before that, each engine built its own `UInput`, which showed the OS multiple keyboards and could leak a device on crash. `pynput` stayed the hotkey listener on purpose. Task 018 asked to add `inject_char()` on `VirtualKeyboard` and to stop calling `close_injector()` from `main`. `inject_char()` was not added. `close_injector()` is still called, and that call is what flushes a leftover clipboard buffer. Hardware close stays in `__exit__`.

### Uinput typer

`UInputInjector.inject`:

- `rstrip` trailing spaces, then append exactly one space, so sequential finals do not run together.
- For each character, shift down, key down, key up, shift up, each as its own event plus `syn`, then `time.sleep(0.01)`.
- Unmapped characters are skipped with no log.

The map is US QWERTY position scancodes, not Unicode:

- Letters, shift if uppercase.
- Digits unshifted.
- Unshifted: space `. , - ' / \ ; = \`` `[ ]`
- Shifted: `? ! @ # $ % ^ & * ( ) _ + { } | : " < > ~`

Only Left Shift. Caps Lock is not tracked, so Caps Lock inverts letters. No Ctrl, Alt, AltGr, or Right Shift. Newline, tab, emoji, smart quotes, and all non-ASCII (including Devanagari and `।`) are skipped. `str.isalpha()` is true for Hindi letters, then `getattr(ecodes, "KEY_ज")` is `None`, and the character disappears. History still stores the original string, so Super+H can paste what the keyboard could not type.

On a non-US layout, `KEY_A` is a position, not the letter A. A long final is visibly typed at about 100 characters per second. The “instant” wording in the docs does not describe this path.

### Clipboard paster

This is the method in `config.json` and in 39 of 41 logged startups. It still needs `/dev/uinput`, because the paste key is a hardware chord.

`inject` only buffers. It strips each chunk and joins chunks with a single space. Nothing appears in the target app until a flush.

Flush triggers:

1. Ideal: word count ≥ `IDEAL_FLUSH_WORD_COUNT` (2 in the live file) and the last non-space character is `.` `?` `!` or Hindi danda `।`.
2. Failsafe: word count ≥ ideal × 1.6 (3.2 with the live file), even without punctuation.
3. Cleanup: consumer calls `flush()` when listening has stopped and the queue is empty. A one-word leftover is normal.

A single STT final is one append. A 107-word final that ends in punctuation pastes as one blob. The threshold is a minimum, not a splitter. While listening continues, a short buffer with no punctuation sits invisible until stop, silence, or the failsafe.

`flush` sequence:

1. `payload = buffer.strip() + " "`, then the buffer is cleared immediately. A missed paste loses the chunk from the injector. History may still have it.
2. Backup CLIPBOARD via `pyperclip.paste()` and PRIMARY via xclip / xsel / wl-paste.
3. Write the payload to both selections.
4. Sleep 0.05 s.
5. `vkb.simulate_shift_insert()`. Not Ctrl+V and not Ctrl+Shift+V.
6. Sleep `CLIPBOARD_RESTORE_DELAY_SEC` (0.5 s) on the consumer thread. Newer finals wait. The mic thread is not blocked.
7. Restore both selections.

PRIMARY tool order: if `WAYLAND_DISPLAY` is set and `wl-paste` / `wl-copy` exist, use those and do not also call xclip. Otherwise `xclip -selection primary`, otherwise `xsel --primary`. `pyperclip` separately owns the CLIPBOARD selection (what Ctrl+V pastes). Shift+Insert in X11 terminals and many GTK apps pastes PRIMARY. Both are set so terminals and GUI apps have a chance. Middle-click also sees PRIMARY during the 0.5 s window.

“Successfully pasted N words” is logged after the chord is written, not after the target app confirms it.

Unicode and internal newlines survive on this path, because the payload is raw text. `strip()` removes leading and trailing whitespace, so a chunk that is only a newline disappears, and newlines at the edges of a chunk are removed. Chunks are then joined with a space.

### Paste last message

`utils.paste_last_message`, hotkey Super+H by default:

- Reads `get_recent_history(1)`, appends a trailing space.
- Same backup / copy / sleep 0.05 / Shift+Insert / sleep / restore sequence.
- The chord is sent with `pynput.keyboard.Controller`, not with the virtual keyboard, after releasing `Key.cmd`.
- Empty history logs a line. No notification.
- It pastes into the focused app and restores the clipboard. It does not leave the text on the clipboard. Task 014 asked for a copy.

This runs on the hotkey thread and can interleave with a clipboard flush. There is no shared lock. On Wayland, pynput’s XTest path and `/dev/uinput` can disagree about whether a chord arrives.

### What the experiments concluded

Scripts in `Varun Working Files/Text Injection Method Testing/`:

| File | Tried | What happened to it |
|---|---|---|
| `test_pynput.py` | `Controller.type()` for English and Devanagari | Not shipped. Task 003 calls pynput / pyautogui unreliable on Wayland. |
| `test_pynput2.py` | ASCII via pynput. Other characters via GTK hex (Ctrl+Shift+U). Also highlight-and-replace of an interim. | Not shipped. Hex entry only works in GTK widgets that support it. Interim overwrite was dropped with partials. |
| `test_uinput.py` | evdev device, highlight-and-replace, `KEY_* < 256` to avoid `Errno 22` | Superseded. |
| `test_uinput2_THIS.py` | Header says `# WORKING METHOD`. Two final ASCII streams, 0.01 s per key, 0.5 s device registration. | This is the hardware path that shipped, plus a larger punctuation map and the trailing-space rule. Hindi in its sample is still silently dropped. |
| `test_uinput3.py` | ASCII scancodes, Ctrl+Shift+U at the kernel for everything else | Not shipped. |
| `test_copy_paste_only.py` | pyperclip + Shift+Insert, restore commented out | Prototype. Leaving the payload on the clipboard was rejected. |
| `test_cp2.py` | Same sequence with restore after 0.1 s | Became the ghost-paste sequence. Delays later moved to config. |
| `test_hybrid.py` | `str.isascii()` → uinput, else clipboard with Ctrl+Shift+V | Not shipped. Ctrl+Shift+V means different things in different apps. |
| `test_hybrid2.py` | Same router, unicode paste via Shift+Insert | The chord was kept. The router was not. The user picks one engine for the whole process. |

Daily use did not stay on the experiment winner. The user guide says to try both and recommends clipboard. The live config and the logs follow that.

### Permissions, two recipes

`SETUP_PERMISSIONS.md`, `README.md`, and `Installation_Deep_Dive.md`:

- `sudo groupadd -f uinput`
- `sudo usermod -aG uinput $USER`
- udev `KERNEL=="uinput", MODE="0660", GROUP="uinput", OPTIONS+="static_node=uinput"` in `/etc/udev/rules.d/99-uinput.rules`
- `udevadm control --reload-rules` and `udevadm trigger`
- Log out so the group applies. Do not run the app under sudo.

`ui/desktop_app/Installing_on_Linux_Mint_Cinnamon.md` and the personal desktop setup doc use group `input` and `KERNEL=="uinput", GROUP="input", MODE="0660"`. Whichever file was written to udev last is the one that was installed. The logs show `UInput` succeeding. They do not show which rule was active.

Other system packages the docs install outside pip: `python3-tk`, `gir1.2-gtk-3.0`, `gir1.2-ayatanaappindicator3-0.1`, `libgirepository1.0-dev`, `gcc`, `libcairo2-dev`, `pkg-config`, `python3-dev`. Binaries the code shells out to: `aplay`, `notify-send`, and for PRIMARY `xclip` or `xsel` or `wl-copy` / `wl-paste`.

---

## 8. Desktop UI, hotkeys, and tray

Two toolkits. No pystray, no CustomTkinter, no Qt. `requirements.txt` lists `pynput` and `PyGObject`.

| Surface | Class | Toolkit |
|---|---|---|
| Main window | `VoiceMintUI(tk.Tk)` in `ui/floating.py` | Tk + ttk, theme `clam` |
| Settings | `SettingsPanel(tk.Toplevel)` | same |
| History viewer | `HistoryViewerWindow` in `ui/settings_ui.py` | same |
| Tray | `TrayManager` | GTK 3 + Ayatana AppIndicator, else AppIndicator3 |

`ui/floating.py` is a normal decorated window, 280×260, not resizable, title “VoiceMint”. It does not call `overrideredirect`. `GEMINI.md` calls it a borderless floating UI. The code does not. There is no click-through, no transparency, no cursor following, and no saved position. The original single-source-of-truth doc described a borderless listening animation at the bottom of the screen. That was not built.

Widgets: status label, a color square (`width=4`, `height=2`), Start, Stop, Settings, and an “Always on Top” checkbox. Always-on-top is `attributes("-topmost")`, default off, not saved. Fonts are Noto Sans 10 and 11. The checkbox uses a small ttk style.

Settings and history are modal (`transient`, `grab_set` on `<Map>`). Opening history from settings nests two grabs. Close on the history window does not restore the parent grab.

Settings geometry in `ui/constants.py` is `500x400`. History is `650x640` (minimum 550×450). `MIN_SETTINGS_WINDOW_SIZE` `(500, 500)` is never applied. Task 008 asked for a 550×450 history window.

### Tray

Indicator id `voicemint_indicator`, category `APPLICATION_STATUS`. The indicator stays `ACTIVE`. The icon file changes.

| State | File | Sound | Notification |
|---|---|---|---|
| Inactive | `icon-off-128.png` | `stop.wav` on a real stop | “VoiceMint Deactivated” / “Stopped Listening...” |
| Connecting | `icon-connecting-128.png` | none | none |
| Active | `icon-on-128.png` | `start.wav` after the socket connects | “VoiceMint Activated” / “Listening via {Provider}...” |

Provider text is `ACTIVE_STT_PROVIDER.value.capitalize()` (`Soniox`, `Modulate`, `Assemblyai`).

Other notifications:

- Already active or connecting: “Voice typing is already active or connecting.”
- Already stopped: “Voice typing is already stopped.”
- Silence timeout: “Silence timeout reached. Stopped listening.”

A failure inside `start_listening` that is not a handshake exception calls deactivate with no timeout flag, so the user sees a normal stop. There is no error icon. `assets/red-icon.png` is unused. `Extension Bar Icon.png` and `VoiceMint Demo.mkv` are unused by the app. `assets/icon_names.txt` lists only the three status PNGs.

Menu: “Open VoiceMint”, separator, “Quit VoiceMint”. No Start, Stop, Settings, or History. Left-click is not bound. After the window is withdrawn, listening is toggled only by hotkeys.

`notify-send` and `aplay -q` are `subprocess.Popen` from whichever thread asked, not marshalled onto the GTK thread, and never `wait()`ed. Icons are attached with `-i`. No urgency and no replace-id.

`load_assets_to_ram` copies the three PNGs and two wavs to `/dev/shm/voicemint_assets`. Failure keeps the SSD path. `cleanup_ram_assets` runs from `main` after the UI exits.

If the Ayatana import fails, `setup_indicator` logs and the tray is `None`. Icon updates no-op. The Tk window still runs.

### Hotkeys

`pynput.keyboard.GlobalHotKeys`, one daemon, no `suppress=True`, no `XGrabKey`. `<cmd>` is Super on X11 and Command on macOS.

| Key | Code default | Live JSON | Editable in settings | Action |
|---|---|---|---|---|
| `HOTKEY_START` | `<cmd>+u` | `<cmd>+w` | Yes | Suppress, then start |
| `HOTKEY_STOP` | `<cmd>+i` | `<cmd>+q` | Yes | Suppress, then stop |
| `HOTKEY_COPY_LAST` | `<cmd>+h` | missing, fallback `<cmd>+h` | No | Suppress, then `paste_last_message` |

`USER_GUIDE.md` documents Super+U / Super+I / Super+H and says all three are editable. The logs show `<cmd>+w`, `<cmd>+q`, `<cmd>+h` on every startup.

Suppression exists because `GlobalHotKeys` does not swallow the key. `_suppress_typed_character` releases `Key.cmd` and taps Backspace so the letter is deleted and X11 does not see Super+Backspace. When the combo inserts no character, that Backspace deletes the previous character in the focused app. A comment on `start_hotkey_listener` says X11 suppression is native. The implementation comment says the opposite, and the implementation is the Backspace hack.

Duplicate hotkey strings collapse in the dict. There is no conflict check. An empty entry becomes `"<cmd>+"`.

### Settings controls

Notebook tabs: Application, Hotkeys, History, Clipboard Injection.

Application writes `ACTIVE_STT_PROVIDER`, `ACTIVE_INJECTION_METHOD`, `SILENCE_TIMEOUT_SECONDS`.

Hotkeys writes `HOTKEY_START` and `HOTKEY_STOP` only, prefixed with `<cmd>+`.

History writes `MAX_HISTORY_MESSAGES` and `HISTORY_SAVE_INTERVAL_MINUTES`, plus a button “View Last 3 Messages”.

Clipboard writes `IDEAL_FLUSH_WORD_COUNT`, `FAILSAFE_FLUSH_MULTIPLIER`, `CLIPBOARD_RESTORE_DELAY_SEC`.

Not in the panel: `HOTKEY_COPY_LAST`, `SAMPLE_RATE`, `LOG_KEEP_DAYS`, `DEFAULT_LLM_PROVIDER`, endpoint delay, ping interval, ping timeout. The last three cannot be set from JSON at all.

The history viewer loads `get_recent_history(3)`, reverses so the newest card is “Message 1 (Newest)”, and shows read-only text with a Copy button. Copy uses the Tk clipboard (`clipboard_clear` / `clipboard_append`) and flips the button to “Copied!” for 1.5 s. It does not inject. Empty state says “No messages in current session.” The source is the file plus the pending RAM buffer, not only the live session. Task 008 asked for a tray menu entry that opens settings. The tray has no Settings item.

---

## 9. History

`history/history.py` stores a JSON array of plain strings. No timestamps, no provider, no model, no prompt, no polished text, no window or app context, no audio.

A record is the concatenated `is_final` chunks of one listening session, joined with single spaces. Blank text is dropped. `add_session` only appends to `_pending_sessions` under a lock, capped at `MAX_HISTORY_MESSAGES`.

Disk writes:

- Daemon timer, first fire after `HISTORY_SAVE_INTERVAL_MINUTES` (120 in the live file).
- `atexit` on a normal interpreter shutdown.

`flush_history` snapshots and clears the RAM list, reads the file, appends, keeps the last N, and `json.dump`s with mode `"w"`. A missing, corrupt, or non-list file is replaced by the new batch only. The write is not atomic. The file lock is not held across the read-modify-write. The timer and `atexit` can overlap. `get_recent_history` reads the file and then appends the pending list, so a flush between those steps can hide a message. `SIGKILL` skips `atexit`. A kill during dictation drops the session, because `add_session` runs after stop.

This snapshot’s `history/history.json` has 5 strings, about 23 KB, mode `700`. Lengths are roughly 1.1k, 0.4k, 7.6k, 13.5k, and 0.5k characters. They are real dictated text. Do not copy that file into a new repo, quote it, or use it as sample data. `main.py` also prints `[Consumer] FINAL TEXT:` to stdout. The history logger itself only records counts and paths.

Readers:

- Settings history viewer, last 3, newest first.
- Super+H via `paste_last_message`, last 1.
- Extension `init`, which sends `recent_message` from the last entry. Raw dictation, not LLM output.

---

## 10. LLM layer and Chrome extension

Streaming STT drops punctuation and keeps fillers. The LLM is an opt-in rewrite. It is not on the dictation path.

Desktop: finals are injected raw, then stored raw.

Extension, two entry points:

- Popup “Format Text” sends the scratchpad.
- Context menu “Send to VoiceMint” sends the page selection and writes the result back into the page.

“Use last voice message” only copies `recent_message` into the scratchpad. It does not call Gemini.

If the extension is not installed, voice typing still works. The WebSocket thread sits idle. The logs show the server listening on every startup and zero format requests.

### Provider

`llm/manager.py` `format_text(text, provider_name, prompt_name)` loads `SYSTEM_PROMPT` from `llm/prompts/<prompt_name>.py` and routes on the provider name. The only real branch is `gemini_flash_2_5_lite`. Any other string, including `""`, logs a warning and still calls Gemini.

`llm/providers/gemini_flash_2_5_lite.py`:

- Model `gemini-2.5-flash-lite`, library `google-genai`, async `generate_content`, not streaming.
- System instruction is the prompt’s `SYSTEM_PROMPT` when one was loaded. No temperature, tools, or JSON schema.
- Auth: `GEMINI_API_KEY` from the environment.
- No timeout.
- Missing key returns the string `"Error: GEMINI_API_KEY is not set."` as the formatted text.
- API exceptions return `"Error: {e}"` as formatted text. The socket still sends `format_response`, so the popup shows it and the context menu can replace the selection with that error string.

The ancestor forced a JSON field `model_answer` so the model could not preface the answer. This code returns `response.text` with no schema.

### Prompts

Discovered by listing `llm/prompts/*.py` except names starting with `__`. The stem is the id. Loaded with `importlib` on each format, not cached. The module must define `SYSTEM_PROMPT`. `system_prompt.py.template` is not loaded.

There is no config key for the active prompt. The extension dropdown is the selector. Display strips a leading `NN_`, splits on `_`, and title-cases.

| File | Id | Behavior |
|---|---|---|
| `01_voice_typing.py` | `01_voice_typing` | Role “Agent Jack”. Clean a transcript without changing words or tone. If the user says “Agent Jack”, treat that span as an instruction. Drop ums and ahs. Mix short and longer paragraphs. Output only the cleaned text. The sample also turns a spoken list into a numbered list and lightly fixes slips, which is looser than the “do not change words” rule. |
| `fix_grammar.py` | `fix_grammar` | The whole prompt is “Fix the grammar on the given sentence.” The file header still says `pep_fan.py`. The ancestor’s grammar prompt was a longer “keep the meaning” editor instruction. |
| `pep_fan.py` | `pep_fan` | “Answer as if you are a huge Pep Guardiola fan.” |
| `system_prompt.py.template` | not loaded | Placeholder. Copy to a new `.py`. |

The directory is scanned on every `init`, so a new file appears on the next popup open without restarting the server, as long as the process can see the file. The user guide says to restart. Edits to `SYSTEM_PROMPT` apply on the next `format`.

`init_response` does not send a providers list. The popup falls back to `[default_provider]`, so the LLM dropdown is only Gemini. The display name is hardcoded: “Gemini Flash 2.5 Lite”.

### WebSocket

`main.py` starts daemon thread `llm.start_llm_server` → `websocket_server.start_server_loop` → `asyncio.run`.

- Bind: `127.0.0.1:6468`. Comment: 6468 is M-I-N-T on a keypad. Not `0.0.0.0`. No TLS, no auth token, no origin check.
- Loop sleeps 0.5 s while `app_running` is set, then closes the server. Task 011 mentioned `stop_llm_server()`. It was not implemented.
- Any local process can connect, spend the Gemini key, and read the latest dictated message via `init`.

Client → server:

```json
{ "action": "init" }
{ "action": "format", "text": "...", "prompt": "01_voice_typing", "provider": "gemini_flash_2_5_lite" }
```

A missing `provider` key uses `DEFAULT_LLM_PROVIDER`. A present `""` does not. `dict.get` only defaults when the key is absent. The manager then still falls through to Gemini.

Server → client:

```json
{ "action": "init_response", "prompts": ["..."], "default_provider": "gemini_flash_2_5_lite", "recent_message": "<newest history string or empty>" }
{ "action": "format_response", "formatted_text": "..." }
{ "error": "..." }
```

Gemini failures are not socket-level errors. They arrive inside `formatted_text`.

If bind fails, the server thread logs and dies. Dictation continues.

### Chrome extension

Manifest V3, name “VoiceMint Extension”, version 1.0.

Permissions: `activeTab`, `scripting`, `contextMenus`, `storage`. Host: `ws://127.0.0.1:6468/*` only. No content script. Suggested command `_execute_action` is Ctrl+M, and Command+M on Mac. Chrome opens the popup itself. There is no command listener in `background.js`.

Toolbar icon stays `icons/icon-off-128.png`. `icon-on-128.png` is unused. Task 012 asked for an active icon. The icon does not change with server state.

Service worker:

- On install, context menu id `sendToVoiceMint`, title “Send to VoiceMint”, context `selection`. The user guide says “Add to VoiceMint”.
- On click, opens a new socket, reads `chrome.storage.local` keys `selectedPrompt` and `selectedProvider`, formats, then `chrome.scripting.executeScript` → `replaceSelection`, then closes the socket.
- Those two local keys are never written. The popup stores prompt and provider under `chrome.storage.session` key `voice_mint_tab_state[tabId]`. The menu therefore always sends `prompt: ""` and `provider: ""`, which means Gemini with no system prompt.
- `replaceSelection` uses `document.activeElement` if it is a textarea or input, otherwise the current DOM selection. It does not use the captured `selectionText`. If the menu stole focus, this can no-op. Socket failure is `console.error` only. No timeout.

Popup (500 px wide, Poppins from Google Fonts):

- Reset, theme switch, scratchpad, copy, “Use last voice message”.
- Prompt dropdown, LLM dropdown, “Format Text”.
- Second textarea, hidden until a response, with its own copy button.
- Copy uses `navigator.clipboard.writeText` and adds class `copied` for 1.5 s. `popup.css` has no `.copied` rule, so there is no visible copied state.
- Per-tab session state: raw text, formatted text, visibility, prompt, provider.
- On open, if the page selection is non-empty and different from the saved raw text, it replaces the scratchpad. The same selection does not reset (task 012).

The user guide says the user can dictate directly into the popup. The extension does not receive live transcripts. Dictation into a browser field only happens if the desktop injector types into a focused field, which is a separate path. The popup pulls a selection, or the last history line, or whatever the user types.

Dark mode: `theme-init.js` is a blocking script at the start of `<body>`. It reads `localStorage["voice_mint_theme"]` and adds `dark-mode` before paint if the value is `"dark"`. It never removes the class. `toggleTheme` writes `chrome.storage.local` and does not write `localStorage`. `initialize()` later copies storage into `localStorage` if they differ. The first popup open after a toggle can still flash the previous theme. Task 015 asked `toggleTheme` to write `localStorage`. That part is missing.

The extension JavaScript does not check the OS. It needs a Chromium that can load an unpacked MV3 extension and reach port 6468. The Linux-only pieces are all in the Python process.

---

## 11. The previous app

`ai_docs/refs/Old-Voice-Typing-App/` is a different architecture. The rewrite kept the product idea and replaced the shape.

### Old shape

Three processes, plus the browser. The archive does not contain the thing that starts the server, or `run_client.py`, or `voice_typing_HTML/`.

| Piece | What it is |
|---|---|
| Mic client | `voice_typing_app/client/mic_client.py`. One dictation is one process. `GUI/start_voice_typing.sh` runs a missing `run_client.py`. |
| FastAPI | `voice_typing_app/server/app.py` on `127.0.0.1:8642`. No uvicorn runner is archived. |
| Tk launcher | `GUI/app_launcher_gui.py`, class `AppLauncher`. Supervises the client. It is not a dictation UI. 280×200, title “Voice Typing by Varun”. |
| Extension | “Voice Typing by Varun” v3. Content script on `<all_urls>` types into the focused field. |

Client posts `POST /api/status/start` and `/stop`, and `POST /api/transcript` with `{transcript, is_final}` on every partial and every final (0.5 s timeout, failures swallowed). The server broadcasts that JSON to every `WS /ws/stt` client. Incoming socket text is ignored.

LLM was HTTP: `GET /api/llm/prompts`, `POST /api/llm/format-text` with `{text, prompt_name, provider_name}`. `provider_name` is the enum member name (`GEMINI_FLASH_2_5_LITE`), not the value. 404 if the prompt or key is missing.

The extension service worker holds the STT socket, reconnects after 5 s, and routes `NEW_TRANSCRIPT` to the focused tab or, if the popup is open, to the popup. A content script reports `TEXTBOX_FOCUSED`. `chrome.alarms` polls `/api/status` about every 3 s and swaps the toolbar icon.

`modules/injector.js` does real caret injection: finals insert `transcript + " "` at the selection, interims replace the previous interim span, and it dispatches a bubbling `input` event. Contenteditable is a blunt `innerText +=`. The README still describes a floating on-page scratchpad (`ui.js`, `drag.js`, `resize.js`). Those files are not in the archive. The content script comment says the on-page UI was removed.

The launcher polls `pgrep` every 2 s for status, and polls `/tmp/voice_typing.start` and `/tmp/voice_typing.stop` so `ipc_start.sh` / `ipc_stop.sh` can drive it. Paths are hardcoded to `/home/varun/Desktop/Projects/Python/Voice_Typing_Python` and venv `voice-typing`. Stop is `pkill -INT -f run_client.py`, so the client’s `finally` still runs. Silence calls `_thread.interrupt_main()`. Each STT class opened its own microphone. Config raised `ValueError` at import if the active STT key was missing.

Nothing in the old tree registers a global hotkey. The IPC shell scripts may have been bound in the desktop environment outside this snapshot.

### Old providers that the rewrite dropped

STT enum: AssemblyAI, Deepgram, Soniox. Each class owned `connect_and_stream(sample_rate)` and its own mic.

- Deepgram: SDK, `nova-2`, `en-US`, linear16, `smart_format`, block size 1024. Gone.
- Assembly: official SDK, `format_turns=True`, `MicrophoneStream`. Rewritten as a raw v3 WebSocket.
- Soniox: sync websockets, `stt-rt-v4`. Rewritten as `stt-rt-v5` with the mic pulled out.

LLM enum:

- `GEMINI_FLASH_2_5_LITE` value was the model id `gemini-2.5-flash-lite`. The rewrite’s value is the slug `gemini_flash_2_5_lite`.
- `GEMINI_FLASH_2_5` = `gemini-2.5-flash`.
- `CEREBRAS` via the OpenAI SDK at `https://api.cerebras.ai/v1`, model `gpt-oss-120b`.
- `VERCEL_AI_GATEWAY` at `https://ai-gateway.vercel.sh/v1`, model `openai/gpt-oss-120b`, gateway order `["cerebras", "groq"]`.

All four returned JSON `{"model_answer": string}`. Keys: `GEMINI_API_KEY` shared by both Gemini members, `CEREBRAS_API_KEY`, `AI_GATEWAY_API_KEY`. A missing LLM key warned. It did not crash import. The popup sent the provider per click.

Prompts were `01_voice_typing`, `02_pep_fan`, and a longer `fix_grammar`. The popup stripped the numeric prefix for display. `Ctrl+Enter` formatted.

### What the rewrite did

Kept, usually rewritten: Soniox and Assembly as a factory plus a callback `(text, is_final)`, 16 kHz, a silence timer (now `stop_listening()` instead of `interrupt_main()`), the prompt-module idea, Gemini Flash Lite, a localhost scratchpad with prompt dropdown and per-tab session storage, start/stop sounds, on/off icons, and Soniox `"<end>"` filtering.

Dropped: Deepgram, FastAPI, port 8642, the separate mic process, the Tk supervisor, `/tmp` file IPC, `pkill` shutdown, live browser injection, Cerebras, the Vercel gateway, full Gemini 2.5 Flash, the `model_answer` schema, and provider-owned microphones.

Redesigned into the current tree: one process, desktop injection, mic and network split so an STT callback is not stalled on an HTTP post, LLM moved to the action WebSocket on port 6468, Modulate added, session history added, settings UI added, tray states added, hotkeys added.

The README’s line that the extension bridge “uses lightweight websockets rather than a heavy FastAPI server” is the explicit break with the old design. `README.md` and `GEMINI.md` never name the ancestor.

Running both trees at once would also mean two servers, ports 8642 and 6468.

---

## 12. How it was built

Tasks in `ai_docs/tasks/`, checkboxes dated 2026-04-05 through 2026-04-11. “Final manual verification” is often still unchecked. That is the author’s review step. It does not mean the code is missing. He dictated specs, often to a second AI that rewrote them into the task template, then expected the coding agent to check boxes with timestamps and stop for a human test.

| Task | Date | What landed |
|---|---|---|
| 001 STT and audio | 04-05 | Mic, silence watchdog, provider base, Soniox, finals-only queue. Deepgram was deferred and never arrived. Assembly arrived in 013. |
| 002 Uinput injection | 04-06 | `UInputInjector`, US scancodes, ~10 ms between keys. Later shared via 018. |
| 003 Clipboard injection | 04-06 | Ghost-paste, word thresholds, Shift+Insert. Thresholds were later tuned down (25 → 8 → live 2). |
| 004 Session history | 04-06 | RAM buffer, delayed flush, `atexit`, last 5 strings. Landed as `history/`, not a root `history.py`. |
| 005 GUI and hotkeys | 04-07 | Window, Start/Stop, color square, always on top, global hotkeys. Specified CustomTkinter and `suppress=True`. Shipped as stock ttk and `GlobalHotKeys` plus the Backspace hack. Live hotkeys moved off the original Super+U / Super+I. |
| 006 Tray, notifications, RAM assets | 04-07 | Ayatana tray, `notify-send`, `aplay`, `/dev/shm` cache with SSD fallback. The task said AppIndicator3, GTK on the main thread, and no fallback. The tray loop runs on a background thread. Tk stays on main. |
| 007 Settings and `config.json` | 04-08 | The task file still says CustomTkinter. A later prompt (native ttk, Noto Sans, Save & Exit with no dialog) is what the code does. Provider switch requires a relaunch. |
| 008 History viewer | 04-09 | Last-3 modal cards and Copy. Window is larger than the task asked. Not reachable from the tray. |
| 009 Log rotation | 04-09 | Midnight rotation, keep 7 days. |
| 010 Second instance | 04-10 | Lock file, `SIGUSR1`, “already running” message box. Helpers live in `utils.py`. |
| 011 LLM WebSocket and extension | 04-09 | Port 6468, actions `init` and `format`, Gemini Lite only. `stop_llm_server` was not added. Numeric prompt prefixes were not stripped. |
| 012 Extension UI | 04-10 | Per-tab session state, reset, Ctrl+M. |
| 013 AssemblyAI | 04-10 | Landed, then moved from the v2 URL in the task to the v3 streaming URL. Not the default. |
| 014 Copy-last hotkey | 04-10 | Hotkey exists. Behavior became paste-and-restore, not copy. Missing from `config.json` and from the settings form. |
| 015 Dark-mode FOUC | 04-10 | `theme-init.js` landed. `toggleTheme` still does not write `localStorage` itself. |
| 016 Refresh `GEMINI.md` | 04-10 | File tree and architecture notes. It does not point at the single-source-of-truth doc. |
| 017 User guide | 04-11 | `USER_GUIDE.md`, seven sections. Several sections have since drifted from the code. |
| 018 One uinput context manager | 04-11 | `VirtualKeyboard` shared by both injectors, `with` block in `main`. `close_injector()` was supposed to go away and is still called. |

Modulate is in the product and in none of these eighteen tasks. It matches the “later tweak” note.

Described and not present, or only partly present:

- Deepgram.
- The borderless bottom-of-screen listening animation.
- Automatic Unicode-versus-ASCII injection. The user picks one engine.
- Ctrl+V paste. Production uses Shift+Insert.
- Live provider switch without restart.
- CustomTkinter and pystray.
- An LLM panel inside a Tk window. Replaced by the extension.
- `stop_llm_server`, stripping `01_` from prompt ids, copy-last as a pure clipboard copy, copy-last in the settings form.
- GTK on the main thread, and “no SSD fallback” for tray assets.
- Assembly v2 as the shipped endpoint.

---

## 13. The author’s own notes

`Varun Working Files/Single_Source_of_Truth.md` is the original mission, written before several of the tasks changed it:

- One Python process on Linux Mint Cinnamon, X11 first.
- No bash IPC, no `/tmp` polling, no `multiprocessing`, no FastAPI.
- Threads and `queue.Queue`. State in `utils.py`.
- Mic via `sounddevice`. Only `is_final` text is typed.
- Silence timeout instead of a local VAD. The note said about 45–60 s. Code default is 45. The live file is 30.
- `config.py` plus `.env` for secrets. Enums for providers. Facade `__init__.py` files so `main.py` stays thin.
- A session is everything between start and stop, pauses included.
- History: last 5 sessions, RAM first, flush about every 30 minutes, `atexit`.
- Hotkey placeholders in that note are Super+W / Super+Q, which is what `config.json` actually uses. Task 005 later specified Super+U / Super+I, and the code defaults followed the task. The machine he used followed the note.
- The note’s tree put `history.json` at the repo root and left `llm/` empty. Tray was specified as pystray. Injection was uinput for ASCII and clipboard Ctrl+V for other scripts.

`Flow_of_API_variables.md` is the dependency-injection chain in section 5. It stops at Soniox. The same dict now also has Modulate and AssemblyAI. `SPEECH_ENDPOINT_DELAY_MS`, `WEBSOCKET_PING_INTERVAL`, and `WEBSOCKET_PING_TIMEOUT` are called out as code-only.

`SETUP_PERMISSIONS.md` is the uinput group recipe, the “do not use sudo” warning, the Ayatana packages, `aplay` already on Mint, and `python3-tk` on the system rather than in the venv. The note disagrees with itself on the venv directory name: `./voicemint/bin/python` versus `source venv/bin/activate`. The logs and the `.desktop` file use `voicemint`.

`IMPORTANT_tweak_for_later.txt` is only an STT shopping list: Inword, Grok, Speechmatics, Fal, Groq, Gladia, and Modulate first because of price. It does not mention injection.

Working style visible from the prompts: he course-corrects in follow-up dictations, abandoned CustomTkinter after a real `grab_set` TclError, will not use pystray, wants native ttk that matches the OS (the code then forces the `clam` theme), wants Noto Sans, and keeps injection experiments as throwaway scripts. “Voicemail” in one settings prompt is a mishear of VoiceMint.

---

## 14. What the logs show

`logs/voice_typing_logs.log` plus seven rotated files, 14 Jun 2026 through 10 Jul 2026. `logs/startup.log` is empty and is not referenced in code.

Logging is configured at import in `utils.py`:

- File `logs/voice_typing_logs.log` in the cwd.
- `TimedRotatingFileHandler`, midnight, `backupCount` from `LOG_KEEP_DAYS` (7).
- Root level INFO. No console handler. `websockets.*` shares this file.
- Format example shape: `04 Apr 2026; 02:11:58 PM`.
- The rotating log records injection word counts. It does not record transcript text.
- `GEMINI.md` says `print()` is forbidden for core logic. `main.py`, the consumer, and the STT path still print. Those lines are lost when `Terminal=false`.

Observed:

- 41 startups. Every one reports `VirtualKeyboard` success and “GTK AppIndicator setup complete”.
- Hotkeys on every line: Start `<cmd>+w`, Stop `<cmd>+q`, Copy Last `<cmd>+h`.
- Injection: clipboard 39 times, uinput twice (19 Jun and 21 Jun 2026), then back to clipboard.
- STT provider name is not logged. The current JSON says Soniox. No AssemblyAI or Modulate strings appear.
- LLM server listens on `127.0.0.1:6468` every start. No “client connected” and no format-request lines.
- Copy-last ran 5 times. `SIGUSR1` was received once (21 Jun 2026).
- The only errors are 6× `keepalive ping failed` / `ConnectionClosedError: sent 1011` on 26 Jun 2026. Tracebacks point at the Mint venv, Python 3.12, under `/home/varun/Desktop/Projects/Python/Portfolio/VoiceMint/`.
- No uinput permission failures, no `aplay` or `notify-send` failures, no API keys.

So the Mint box he used could open `/dev/uinput`, could show an Ayatana tray, mostly pasted rather than typed, and did not exercise the extension during this log window. The 1011 timeouts match `GEMINI.md`’s own warning about client pings, which the code still enables.

---

## 15. Where the docs and the code disagree

These are the drifts worth remembering before treating a doc as the spec.

| Topic | Docs | Code and lived config |
|---|---|---|
| Default hotkeys | User guide: Super+U / Super+I / Super+H, all editable | JSON and logs: Super+W / Super+Q, and Super+H with no settings control |
| Tray colors | User guide §2.4: green idle, red listening | Filenames: connecting, on, off. Tk square: red stopped, amber connecting, green listening. `GEMINI.md` matches the square |
| Injection | README: uinput primary, clipboard as fallback | One method for the process. Live method is clipboard, and clipboard still opens uinput for Shift+Insert |
| STT list | User guide: Soniox or AssemblyAI | Enum and settings also include Modulate. The “later tweak” note still talks about getting Modulate running |
| Assembly env var | `GEMINI.md`: `ASSEMBLY_API_KEY` | `ASSEMBLYAI_API_KEY` |
| Source of truth | `GEMINI.md`: `config.json`. User guide: `config.py` | JSON wins for keys it contains. Several constants never round-trip |
| Window | `GEMINI.md`: borderless floating UI | Decorated 280×260 Tk window. Close hides it. The guide says it minimizes to the taskbar |
| Theme | `GEMINI.md`: native Mint theme | ttk theme `clam`, font Noto Sans |
| UI toolkit | Comments and tasks 005 and 007: CustomTkinter | Stock `tkinter` / `ttk` |
| Context menu | User guide: “Add to VoiceMint” | `background.js`: “Send to VoiceMint” |
| Extension behavior | User guide: dictate into the popup. Install doc: floating scratchpad | No live transcripts. No on-page scratchpad. Scratchpad is the popup |
| Prompt prefix | Task 011: strip `01_` | Ids stay prefixed. The popup strips them only for display |
| Copy last | Task 014 and the guide: copy | Paste via Shift+Insert, then restore the clipboard |
| Pings | `GEMINI.md`: can disable client pings to avoid 1011 | Hardcoded 20 s / 30 s. Logs show 1011s |
| uinput group | README and deep-dive: group `uinput`. Cinnamon install doc: group `input` | Both recipes are in the tree. Logs only show that open succeeded |
| Sudo | Docs: never. Code `PermissionError`: suggests sudo | — |
| Stale lock | User guide: delete `/tmp/voicemint.lock` | The lock is the flock. A dead process does not block the next start |
| `print()` | `GEMINI.md`: forbidden in core logic | Used on the STT and main paths |
| Tree in `GEMINI.md` | `02_pep_fan.py`, no `virtual_keyboard.py` | `pep_fan.py`, and `virtual_keyboard.py` exists |
| LICENSE | README says MIT and names a `LICENSE` file | That file is not in the tree |
| Assembly endpoint | Task 013: v2 realtime URL | v3 `streaming.assemblyai.com`, with a v2 terminate frame |
| Modulate in the provider doc | Comparison table omits it | Implemented |

---

## 16. Platform assumptions

The product code is a Linux desktop app that happens to be sitting on a Mac. These are the couplings, grouped by what they touch.

### Will not import or start on macOS as written

- `from evdev import UInput, ecodes` in three injection modules. Needs Linux `linux/input.h` and `/dev/uinput`. `main` constructs `VirtualKeyboard` before it knows whether injection is clipboard or uinput, so clipboard mode fails at the same point.
- The US `KEY_*` map is evdev scancodes. There is no `CGEvent` or `IOHIDUserDevice` path.
- GTK 3 and Ayatana AppIndicator. On failure the tray degrades to “no icon”, it does not switch to `NSStatusItem`. `Gtk.main()` on a background thread, with GTK imported earlier on the main thread, is an X11 arrangement. macOS Tk wants the main thread on AppKit.
- `aplay` and `notify-send`.

### Will run with the wrong meaning

- pynput `<cmd>` is Super on X11 and Command on macOS. The lived hotkeys `<cmd>+w` and `<cmd>+q` are Close Window and Quit on a Mac.
- The Backspace suppression hack is an X11 workaround (“otherwise X11 interprets it as Super+Backspace”). On macOS it can delete the previous character.
- Shift+Insert is the Linux paste chord. macOS paste is Command+V.
- `pyperclip` can talk to `pbcopy` on Darwin. The paste path still also drives X11 PRIMARY (`xclip`, `xsel`) or Wayland (`wl-copy`) and then sends Shift+Insert.
- `/dev/shm/voicemint_assets` does not exist. `load_assets_to_ram` already falls back to the repo `assets/` directory when the copy fails. That part is safe.
- `fcntl.flock`, `/tmp/voicemint.lock`, and `SIGUSR1` exist on macOS. The message box can still show. The tray will not.
- Freedesktop `.desktop` files and `X-GNOME-Autostart-enabled` do nothing for a Mac app bundle.
- Personal `Exec` and `Icon` paths are `/home/varun/Desktop/Projects/Python/Portfolio/VoiceMint/...`.

### Audio is the least Linux-specific piece, and it is still untested here

`sounddevice` uses PortAudio. The code asks for the default input at 16 kHz, mono, int16, from a background daemon thread, with no device id. On macOS that is the CoreAudio default input. Microphone permission is per app or per terminal (TCC). A prompt triggered off the main thread is unreliable. Bluetooth and aggregate devices often reject 16 kHz mono. The Linux docs already warn that running as root yields “Invalid sample rate” because the process leaves the user PulseAudio / PipeWire session. The macOS failure mode is CoreAudio and TCC, not that one.

The socket layer (`websockets`, the silence timer, the queue, PCM s16le framing) does not mention ALSA, Pulse, or PipeWire.

### Wayland, still on Linux

Kernel uinput is what the author counted on for Wayland, because a real HID device is not an XTest client. Global hotkeys are pynput’s default backend, which on Linux is Xorg and only partly works under XWayland. The app never sets `PYNPUT_BACKEND` and never uses pynput’s own uinput backend (the scratch notes say that backend wants root and is unreliable with layouts). On a pure Wayland session, evdev typing can work while Super+W and Super+H do not. Shift+Insert is “paste PRIMARY” in X11 terminals. On Wayland compositors it is not guaranteed. The guide already says some terminals miss the paste.

### Dependencies

`requirements.txt`, no pins: `sounddevice`, `websockets`, `python-dotenv`, `numpy`, `pyperclip`, `pynput`, `PyGObject`, `google-genai`.

`numpy` is not imported by name. `sounddevice` callbacks receive ndarray buffers, so it is an implicit runtime dependency. `evdev` is imported and not listed. Without it, import fails before `main`.

---

## 17. Incomplete work and bugs worth remembering

Collected so the next conversation does not have to rediscover them. Several are “the task said X and the code does Y” from section 12. These are the ones that change behavior.

**STT**

- A missing API key leaves the UI on Connecting forever. Handshake failure does recover. Socket death mid-session does not. The mic stays open until the silence timer.
- Soniox close sends no end-of-audio frame, so the last partial can be dropped. The append-only final buffer duplicates text if the server resends already-final tokens.
- Assembly speaks v3 and shuts down with a v2 `terminate_session` frame. v2 message names are still handled and could double-inject if a socket ever emitted both.
- Modulate cannot set the 1000 ms endpoint delay the other two use. Its API key is in the query string.
- No reconnect. No input-device setting. No language or model setting. All three are hardcoded per provider.
- `audio_queue` is unbounded.

**Injection**

- uinput silently drops non-ASCII, newlines, and tabs, and assumes a US layout.
- Clipboard clears the buffer before the paste. “Successfully pasted” means the chord was written.
- The consumer blocks for the 0.5 s restore. Super+H can race a flush, and the two paste paths do not share a lock (pynput versus uinput).
- `inject()` failure is ignored.
- Permission failure on `/dev/uinput` is an uncaught traceback from `VirtualKeyboard.__enter__`, and the message suggests sudo.

**UI and process**

- `SIGUSR1` is armed only after the Tk window exists, and the message box runs inside the signal handler.
- Failed `get_transcriber` sticks the tray and the square on Connecting.
- Settings save quits and does not relaunch, and does not refresh in-process constants.
- Nested history-viewer grab may not restore the settings grab.
- Copy-last is missing from the Hotkeys tab and from `config.json`.

**Extension**

- The context menu ignores the prompt and provider the popup selected.
- Gemini errors look like successful text and can replace the page selection.
- Dark-mode FOUC fix is half done.
- The providers dropdown implies a choice the server does not implement.
- No timeout on the Gemini call or the context-menu socket.
- `init` on localhost has no shared secret.

**History**

- Delayed flush plus `atexit`. Crash and `SIGKILL` drop the RAM buffer. The file write is not atomic.
- Schema cannot answer “what did I dictate, into which app, with which provider”.

---

## 18. Questions that came up

These are for the structuring conversation. They are not answered here.

### What the product should be on macOS

1. Is the product still “type into whatever app has focus”, or is the browser the main target again, or both?
2. The ancestor solved browser typing with a content script and caret-replace, and never needed a kernel device. The rewrite threw that away on purpose so dictation would work outside the browser. Which of those is the goal now?
3. For OS-level typing on macOS, the portable half of the current design is “put text on the clipboard and send the paste chord”. The scancode engine cannot move. Is clipboard-and-Command+V the injection strategy to design around, with Accessibility permission, or is there a different bar (per-app integrations, only the browser, a menu item the user clicks)?
4. The lived hotkeys are Super+W and Super+Q. On a Mac those chords already mean Close and Quit. What should the modifier and the keys be?
5. The window he actually used is a small always-available control panel plus a tray, not the borderless overlay the early spec described. Which of those is the UI to keep?

### What to carry forward

6. Which STT providers are in scope? Soniox is the one the logs show. Assembly is implemented on a newer endpoint than its task. Modulate is implemented and still described as a future experiment. Deepgram, Cerebras, and the Vercel gateway were dropped. Should any of those come back, or is the set “one STT and one LLM” until the structure is settled?
7. Should formatting stay a separate browser step, move back onto the dictation path, or stay out of the first macOS version?
8. The `model_answer` JSON schema was dropped when Gemini was rewritten. The prompts still say “output only the cleaned text”. Was losing the schema accidental?
9. `fix_grammar.py` is a one-liner and its header still says `pep_fan.py`. The ancestor’s grammar prompt was longer. Which text is the one to keep?
10. Is the prompt-as-a-Python-module pattern something to keep, or should prompts be data files?

### Shape of the program

11. The single-process model was a deliberate rejection of the old client/server/launcher split. Is that still the constraint, or is a split (menu bar app, helper, extension) on the table because macOS permissions and the browser want different lifetimes?
12. Settings currently require a full quit and a manual relaunch, and several knobs are not in the JSON file at all. Should configuration be something that can change while the process stays up?
13. History is five strings and a two-hour flush. Is that enough, or does a new structure want timestamps, provider, and raw versus polished text? The current file should not be migrated as sample content.
14. `load_dotenv()` and `logs/` follow the process cwd, and the `.desktop` file has no `Path=`. Should paths be anchored to the install location from the start?
15. Two uinput permission recipes are in the tree. That only matters if Linux stays a supported target alongside macOS. Is Linux Mint still a target, or is this archive a reference while the new work is macOS-only?

### Smaller facts that change a port

16. Should a dead STT socket stop the session immediately? Today it waits out the silence timer with the mic open.
17. Does current Soniox `stt-rt-v5` send only newly final tokens, or the full list every frame? The injector assumes the first.
18. What end-of-stream frame does Soniox require so the last utterance finalizes?
19. Does Assembly v3 honor `end_utterance_silence_threshold` and `terminate_session`?
20. What is Modulate’s default endpointing delay?
21. Was Super+H meant to paste, or to copy? The task and the code disagree, and the settings UI cannot edit it.
22. The context menu always formats with an empty prompt. Is that a bug to fix if the extension survives, or a reason the extension protocol should be redesigned?
23. `SIGUSR1` plus a Tk message box worked at least once on the Mint box (21 Jun 2026). It is still invoked from a signal handler. Worth knowing if that pattern is copied.

---

## Privacy

`history/history.json` is real dictated text from the Linux machine: five personal transcripts, one of them long, with no metadata. It must not be copied into a new repo, quoted, or used as sample data. The same applies to anything that prints finals. `main.py` writes `[Consumer] FINAL TEXT:` to stdout.

The LLM `init` action returns the newest of those strings to any process that can open `127.0.0.1:6468`. There is no shared secret.
