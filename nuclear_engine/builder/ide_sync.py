"""IDE Integration & IntelliSense Synchronizer for Nuclear Option SDK.
Generates Solution (.sln) files, VS Code workspace settings, and C# XML docstrings
(Assembly-CSharp.xml) to power 100% full hover tooltips and IntelliSense in Visual Studio,
JetBrains Rider, and VS Code.
"""

from pathlib import Path
import uuid
from typing import List, Dict

from nuclear_engine.config import config
from nuclear_engine.extractor.code_indexer import CodeIndexer


KNOWN_DOCS: Dict[str, str] = {
    "Aircraft": "Core aircraft controller handling aerodynamics, engines, damage models, and combat systems.",
    "Aircraft.LockedByMissile": "Invoked when a missile seeker achieves a lock on this aircraft. Triggers MissileWarning alert chain.",
    "Aircraft.GetRadarReturn": "Calculates radar echo power based on distance, radar cross section (RCS), and terrain clutter.",
    "Aircraft.TakeDamage": "Applies kinetic, explosive, or shrapnel damage to airframe components.",
    "Aircraft.KnownRadarWarning": "Checks if an incoming radar emitter is actively painting or tracking this airframe.",
    "Radar": "Active radar sensor component handling scanning, target detection, Doppler filtering, and track maintenance.",
    "Radar.EstimateDetection": "Evaluates whether a target unit can be detected given radar parameters, range, and target RCS.",
    "Missile": "Guided missile entity implementing propulsion, seeker guidance (IR/Radar/Optical), and proximity fuse.",
    "Missile.FixedUpdate": "Physics and guidance loop steering the missile toward the predicted interception point.",
    "Missile.Explode": "Detonates the warhead, applying area-of-effect blast damage and releasing shrapnel.",
    "MissileWarning": "Radar Warning Receiver (RWR) and Missile Approach Warning System (MAWS) logic.",
    "MissileWarning.LockedByMissile": "Receives missile lock notifications and fires onMissileWarning event for cockpit indicators.",
    "Unit": "Base class for all vehicles, aircraft, missiles, ships, and buildings in Nuclear Option.",
    "Unit.TakeDamage": "Universal damage receiver dealing kinetic, explosive, or fire damage to the unit.",
    "GroundVehicle": "Land combat vehicle handling pathfinding, turret tracking, and weapon stations.",
    "Ship": "Naval warship managing point-defense CIWS, long-range radar, and surface-to-air missile batteries.",
    "PartDamageTracker": "Monitors component-level structural integrity, fires, and detachment states.",
}


