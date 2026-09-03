from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Optional


@dataclass
class EngineConfig:
    # Game Installation
    game_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "NUCLEAR_OPTION_DIR",
                r"C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option",
            )
        )
    )

    # LocalLow Save and Mission Directory
    user_data_dir: Path = field(
        default_factory=lambda: Path(
            os.path.expandvars(r"%LOCALAPPDATA%Low\Shockfront\NuclearOption")
        )
    )

    # Analysis & Decompilation Cache
    workspace_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )

    @property
    def managed_dir(self) -> Path:
        return self.game_dir / "NuclearOption_Data" / "Managed"

    @property
    def target_dll(self) -> Path:
        return self.managed_dir / "Assembly-CSharp.dll"

    @property
    def bepinex_dir(self) -> Path:
        return self.game_dir / "BepInEx"

    @property
    def mission_editor_dir(self) -> Path:
        return self.user_data_dir / "MissionEditor"

    @property
    def temp_missions_dir(self) -> Path:
        return self.user_data_dir / "TempMissions"

    @property
    def analysis_dir(self) -> Path:
        return self.workspace_root / "no_code_analysis"

    @property
    def tools_dir(self) -> Path:
        return self.analysis_dir / "tools"

    @property
    def decompiled_dir(self) -> Path:
        return self.analysis_dir / "source"

    @property
    def ilspycmd_exe(self) -> Path:
        return self.tools_dir / "ilspycmd.exe"

    @property
    def ilspycmd_dll(self) -> Path:
        return self.tools_dir / "ilspycmd" / "tools" / "net8.0" / "any" / "ilspycmd.dll"

    def is_game_installed(self) -> bool:
        return self.target_dll.exists()


    def has_user_missions(self) -> bool:
        return self.mission_editor_dir.exists()


# Global default configuration
config = EngineConfig()
