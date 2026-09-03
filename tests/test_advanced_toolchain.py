"""Tests for advanced modder toolchain: Mission Validator, IL Inspector, Livery Scaffolder, and Code Auditor."""

from pathlib import Path
import pytest

from nuclear_engine.domain.mission import Mission, Faction, UnitInstance, Vector3, MissionSettings
from nuclear_engine.domain.mission_validator import MissionValidator, ValidationResult
from nuclear_engine.extractor.il_inspector import ILInspector
from nuclear_engine.builder.livery_scaffolder import LiveryScaffolder
from nuclear_engine.diagnostics.code_auditor import CodeAuditor
from nuclear_engine.mcp_server import NuclearMCPServer


def test_mission_validator_clean_and_corrupt():
    # Clean mission
    clean_mission = Mission(
        factions=[Faction(factionName="Boscali"), Faction(factionName="Primeva")],
        aircraft=[
            UnitInstance(
                UniqueName="Alpha1",
                faction="Boscali",
                playerControlled=True,
                globalPosition=Vector3(x=0, y=1500, z=0),
            )
        ],
        missionSettings=MissionSettings(playerMode="Singleplayer"),
    )
    result = MissionValidator.validate(clean_mission, "CleanTest")
    assert result.is_valid is True
    assert result.error_count == 0

    # Corrupted mission: unknown faction + underwater aircraft
    corrupted_mission = Mission(
        factions=[Faction(factionName="Boscali")],
        aircraft=[
            UnitInstance(
                UniqueName="SubmergedJet",
                faction="AlienInvaders",
                globalPosition=Vector3(x=0, y=-50, z=0),
            )
        ],
    )
    res_corrupt = MissionValidator.validate(corrupted_mission, "CorruptedTest")
    assert res_corrupt.is_valid is False
    assert res_corrupt.error_count >= 2
    codes = [i.code for i in res_corrupt.issues]
    assert "UNKNOWN_FACTION" in codes
    assert "AIRCRAFT_UNDERWATER" in codes

    table = MissionValidator.render_report(res_corrupt)
    assert table is not None


def test_il_inspector_disassembly():
    inspector = ILInspector()
    method = inspector.get_method_il("RadarWarning", "Start")
    assert method is not None
    assert method.class_name == "RadarWarning"
    assert method.method_name == "Start"
    assert len(method.instructions) > 5
    assert any("Aircraft" in inst.operand or "CombatHUD" in inst.operand for inst in method.instructions)

    matcher_code = inspector.generate_matcher_template(method)
    assert "CodeMatcher" in matcher_code
    assert "Transpiler" in matcher_code

    table = inspector.render_table(method)
    assert table is not None


def test_livery_scaffolding(tmp_path):
    target = tmp_path / "skins" / "Revoker" / "Viper"
    out_dir = LiveryScaffolder.scaffold(
        vehicle_name="Revoker",
        skin_name="Viper",
        author="AcePilot",
        target_dir=target,
    )
    assert out_dir.exists()
    assert (out_dir / "livery.json").exists()
    assert (out_dir / "albedo.png").exists()
    assert (out_dir / "normal.png").exists()
    assert (out_dir / "metallic.png").exists()
    assert (out_dir / "ViperLoader.cs").exists()

    content = (out_dir / "ViperLoader.cs").read_text(encoding="utf-8")
    assert "ViperLoader" in content
    assert "Aircraft" in content


def test_code_auditor_detection(tmp_path):
    # Test clean mod
    clean_result = CodeAuditor.audit_mod("NuclearTelemetry")
    assert clean_result.is_clean is True

    # Test bad code snippet
    bad_code = """
using UnityEngine;

public class StutterPlugin : MonoBehaviour
{
    void Update()
    {
        var targets = GameObject.Find("Target");
        GetComponent<Rigidbody>();
        System.IO.File.ReadAllText("data.txt");
    }
}
"""
    test_file = tmp_path / "StutterPlugin.cs"
    test_file.write_text(bad_code, encoding="utf-8")

    issues = CodeAuditor.audit_file(test_file)
    rules = [i.rule for i in issues]
    assert "SCENE_SEARCH_IN_HOT_LOOP" in rules
    assert "UNCACHED_GET_COMPONENT" in rules
    assert "BLOCKING_IO_IN_UPDATE" in rules

    res = CodeAuditor.audit_mod("StutterTest", target_dir=tmp_path)
    assert res.is_clean is False
    assert res.critical_count >= 2

    table = CodeAuditor.render_report(res)
    assert table is not None


def test_mcp_server_19_tools(tmp_path):
    server = NuclearMCPServer()
    tools = [t["name"] for t in server.get_tools()]
    assert len(tools) >= 19
    assert "validate_mission_scenario" in tools
    assert "get_method_il" in tools
    assert "create_aircraft_livery" in tools
    assert "audit_mod_performance" in tools

    # Test tool executions
    audit_res = server.call_tool("audit_mod_performance", {"mod_name": "NuclearTelemetry"})
    assert audit_res["is_clean"] is True

    il_res = server.call_tool("get_method_il", {
        "class_name": "RadarWarning",
        "method_name": "Start",
        "include_matcher": True,
    })
    assert "instructions" in il_res
    assert "matcher_template" in il_res

    livery_res = server.call_tool("create_aircraft_livery", {
        "vehicle": "Cricket",
        "skin_name": "DesertGhost",
    })
    assert livery_res["status"] == "created"
