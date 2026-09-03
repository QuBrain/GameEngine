"""Tests for comprehensive modder lifecycle: Watcher, RPC Inspector, Scenario Factory, Audio Inspector, and Telemetry."""

from pathlib import Path
import pytest

from nuclear_engine.config import config
from nuclear_engine.builder.watcher import ModWatcher
from nuclear_engine.extractor.rpc_inspector import RPCInspector
from nuclear_engine.domain.mission_generator import MissionFactory
from nuclear_engine.extractor.audio_inspector import AudioInspector
from nuclear_engine.telemetry.server import TelemetryServer
from nuclear_engine.mcp_server import NuclearMCPServer


def test_mod_watcher_run_once():
    watcher = ModWatcher("NuclearTelemetry")
    success = watcher.run_once()
    assert success is True


def test_rpc_inspector_queries():
    inspector = RPCInspector()
    all_rpcs = inspector.scan_all()
    assert len(all_rpcs) > 50

    aircraft_rpcs = inspector.query(class_filter="Aircraft")
    assert len(aircraft_rpcs) > 10
    names = [r.name for r in aircraft_rpcs]
    assert any("CmdLaunchMissile" in n or "Cmd" in n for n in names)


def test_mission_factory_generation(tmp_path):
    mission_file = MissionFactory.save_to_mission_editor(
        mission_name="UnitTestingScenario",
        preset="dogfight",
        player_faction="Boscali",
        enemy_faction="Primeva",
        target_dir=tmp_path / "UnitTestingScenario",
    )
    assert mission_file.exists()
    assert mission_file.stat().st_size > 500


    mission = MissionFactory.create_mission("StrikeTest", preset="strike")
    assert len(mission.aircraft) >= 1
    assert len(mission.buildings) >= 1
    assert len(mission.objectives) >= 1


def test_audio_inspector():
    inspector = AudioInspector()
    events = inspector.scan_all()
    assert len(events) > 20

    voices = inspector.query(category="VoiceWarning")
    assert len(voices) >= 3


def test_telemetry_hud_render():
    server = TelemetryServer()
    server._update_state({
        "alt_asl": 4500.0,
        "alt_agl": 4200.0,
        "mach": 1.85,
        "heading": 315.0,
        "g": 5.4,
    })
    hud = server.render_hud()
    assert "COCKPIT TELEMETRY" in hud
    assert "4500.0" in hud
    assert "1.85" in hud


def test_mcp_server_new_lifecycle_tools():
    server = NuclearMCPServer()
    tools = [t["name"] for t in server.get_tools()]
    assert "get_network_rpcs" in tools
    assert "create_mission_scenario" in tools
    assert "get_audio_events" in tools

    rpcs = server.call_tool("get_network_rpcs", {"class_name": "Aircraft"})
    assert isinstance(rpcs, list)
    assert len(rpcs) > 0

    audio = server.call_tool("get_audio_events", {"category": "VoiceWarning"})
    assert isinstance(audio, list)
    assert len(audio) > 0
