"""Scans, indexes, and loads Nuclear Option missions from the game directories."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from pydantic import ValidationError

from nuclear_engine.config import config
from nuclear_engine.domain.mission import Mission


class MissionSummary:
    def __init__(self, name: str, folder_path: Path, mission: Mission):
        self.name = name
        self.folder_path = folder_path
        self.mission = mission

    @property
    def aircraft_count(self) -> int:
        return len(self.mission.aircraft)

    @property
    def ground_count(self) -> int:
        return len(self.mission.vehicles)

    @property
    def ship_count(self) -> int:
        return len(self.mission.ships)

    @property
    def faction_names(self) -> List[str]:
        return [f.factionName for f in self.mission.factions]

    @property
    def objective_names(self) -> List[str]:
        return [o.DisplayName or o.UniqueName for o in self.mission.objectives]


class MissionScanner:
    def __init__(self, editor_dir: Optional[Path] = None):
        self.editor_dir = editor_dir or config.mission_editor_dir

    def list_missions(self) -> List[Tuple[str, Path]]:
        """List all mission directories found in the editor directory."""
        if not self.editor_dir.exists():
            return []

        missions = []
        for item in self.editor_dir.iterdir():
            if item.is_dir():
                missions.append((item.name, item))
        return sorted(missions, key=lambda x: x[0])

    def load_latest_mission_file(self, mission_name_or_dir: str) -> Optional[Tuple[Path, Mission]]:
        """Find the latest mission.json for a named mission or direct path."""
        target_dir: Optional[Path] = None

        candidate_path = Path(mission_name_or_dir)
        if candidate_path.exists():
            if candidate_path.is_file() and candidate_path.name == "mission.json":
                return candidate_path, self._parse_file(candidate_path)
            if candidate_path.is_dir():
                target_dir = candidate_path

        if not target_dir and self.editor_dir.exists():
            for d in self.editor_dir.iterdir():
                if d.is_dir() and mission_name_or_dir.lower() in d.name.lower():
                    target_dir = d
                    break

        if not target_dir:
            return None

        # Look for mission.json in target_dir or its autosave subfolders
        all_json = list(target_dir.rglob("mission.json"))
        if not all_json:
            return None

        # Sort by modification time (most recent first)
        all_json.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        latest = all_json[0]
        return latest, self._parse_file(latest)

    def scan_all_summaries(self) -> List[MissionSummary]:
        """Scan all missions in the editor dir and return summaries of the latest save for each."""
        summaries = []
        for name, mdir in self.list_missions():
            res = self.load_latest_mission_file(str(mdir))
            if res:
                path, mission = res
                summaries.append(MissionSummary(name=name, folder_path=path, mission=mission))
        return summaries

    def _parse_file(self, file_path: Path) -> Mission:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Mission.model_validate(data)
