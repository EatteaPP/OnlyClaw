from __future__ import annotations

import threading
import time
from typing import Callable

from pynput import keyboard


class HotkeyListener:
    def __init__(self, enabled: bool, key: str, interval_ms: int, on_trigger: Callable[[], None]):
        self.enabled = enabled
        self.key = key.lower()
        self.interval_ms = interval_ms
        self.on_trigger = on_trigger
        self._listener: keyboard.Listener | None = None
        self._last_press_time = 0.0
        self._lock = threading.Lock()

    def start(self) -> None:
        if not self.enabled:
            return

        try:
            self._listener = keyboard.Listener(on_press=self._on_press)
            self._listener.daemon = True
            self._listener.start()
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[hotkey] Warning: failed to start listener: {exc}")

    def stop(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
                self._listener.join()
            except Exception:
                pass
            self._listener = None

    def _matches_key(self, key: keyboard.Key | keyboard.KeyCode) -> bool:
        if self.key != "ctrl":
            return False
        return key in {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if not self._matches_key(key):
            return

        now = time.monotonic()
        with self._lock:
            if now - self._last_press_time <= self.interval_ms / 1000.0:
                self._last_press_time = 0.0
                self.on_trigger()
            else:
                self._last_press_time = now