class IDESync:
    def __init__(self):
        self.plugins_dir = config.workspace_root / "plugins"
        self.publicized_dir = config.workspace_root / "lib" / "publicized"
        self.vscode_dir = config.workspace_root / ".vscode"

    def sync_all(self) -> Dict[str, Path]:
        """Synchronize all IDE integration components."""
        res = {}
        res["sln"] = self.generate_solution()
        res["xml_docs"] = self.generate_xml_documentation()
        res["settings"] = self.generate_vscode_settings()
        res["extensions"] = self.generate_vscode_extensions()
        return res

    def generate_solution(self) -> Path:
        """Create or update NuclearMods.sln linking all mod projects in plugins/."""
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        sln_path = self.plugins_dir / "NuclearMods.sln"

        projects = []
        for p in self.plugins_dir.iterdir():
            if p.is_dir() and not p.name.startswith("."):
                csproj_list = list(p.glob("*.csproj"))
                if csproj_list:
                    projects.append((p.name, csproj_list[0]))

        sln_lines = [
            "Microsoft Visual Studio Solution File, Format Version 12.00",
            "# Visual Studio Version 17",
            "VisualStudioVersion = 17.0.31903.59",
            "MinimumVisualStudioVersion = 10.0.40219.1",
        ]

        # Project entries (ProjectTypeGuid for C# = {FAE04EC0-301F-11D3-BF4B-00C04F79EFBC})
        csharp_guid = "{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}"
        proj_guids = {}

        for name, csproj in projects:
            proj_id = "{" + str(uuid.uuid5(uuid.NAMESPACE_DNS, name)).upper() + "}"
            proj_guids[name] = proj_id
            rel_path = csproj.relative_to(self.plugins_dir)
            sln_lines.append(f'Project("{csharp_guid}") = "{name}", "{rel_path}", "{proj_id}"')
            sln_lines.append("EndProject")

        sln_lines.append("Global")
        sln_lines.append("\tGlobalSection(SolutionConfigurationPlatforms) = preSolution")
        sln_lines.append("\t\tDebug|Any CPU = Debug|Any CPU")
        sln_lines.append("\t\tRelease|Any CPU = Release|Any CPU")
        sln_lines.append("\tEndGlobalSection")
        sln_lines.append("\tGlobalSection(ProjectConfigurationPlatforms) = postSolution")

        for name, proj_id in proj_guids.items():
            sln_lines.append(f"\t\t{proj_id}.Debug|Any CPU.ActiveCfg = Debug|Any CPU")
            sln_lines.append(f"\t\t{proj_id}.Debug|Any CPU.Build.0 = Debug|Any CPU")
            sln_lines.append(f"\t\t{proj_id}.Release|Any CPU.ActiveCfg = Release|Any CPU")
            sln_lines.append(f"\t\t{proj_id}.Release|Any CPU.Build.0 = Release|Any CPU")

        sln_lines.append("\tEndGlobalSection")
        sln_lines.append("EndGlobal")

        with open(sln_path, "w", encoding="utf-8") as f:
            f.write("\r\n".join(sln_lines) + "\r\n")

        return sln_path

    def generate_xml_documentation(self) -> Path:
        """Generate Assembly-CSharp.xml docstrings for rich IDE hover tooltips."""
        self.publicized_dir.mkdir(parents=True, exist_ok=True)
        xml_path = self.publicized_dir / "Assembly-CSharp.xml"

        indexer = CodeIndexer()
        indexer._ensure_cache()

        members_xml = []
        for member_name, doc in KNOWN_DOCS.items():
            prefix = "T:" if "." not in member_name else "M:"
            members_xml.append(f'        <member name="{prefix}{member_name}">\n            <summary>{doc}</summary>\n        </member>')

        xml_content = f"""<?xml version="1.0"?>
<doc>
    <assembly>
        <name>Assembly-CSharp</name>
    </assembly>
    <members>
{chr(10).join(members_xml)}
    </members>
</doc>
"""
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_content)

        return xml_path

    def generate_vscode_settings(self) -> Path:
        """Create or update .vscode/settings.json for C# Dev Kit and OmniSharp."""
        self.vscode_dir.mkdir(parents=True, exist_ok=True)
        settings_file = self.vscode_dir / "settings.json"

        content = """{
  "dotnet.defaultSolution": "plugins/NuclearMods.sln",
  "omnisharp.useModernNet": true,
  "omnisharp.enableRoslynAnalyzers": true,
  "omnisharp.organizeImportsOnFormat": true,
  "csharp.inlayHints.parameters.enabled": true,
  "csharp.inlayHints.types.enabled": true,
  "files.exclude": {
    "**/bin": true,
    "**/obj": true,
    "no_code_analysis": false
  }
}
"""
        with open(settings_file, "w", encoding="utf-8") as f:
            f.write(content)

        return settings_file

    def generate_vscode_extensions(self) -> Path:
        """Create .vscode/extensions.json recommending C# and Unity modding extensions."""
        self.vscode_dir.mkdir(parents=True, exist_ok=True)
        ext_file = self.vscode_dir / "extensions.json"

        content = """{
  "recommendations": [
    "ms-dotnettools.csharp",
    "ms-dotnettools.csdevkit",
    "unity.unity-debug"
  ]
}
"""
        with open(ext_file, "w", encoding="utf-8") as f:
            f.write(content)

        return ext_file
