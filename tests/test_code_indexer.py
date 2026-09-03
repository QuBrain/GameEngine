"""Tests for C# CodeIndexer, API parsing, and token-saving method extractors."""

import pytest
from nuclear_engine.config import config
from nuclear_engine.extractor.code_indexer import CodeIndexer


@pytest.fixture
def indexer():
    return CodeIndexer()


def test_indexer_finds_aircraft(indexer):
    if not config.decompiled_dir.exists():
        pytest.skip("Source not decompiled")
    path = indexer.find_class_file("Aircraft")
    assert path is not None
    assert path.name == "Aircraft.cs"


def test_indexer_parses_aircraft_class(indexer):
    if not config.decompiled_dir.exists():
        pytest.skip("Source not decompiled")
    info = indexer.parse_class("Aircraft")
    assert info is not None
    assert info.name == "Aircraft"
    assert info.base_class == "Unit"
    assert "IRadarReturn" in info.interfaces
    assert len(info.methods) > 20


def test_indexer_extracts_method_body(indexer):
    if not config.decompiled_dir.exists():
        pytest.skip("Source not decompiled")
    res = indexer.get_method_source("Aircraft", "LockedByMissile")
    assert res is not None
    code, line_no = res
    assert "void LockedByMissile" in code
    assert "missileWarning" in code
    # Ensure it only extracts the method, not the whole file
    assert len(code.splitlines()) < 25


def test_indexer_generates_harmony_patch(indexer):
    if not config.decompiled_dir.exists():
        pytest.skip("Source not decompiled")
    patch = indexer.generate_harmony_patch("Aircraft", "LockedByMissile", patch_type="Prefix")
    assert patch is not None
    assert "[HarmonyPatch(typeof(Aircraft), nameof(Aircraft.LockedByMissile))]" in patch
    assert "Aircraft __instance" in patch
    assert "Missile missile" in patch


def test_indexer_finds_subclasses(indexer):
    if not config.decompiled_dir.exists():
        pytest.skip("Source not decompiled")
    subs = indexer.find_subclasses("Unit")
    names = [name for name, _ in subs]
    assert "Aircraft" in names
    assert "Missile" in names


def test_indexer_finds_callers(indexer):
    if not config.decompiled_dir.exists():
        pytest.skip("Source not decompiled")
    callers = indexer.find_callers("LockedByMissile")
    assert len(callers) >= 2
    classes = [c for c, _, _ in callers]
    assert "Aircraft" in classes or "Missile" in classes


def test_indexer_finds_structs_and_events(indexer):
    if not config.decompiled_dir.exists():
        pytest.skip("Source not decompiled")
    info = indexer.parse_class("MissileWarning")
    assert info is not None
    struct_names = [s.name for s in info.structs]
    assert "OnMissileWarning" in struct_names

    event_names = [e.name for e in info.events]
    assert "onMissileWarning" in event_names

