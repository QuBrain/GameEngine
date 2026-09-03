"""Unified Log Viewer and Diagnostic Tool for Nuclear Option & BepInEx."""

from dataclasses import dataclass
from pathlib import Path
import time
from typing import List, Optional, Generator

from nuclear_engine.config import config


@dataclass
class LogEntry:
    source: str  # "BepInEx" or "Player"
    level: str   # "ERROR", "WARN", "INFO", "DEBUG"
    message: str
    raw: str


class LogViewer:
    def __init__(self):
        self.player_log = config.user_data_dir / "Player.log"
        self.bepinex_log = config.bepinex_dir / "LogOutput.log"

    def get_log_file(self, source: str = "bepinex") -> Optional[Path]:
        if source.lower() in ("bepinex", "mod", "mods"):
            return self.bepinex_log if self.bepinex_log.exists() else None
        elif source.lower() in ("player", "unity", "game"):
            return self.player_log if self.player_log.exists() else None
        return self.bepinex_log if self.bepinex_log.exists() else self.player_log

    def read_entries(
        self,
        source: str = "bepinex",
        lines: int = 50,
        errors_only: bool = False,
    ) -> List[LogEntry]:
        """Read the last N lines from the target log file and parse levels."""
        target_file = self.get_log_file(source)
        if not target_file or not target_file.exists():
            return []

        try:
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                all_lines = f.readlines()
        except Exception:
            return []

        selected_lines = all_lines[-lines:] if lines > 0 else all_lines
        entries: List[LogEntry] = []

        src_label = "BepInEx" if "bepinex" in str(target_file).lower() else "Player"

        for line in selected_lines:
            line_str = line.rstrip()
            if not line_str:
                continue

            lower = line_str.lower()
            if "error" in lower or "fatal" in lower or "exception" in lower:
                level = "ERROR"
            elif "warn" in lower:
                level = "WARN"
            elif "info" in lower or "message" in lower:
                level = "INFO"
            else:
                level = "DEBUG"

            if errors_only and level not in ("ERROR", "WARN"):
                continue

            entries.append(LogEntry(source=src_label, level=level, message=line_str, raw=line_str))

        return entries

    def follow(
        self,
        source: str = "bepinex",
        errors_only: bool = False,
    ) -> Generator[LogEntry, None, None]:
        """Stream new log entries as they are written in real time."""
        target_file = self.get_log_file(source)
        if not target_file or not target_file.exists():
            return

        src_label = "BepInEx" if "bepinex" in str(target_file).lower() else "Player"

        with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, 2)  # Go to end
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.2)
                    continue

                line_str = line.rstrip()
                lower = line_str.lower()
                if "error" in lower or "fatal" in lower or "exception" in lower:
                    level = "ERROR"
                elif "warn" in lower:
                    level = "WARN"
                elif "info" in lower or "message" in lower:
                    level = "INFO"
                else:
                    level = "DEBUG"

                if errors_only and level not in ("ERROR", "WARN"):
                    continue

                yield LogEntry(source=src_label, level=level, message=line_str, raw=line_str)
