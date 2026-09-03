"""Mission Validator and Scenario Linter for Nuclear Option mission.json files."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from rich.table import Table
from rich import box

from nuclear_engine.domain.mission import Mission, UnitInstance
from nuclear_engine.domain.vehicle_inspector import VEHICLE_DATABASE
from nuclear_engine.config import config



@dataclass
class ValidationIssue:
    severity: str  # "ERROR", "WARNING", "INFO"
    code: str
    message: str
    entity_name: str = ""
    fix_suggestion: str = ""


@dataclass
class ValidationResult:
    mission_name: str
    is_valid: bool
    issues: List[ValidationIssue]

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "WARNING")


class MissionValidator:
    """Validates mission scenarios for syntax errors, missing references, and game logic flaws."""

    @classmethod
    def validate_file(cls, file_path_or_name: str | Path) -> ValidationResult:
        path = Path(file_path_or_name)
        if not path.exists() or path.is_dir():
            # Check directly in MissionEditor directory
            target_dir = config.mission_editor_dir / str(file_path_or_name)
            if target_dir.exists():
                direct_file = target_dir / "mission.json"
                if direct_file.exists():
                    path = direct_file
                else:
                    sub_matches = sorted(target_dir.glob("**/mission.json"))
                    if sub_matches:
                        path = sub_matches[0]
            if not path.exists() or path.is_dir():
                matches = list(config.mission_editor_dir.glob(f"*{file_path_or_name}*/**/mission.json"))
                if matches:
                    path = matches[0]
                else:
                    raise FileNotFoundError(f"Mission file not found: {file_path_or_name}")


        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        mission = Mission.model_validate(data)
        mission_name = path.parent.name if path.name == "mission.json" else path.stem
        return cls.validate(mission, mission_name=mission_name)

    @classmethod
    def validate(cls, mission: Mission, mission_name: str = "Scenario") -> ValidationResult:
        issues: List[ValidationIssue] = []

        # 1. Factions validation
        declared_factions = {f.factionName.strip().lower(): f.factionName for f in mission.factions}
        if not declared_factions:
            issues.append(ValidationIssue(
                severity="ERROR",
                code="NO_FACTIONS",
                message="Mission has no declared factions in 'factions' array.",
                fix_suggestion="Add at least two factions (e.g. Boscali and Primeva)."
            ))

        # 2. Collect all unit unique names and verify uniqueness
        all_units: List[UnitInstance] = (
            mission.aircraft + mission.vehicles + mission.ships + mission.buildings
        )
        seen_names: Dict[str, str] = {}
        for u in all_units:
            if not u.UniqueName or not u.UniqueName.strip():
                issues.append(ValidationIssue(
                    severity="ERROR",
                    code="EMPTY_UNIT_NAME",
                    message="Unit has an empty or null UniqueName.",
                    fix_suggestion="Assign a distinct UniqueName to each unit."
                ))
                continue

            lower_name = u.UniqueName.lower()
            if lower_name in seen_names:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    code="DUPLICATE_UNIT_NAME",
                    message=f"Duplicate UniqueName '{u.UniqueName}' found.",
                    entity_name=u.UniqueName,
                    fix_suggestion="Ensure each unit has a globally unique identifier."
                ))
            else:
                seen_names[lower_name] = u.UniqueName

            # Check faction association
            if declared_factions and u.faction.strip().lower() not in declared_factions:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    code="UNKNOWN_FACTION",
                    message=f"Unit '{u.UniqueName}' assigned to undeclared faction '{u.faction}'.",
                    entity_name=u.UniqueName,
                    fix_suggestion=f"Assign unit to one of: {', '.join(declared_factions.values())}"
                ))

            # Elevation safety for aircraft
            if u in mission.aircraft and u.globalPosition:
                if u.globalPosition.y < 0:
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        code="AIRCRAFT_UNDERWATER",
                        message=f"Aircraft '{u.UniqueName}' spawned below sea level (Y = {u.globalPosition.y:.1f} m).",
                        entity_name=u.UniqueName,
                        fix_suggestion="Set globalPosition.y to at least 200 m for airborne spawns."
                    ))
                elif u.globalPosition.y < 10 and not u.playerControlled:
                    issues.append(ValidationIssue(
                        severity="WARNING",
                        code="AIRCRAFT_LOW_ALTITUDE",
                        message=f"Aircraft '{u.UniqueName}' spawned dangerously close to ground (Y = {u.globalPosition.y:.1f} m).",
                        entity_name=u.UniqueName,
                        fix_suggestion="Ensure spawn altitude is safe or unit is assigned to an airfield."
                    ))

        # 3. Player aircraft presence
        if mission.missionSettings.playerMode.lower() == "singleplayer":
            has_player = any(a.playerControlled for a in mission.aircraft)
            if not has_player and mission.aircraft:
                issues.append(ValidationIssue(
                    severity="WARNING",
                    code="NO_PLAYER_AIRCRAFT",
                    message="Singleplayer mission does not designate any playerControlled aircraft.",
                    fix_suggestion="Set 'playerControlled: true' on at least one player aircraft."
                ))

        # 4. Airbases validation
        for b in mission.airbases:
            name = b.get("DisplayName") or b.get("UniqueName", "Unknown Base")
            capture_range = b.get("CaptureRange", 0.0)
            if capture_range <= 0:
                issues.append(ValidationIssue(
                    severity="WARNING",
                    code="INVALID_CAPTURE_RANGE",
                    message=f"Airbase '{name}' has zero or negative CaptureRange ({capture_range}).",
                    entity_name=name,
                    fix_suggestion="Set CaptureRange to standard value (e.g. 2600.0 meters)."
                ))
            center = b.get("Center")
            if not center or ("x" not in center and "y" not in center):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    code="MISSING_AIRBASE_CENTER",
                    message=f"Airbase '{name}' missing valid Center position coordinates.",
                    entity_name=name,
                    fix_suggestion="Define 'Center': {'x': float, 'y': float, 'z': float}."
                ))

        # 5. Objectives targets validation
        for obj in mission.objectives:
            if not obj.targetUnits:
                issues.append(ValidationIssue(
                    severity="INFO",
                    code="OBJECTIVE_NO_TARGETS",
                    message=f"Objective '{obj.UniqueName}' has no targetUnits defined.",
                    entity_name=obj.UniqueName,
                    fix_suggestion="Define target units or ensure it represents an area/time trigger."
                ))
            else:
                for target in obj.targetUnits:
                    if target.lower() not in seen_names:
                        issues.append(ValidationIssue(
                            severity="ERROR",
                            code="OBJECTIVE_TARGET_NOT_FOUND",
                            message=f"Objective '{obj.UniqueName}' references non-existent unit '{target}'.",
                            entity_name=obj.UniqueName,
                            fix_suggestion=f"Update targetUnits with a valid unit UniqueName."
                        ))

        is_valid = sum(1 for i in issues if i.severity == "ERROR") == 0
        return ValidationResult(mission_name=mission_name, is_valid=is_valid, issues=issues)

    @classmethod
    def render_report(cls, result: ValidationResult) -> Table:
        table = Table(
            title=f"Scenario Validation: {result.mission_name} ({'PASS' if result.is_valid else 'FAIL'})",
            box=box.ROUNDED,
            header_style="bold cyan",
        )
        table.add_column("Severity", style="bold", width=10)
        table.add_column("Code", style="dim", width=22)
        table.add_column("Entity", width=18)
        table.add_column("Message and Remediation", justify="left")

        if not result.issues:
            table.add_row(
                "[green]PASS[/green]",
                "ALL_CHECKS_CLEAN",
                "Scenario",
                "[green]No structural, faction, elevation, or target reference issues detected.[/green]"
            )
            return table

        for issue in result.issues:
            if issue.severity == "ERROR":
                sev_style = "[red]ERROR[/red]"
            elif issue.severity == "WARNING":
                sev_style = "[yellow]WARNING[/yellow]"
            else:
                sev_style = "[blue]INFO[/blue]"

            msg = f"{issue.message}\n[dim]Fix: {issue.fix_suggestion}[/dim]" if issue.fix_suggestion else issue.message
            table.add_row(
                sev_style,
                issue.code,
                issue.entity_name or "-",
                msg,
            )

        return table
