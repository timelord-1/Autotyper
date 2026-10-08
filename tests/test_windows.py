import ctypes
import sys
import threading
import unittest

from autotyper.windows import INPUT, Keyboard, StopHotkey


@unittest.skipUnless(sys.platform == "win32", "Windows API test")
class WindowsTests(unittest.TestCase):
    def test_input_structure_and_api_load(self):
        self.assertEqual(ctypes.sizeof(INPUT), 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28)
        Keyboard()

    def test_global_stop_hotkey(self):
        stopped = threading.Event()
        hotkey = StopHotkey(stopped.set)
        hotkey.start()
        try:
            api = ctypes.WinDLL("user32", use_last_error=True)
            api.keybd_event.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_ulong, ctypes.c_size_t]
            api.keybd_event(0x77, 0, 0, 0)
            api.keybd_event(0x77, 0, 2, 0)
            self.assertTrue(stopped.wait(2), "Global F8 callback did not fire")
        finally:
            hotkey.close()
        self.assertFalse(hotkey.thread.is_alive())
