"""Tk desktop UI. Worker threads never access Tk widgets."""
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from .engine import Settings, type_text
from .windows import Keyboard, StopHotkey


class App:
    def __init__(self, root):
        self.root = root
        self.stop = threading.Event()
        self.events = queue.Queue()
        self.worker = None
        self.keyboard = Keyboard()
        self.hotkey = StopHotkey(self.stop.set)
        self.hotkey.start()
        root.title("Autotyper")
        root.geometry("720x520")
        root.minsize(520, 380)
        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Autotyper", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Paste text, press Start, then select the window to type into.").pack(anchor="w", pady=(4, 12))
        editor = ttk.Frame(frame)
        editor.pack(fill="both", expand=True)
        self.text = tk.Text(editor, wrap="word", undo=True, font=("Segoe UI", 11))
        scrollbar = ttk.Scrollbar(editor, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.text.pack(fill="both", expand=True)
        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=12)
        self.speed = tk.StringVar(value="20")
        self.delay = tk.StringVar(value="5")
        ttk.Label(controls, text="Characters / second").pack(side="left")
        self.speed_input = ttk.Spinbox(controls, from_=1, to=200, width=6, textvariable=self.speed)
        self.speed_input.pack(side="left", padx=(8, 20))
        ttk.Label(controls, text="Delay (seconds)").pack(side="left")
        self.delay_input = ttk.Spinbox(controls, from_=1, to=60, width=6, textvariable=self.delay)
        self.delay_input.pack(side="left", padx=8)
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")
        self.start_button = ttk.Button(buttons, text="Start typing", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(buttons, text="Stop (F8)", command=self.stop.set, state="disabled")
        self.stop_button.pack(side="left", padx=8)
        self.status = tk.StringVar(value="Ready. F8 stops typing from any window.")
        ttk.Label(frame, textvariable=self.status, wraplength=650).pack(anchor="w", pady=(12, 0))
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(50, self.poll)

    def start(self):
        if self.worker and self.worker.is_alive():
            return
        try:
            settings = Settings(float(self.speed.get()), float(self.delay.get()))
            text = self.text.get("1.0", "end-1c")
            if not text:
                raise ValueError("Enter some text first.")
            text.encode("utf-16-le")
        except ValueError as error:
            messagebox.showerror("Check your input", str(error))
            return
        self.stop.clear()
        self.set_running(True)
        self.worker = threading.Thread(target=self.run, args=(text, settings), daemon=True)
        self.worker.start()

    def run(self, text, settings):
        try:
            type_text(text, settings, self.stop, self.keyboard.send,
                      lambda value: self.events.put(("status", value)))
        except Exception as error:
            self.events.put(("error", str(error)))
        finally:
            self.events.put(("done", None))

    def set_running(self, running):
        for widget in (self.start_button, self.speed_input, self.delay_input, self.text):
            widget.configure(state="disabled" if running else "normal")
        self.stop_button.configure(state="normal" if running else "disabled")

    def poll(self):
        latest = None
        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "status":
                latest = value
            elif kind == "error":
                latest = f"Error: {value}"
                messagebox.showerror("Typing failed", value)
            elif kind == "done":
                self.set_running(False)
        if latest is not None:
            self.status.set(latest)
        self.root.after(50, self.poll)

    def close(self):
        self.stop.set()
        if self.worker:
            self.worker.join(timeout=2)
        self.hotkey.close()
        self.root.destroy()


def main():
    if sys.platform != "win32":
        raise SystemExit("Autotyper is a Windows desktop app. Run it on Windows 10 or newer.")
    root = tk.Tk()
    try:
        App(root)
    except Exception as error:
        messagebox.showerror("Autotyper could not start", str(error))
        root.destroy()
        raise SystemExit(1) from error
    root.mainloop()
