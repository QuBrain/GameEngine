"""Audio & Sound Event Inspector for Nuclear Option."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import List, Dict, Any, Optional

from nuclear_engine.config import config


@dataclass
class AudioEvent:
    category: str  # "VoiceWarning", "Interface", "Effects", "Alert", "Weapon"
    class_name: str
    event_name: str
    mixer_group: str
    trigger_method: str
    line_number: int


class AudioInspector:
    """Scans and indexes game audio clips, cockpit voice cues, and sound manager hooks."""

    def __init__(self, source_dir: Optional[Path] = None):
        self.source_dir = source_dir or (config.workspace_root / "no_code_analysis" / "source")
        self._cache: Optional[List[AudioEvent]] = None

    def scan_all(self) -> List[AudioEvent]:
        if self._cache is not None:
            return self._cache

        events: List[AudioEvent] = []
        if not self.source_dir.exists():
            return events

        # Regex patterns
        play_regex = re.compile(r"SoundManager\.(PlayInterfaceOneShot|PlayRadarWarningOneShot)\s*\((.*?)\)")
        mixer_regex = re.compile(r"outputAudioMixerGroup\s*=\s*SoundManager\.i\.(\w+)")
        voice_field_regex = re.compile(r"AudioClip\s+(\w*(?:Voice|Warning|Alert|Sound|Clip)\w*)")

        for file_path in self.source_dir.rglob("*.cs"):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            lines = content.splitlines()
            current_class = file_path.stem
            current_method = "Unknown"

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Track method name
                if "(" in stripped and ")" in stripped and any(stripped.startswith(k) for k in ("public", "private", "protected", "internal")):
                    parts = stripped.split("(")[0].split()
                    if len(parts) >= 2:
                        current_method = parts[-1]

                # Look for SoundManager playback
                play_match = play_regex.search(stripped)
                if play_match:
                    clip_arg = play_match.group(2).strip()
                    cat = "VoiceWarning" if "voice" in clip_arg.lower() or "warning" in clip_arg.lower() else "Interface"
                    events.append(AudioEvent(
                        category=cat,
                        class_name=current_class,
                        event_name=clip_arg,
                        mixer_group="InterfaceMixer",
                        trigger_method=current_method,
                        line_number=i + 1,
                    ))

                # Look for AudioMixer assignments
                mixer_match = mixer_regex.search(stripped)
                if mixer_match:
                    mixer = mixer_match.group(1)
                    cat = "Alert" if "alert" in mixer.lower() else "Effects"
                    events.append(AudioEvent(
                        category=cat,
                        class_name=current_class,
                        event_name=f"AudioSource ({mixer})",
                        mixer_group=mixer,
                        trigger_method=current_method,
                        line_number=i + 1,
                    ))

        self._cache = events
        return events

    def query(
        self,
        category: Optional[str] = None,
        class_filter: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[AudioEvent]:
        events = self.scan_all()
        results: List[AudioEvent] = []

        for e in events:
            if category and category.lower() != e.category.lower():
                continue
            if class_filter and class_filter.lower() not in e.class_name.lower():
                continue
            if search_query:
                q = search_query.lower()
                if q not in e.event_name.lower() and q not in e.class_name.lower() and q not in e.mixer_group.lower():
                    continue
            results.append(e)

        return results
