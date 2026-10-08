import threading
import unittest

from autotyper.engine import Settings, type_text
from autotyper.windows import key_events


class FakeStop:
    def __init__(self, cancel_at=None):
        self.waits = []
        self.cancel_at = cancel_at
        self.cancelled = False

    def wait(self, seconds):
        self.waits.append(seconds)
        if len(self.waits) == self.cancel_at:
            self.cancelled = True
        return self.cancelled

    def is_set(self):
        return self.cancelled


class TypingTests(unittest.TestCase):
    def test_normalizes_newlines_preserves_unicode_and_paces(self):
        sent, reports = [], []
        stop = FakeStop()
        self.assertTrue(type_text("A\r\n😀\rB", Settings(20, 1.5), stop, sent.append, reports.append))
        self.assertEqual(sent, list("A\n😀\nB"))
        self.assertEqual(stop.waits, [1, .5, .05, .05, .05, .05])
        self.assertEqual(reports[-1], "Completed: 5 characters.")

    def test_cancel_during_countdown(self):
        sent = []
        self.assertFalse(type_text("abc", Settings(), FakeStop(1), sent.append, lambda _: None))
        self.assertEqual(sent, [])

    def test_cancel_during_typing(self):
        sent = []
        self.assertFalse(type_text("abc", Settings(delay=1), FakeStop(2), sent.append, lambda _: None))
        self.assertEqual(sent, ["a"])

    def test_cancel_from_send_callback(self):
        stop = FakeStop()
        sent = []
        def send(char):
            sent.append(char)
            stop.cancelled = True
        self.assertFalse(type_text("abc", Settings(delay=1), stop, send, lambda _: None))
        self.assertEqual(sent, ["a"])

    def test_empty_text_rejected(self):
        with self.assertRaises(ValueError):
            type_text("", Settings(), FakeStop(), lambda _: None, lambda _: None)

    def test_invalid_settings(self):
        for speed, delay in [(0, 5), (201, 5), (20, 0), (20, 61), (float('nan'), 5), (20, float('inf'))]:
            with self.subTest(speed=speed, delay=delay), self.assertRaises(ValueError):
                Settings(speed, delay)

    def test_backend_error_propagates(self):
        def send(_):
            raise RuntimeError("blocked")
        with self.assertRaisesRegex(RuntimeError, "blocked"):
            type_text("a", Settings(delay=1), FakeStop(), send, lambda _: None)

    def test_real_event_interrupts_countdown(self):
        stop = threading.Event()
        stop.set()
        sent = []
        self.assertFalse(type_text("a", Settings(), stop, sent.append, lambda _: None))
        self.assertEqual(sent, [])

    def test_unicode_key_events(self):
        self.assertEqual(key_events("é"), [(0, 233, 4), (0, 233, 6)])
        self.assertEqual(key_events("😀"), [(0, 0xD83D, 4), (0, 0xD83D, 6), (0, 0xDE00, 4), (0, 0xDE00, 6)])

    def test_enter_and_tab(self):
        self.assertEqual(key_events("\n"), [(13, 0, 0), (13, 0, 2)])
        self.assertEqual(key_events("\t"), [(9, 0, 0), (9, 0, 2)])


if __name__ == "__main__":
    unittest.main()
