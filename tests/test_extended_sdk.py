"""Tests for extended SDK capabilities: multi-assembly, patch verifier, log viewer, and config generator."""

from pathlib import Path
import pytest

from nuclear_engine.config import config
from nuclear_engine.extractor.code_indexer import CodeIndexer
from nuclear_engine.extractor.decompiler import DecompilerEngine
from nuclear_engine.builder.patch_verifier import PatchVerifier
from nuclear_engine.builder.config_generator import generate_config_file
from nuclear_engine.diagnostics.log_viewer import LogViewer
from nuclear_engine.mcp_server import NuclearMCPServer


def test_multi_assembly_indexing():
    """Verify that classes from subdirectories (like Mirage) are properly indexed."""
    indexer = CodeIndexer()
    info = indexer.parse_class("NetworkClient")
    if info:
        assert info.name == "NetworkClient"
        assert "Mirage" in str(info.path)


def test_patch_verifier_passes_valid_patch():
    verifier = PatchVerifier()
    results = verifier.verify_mod("NuclearTelemetry")
    assert len(results) >= 1
    patch = results[0]
    assert patch.target_class == "Aircraft"
    assert patch.target_method == "LockedByMissile"
    assert patch.status == "PASS"
    assert patch.is_valid is True


def test_patch_verifier_detects_invalid_patch(tmp_path):
    test_cs = tmp_path / "BadPatch.cs"
    test_cs.write_text(
        """using HarmonyLib;
[HarmonyPatch(typeof(NonExistentClass), "NonExistentMethod")]
public static class BadPatch {
    [HarmonyPrefix]
    public static void Prefix() {}
}""",
        encoding="utf-8",
    )
    verifier = PatchVerifier()
    results = verifier.verify_file(test_cs)
    assert len(results) == 1
    res = results[0]
    assert res.status == "FAIL"
    assert res.is_valid is False
    assert any("does not exist" in i.message for i in res.issues)


def test_log_viewer_reads_entries():
    viewer = LogViewer()
    entries = viewer.read_entries(source="bepinex", lines=20)
    assert isinstance(entries, list)
    if entries:
        assert entries[0].source == "BepInEx"
        assert entries[0].level in ("ERROR", "WARN", "INFO", "DEBUG")


def test_config_generator_creates_file(tmp_path, monkeypatch):
    # Set workspace_root to tmp_path
    plugin_dir = tmp_path / "plugins" / "TestConfigMod"
    plugin_dir.mkdir(parents=True)
    monkeypatch.setattr(config, "workspace_root", tmp_path)

    cfg_file = generate_config_file("TestConfigMod")
    assert cfg_file.exists()
    content = cfg_file.read_text(encoding="utf-8")
    assert "ConfigEntry<bool> Enabled" in content
    assert "ConfigEntry<KeyCode> ToggleKey" in content
    assert "ConfigEntry<float> Multiplier" in content


def test_mcp_server_extended_tools():
    server = NuclearMCPServer()
    tools = [t["name"] for t in server.get_tools()]
    assert "verify_mod_patches" in tools
    assert "get_game_logs" in tools

    # Call verify_mod_patches
    res = server.call_tool("verify_mod_patches", {"mod_name": "NuclearTelemetry"})
    assert isinstance(res, list)
    assert res[0]["status"] == "PASS"

    # Call get_game_logs
    logs = server.call_tool("get_game_logs", {"source": "bepinex", "lines": 5})
    assert isinstance(logs, list)


def test_ide_synchronization():
    from nuclear_engine.builder.ide_sync import IDESync
    sync = IDESync()
    res = sync.sync_all()
    assert res["sln"].exists()
    assert res["xml_docs"].exists()
    assert res["settings"].exists()
    assert res["extensions"].exists()

    # Check solution file contents
    sln_text = res["sln"].read_text(encoding="utf-8")
    assert "NuclearTelemetry" in sln_text

    # Check XML docstrings file
    xml_text = res["xml_docs"].read_text(encoding="utf-8")
    assert "<summary>" in xml_text
    assert "LockedByMissile" in xml_text

