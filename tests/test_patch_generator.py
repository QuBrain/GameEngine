"""Automated tests for Harmony Patch Generator, IDE Decompilation config, and XML Docstrings."""

import pytest
from pathlib import Path

from nuclear_engine.generator.patch_generator import PatchGenerator, PatchTargetInfo
from nuclear_engine.mcp_server import NuclearMCPServer
from nuclear_engine.builder.ide_sync import IDESync


def test_resolve_target_from_indexer():
    generator = PatchGenerator()
    info = generator.resolve_target("Aircraft.LockedByMissile")
    assert info.class_name == "Aircraft"
    assert info.method_name == "LockedByMissile"
    assert "Missile" in info.parameters
    assert info.return_type == "void"


def test_resolve_target_inferred():
    generator = PatchGenerator()
    info = generator.resolve_target("NonExistentClass.CustomMethod")
    assert info.class_name == "NonExistentClass"
    assert info.method_name == "CustomMethod"
    assert info.source == "Inferred"


def test_generate_patch_code_structure():
    generator = PatchGenerator()
    code = generator.generate_patch("Aircraft.LockedByMissile")
    assert "[HarmonyPatch(typeof(Aircraft), nameof(Aircraft.LockedByMissile))]" in code
    assert "public static class Aircraft_LockedByMissile_Patch" in code
    assert "[HarmonyPrefix]" in code
    assert "public static bool Prefix(Aircraft __instance, Missile missile)" in code
    assert "[HarmonyPostfix]" in code
    assert "public static void Postfix(Aircraft __instance, Missile missile)" in code
    assert "[HarmonyTranspiler]" in code
    assert "public static IEnumerable<CodeInstruction> Transpiler" in code


def test_generate_patch_specific_type():
    generator = PatchGenerator()
    code = generator.generate_patch("Aircraft.LockedByMissile", patch_types=["prefix"])
    assert "[HarmonyPrefix]" in code
    assert "[HarmonyPostfix]" not in code
    assert "[HarmonyTranspiler]" not in code


def test_save_patch_to_disk(tmp_path: Path):
    generator = PatchGenerator()
    out_file = tmp_path / "Aircraft_LockedByMissile_Patch.cs"
    saved = generator.save_patch("Aircraft.LockedByMissile", out_path=out_file)
    assert saved.exists()
    content = saved.read_text(encoding="utf-8")
    assert "Aircraft_LockedByMissile_Patch" in content


def test_mcp_generate_harmony_patch():
    server = NuclearMCPServer()
    result = server.call_tool("generate_harmony_patch", {"target": "Aircraft.LockedByMissile"})
    assert "target" in result
    assert "code" in result
    assert "[HarmonyPatch(typeof(Aircraft)" in result["code"]


def test_ide_sync_decompilation_setting(tmp_path: Path):
    sync = IDESync()
    # Test that decompilation support is present in generate_vscode_settings
    settings_path = sync.generate_vscode_settings()
    content = settings_path.read_text(encoding="utf-8")
    assert '"omnisharp.enableDecompilationSupport": true' in content
    assert '"omnisharp.enableRoslynAnalyzers": true' in content


def test_ide_sync_xml_docs():
    sync = IDESync()
    xml_path = sync.generate_xml_documentation()
    assert xml_path.exists()
    content = xml_path.read_text(encoding="utf-8")
    assert '<member name="T:Aircraft">' in content
    assert '<member name="T:CombatHUD">' in content
    assert "gearDeployed" in content
