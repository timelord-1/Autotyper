# Autotyper

A Windows desktop app that types your text into the active window. Includes a configurable speed (1–200 characters/second), start delay (1–60 seconds), progress display, and a global **F8** stop hotkey. Built with Python's Tkinter and Windows APIs; no runtime packages required.

## Install and run

Use Windows 10 or newer with Python 3.11+ from python.org, including Tcl/Tk support. In PowerShell, from this checkout:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -e .
.\.venv\Scripts\python -m autotyper
```

The installed `autotyper` command also launches the app without a console.

1. Paste or type text into the editor.
2. Set speed and countdown duration, then press **Start typing**.
3. During the countdown, switch to the destination app and select its editable field.
4. Press **F8** at any time to stop, or use the app's Stop button. Closing Autotyper also stops typing.

F8 is reserved while Autotyper is open. If another app has registered it, Autotyper shows an error and exits. Text stays local and is not saved to disk or sent over the network.

Typing follows the active window, so keep the intended target focused. Newlines become Enter and tabs become Tab; these can submit forms or move focus in some applications. Unicode characters, including emoji, use UTF-16 keyboard events. Some games, terminals, or apps may not accept injected input. Windows prevents input into apps with higher privileges; run both apps at the same privilege level. Avoid holding modifier keys while typing.

## Development and tests

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

Core tests also run on Linux and macOS. Windows-only tests verify native structure sizes, API loading, and the global F8 callback. CI runs both Linux and Windows across Python 3.11–3.13.

Manual Windows acceptance check: open Notepad, start typing `Hello é 😀` with a newline and a tab, focus Notepad during the countdown, and confirm output. Try a long paragraph and press F8 during both countdown and typing; confirm no further input. Close Autotyper during a countdown and confirm nothing is typed. Keyboard injection and the GUI require an interactive Windows session; passing core tests on Linux does not validate these behaviours.

Project layout: `src/autotyper/app.py` contains the UI, `engine.py` contains pacing and cancellation, and `windows.py` contains keyboard injection and hotkey handling.
