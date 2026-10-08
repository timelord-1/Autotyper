"""Windows SendInput and global F8 hotkey bindings (standard library only)."""
import ctypes
from ctypes import wintypes
import sys
import threading


def _api():
    if sys.platform != "win32":
        raise RuntimeError("Autotyper requires Windows 10 or newer.")
    return ctypes.WinDLL("user32", use_last_error=True)


ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]


class INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("value",)
    _fields_ = [("type", wintypes.DWORD), ("value", INPUTUNION)]


def key_events(char):
    if char in ("\n", "\t"):
        vk = 0x0D if char == "\n" else 0x09
        return [(vk, 0, 0), (vk, 0, 2)]
    encoded = char.encode("utf-16-le")
    events = []
    for offset in range(0, len(encoded), 2):
        unit = int.from_bytes(encoded[offset:offset + 2], "little")
        events.extend([(0, unit, 4), (0, unit, 6)])
    return events


class Keyboard:
    def __init__(self):
        self.api = _api()
        self.api.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        self.api.SendInput.restype = wintypes.UINT

    def send(self, char):
        events = key_events(char)
        inputs = (INPUT * len(events))()
        for item, (vk, scan, flags) in zip(inputs, events):
            item.type = 1
            item.ki = KEYBDINPUT(vk, scan, flags, 0, 0)
        count = self.api.SendInput(len(inputs), inputs, ctypes.sizeof(INPUT))
        if count != len(inputs):
            raise RuntimeError("Windows rejected keyboard input. Select an editable window running at the same privilege level.")


class StopHotkey:
    def __init__(self, callback):
        self.callback = callback
        self.ready = threading.Event()
        self.error = None
        self.thread_id = None
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()
        if not self.ready.wait(5):
            raise RuntimeError("Could not start the F8 listener.")
        if self.error:
            raise RuntimeError(self.error)

    def _run(self):
        api = _api()
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentThreadId.restype = wintypes.DWORD
        self.thread_id = kernel.GetCurrentThreadId()
        api.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        api.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
        api.GetMessageW.restype = ctypes.c_int
        if not api.RegisterHotKey(None, 1, 0x4000, 0x77):
            self.error = "F8 is already registered by another app. Close that app and restart Autotyper."
            self.ready.set()
            return
        self.ready.set()
        try:
            msg = wintypes.MSG()
            while api.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == 0x0312:
                    self.callback()
        finally:
            api.UnregisterHotKey(None, 1)

    def close(self):
        if self.thread_id and self.thread.is_alive():
            api = _api()
            api.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
            api.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)
            self.thread.join(timeout=2)
