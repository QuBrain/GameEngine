"""Test suite for Mission parser and scanner."""

import pytest
from pathlib import Path
from nuclear_engine.config import config
from nuclear_engine.domain.mission import Mission, UnitInstance, Faction, Objective
from nuclear_engine.extractor.mission_scanner import MissionScanner
from nuclear_engine.tactical_advisor.mission_analyzer import MissionAnalyzer


def test_mission_model_validation():
    sample_data = {
        "JsonVersion": 1,
        "factions": [
            {"factionName": "Boscali", "startingBalance": 1000.0},
            {"factionName": "Primeva", "startingBalance": 1000.0},
        ],
        "aircraft": [
            {
                "UniqueName": "Fighter1",
                "type": "SA-42",
                "faction": "Boscali",
                "globalPosition": {"x": 100.0, "y": 2000.0, "z": 300.0},
            }
        ],
        "vehicles": [
            {
                "UniqueName": "SAM_1",
                "type": "SPAAG1",
                "faction": "Primeva",
            }
        ],
        "objectives": [
            {
                "UniqueName": "Obj1",
                "DisplayName": "Eliminate SAM",
                "Faction": "Boscali",
                "Type": "DestroyUnits",
                "targetUnits": ["SAM_1"],
            }
        ],
    }

    mission = Mission.model_validate(sample_data)
    assert len(mission.factions) == 2
    assert len(mission.aircraft) == 1
    assert mission.aircraft[0].type == "SA-42"
    assert len(mission.vehicles) == 1
    assert mission.total_unit_count == 2


def test_mission_analyzer():
    mission = Mission(
        factions=[Faction(factionName="Boscali"), Faction(factionName="Primeva")],
        aircraft=[
            UnitInstance(UniqueName="P1", type="FS-12", faction="Boscali"),
            UnitInstance(UniqueName="P2", type="FS-12", faction="Boscali"),
        ],
        vehicles=[
            UnitInstance(UniqueName="AD1", type="SPAAG1", faction="Primeva"),
            UnitInstance(UniqueName="AD2", type="Truck2-LADS", faction="Primeva"),
        ],
        objectives=[
            Objective(
                UniqueName="DefeatAirDefense",
                DisplayName="Destroy Air Defense",
                Faction="Boscali",
                Type="DestroyUnits",
                targetUnits=["AD1", "AD2"],
            )
        ],
    )

    analyzer = MissionAnalyzer()
    report = analyzer.analyze(mission, mission_name="Test Scenario")

    assert "Boscali" in report.factions
    assert "Primeva" in report.factions
    assert report.factions["Boscali"].fighter_count == 2
    assert report.factions["Primeva"].air_defense_count == 2
    assert len(report.objective_summaries) == 1


def test_scan_real_user_missions_if_present():
    scanner = MissionScanner()
    if config.mission_editor_dir.exists():
        summaries = scanner.scan_all_summaries()
        assert len(summaries) >= 1
        for s in summaries:
            assert s.mission is not None
            assert s.mission.JsonVersion >= 1
