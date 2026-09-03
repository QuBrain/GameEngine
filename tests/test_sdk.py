"""Automated tests for Nuclear Option Modding SDK components."""

import json
from pathlib import Path
import pytest

from nuclear_engine.config import config
from nuclear_engine.mcp_server import NuclearMCPServer
from nuclear_engine.builder.mod_builder import ModPipeline
from nuclear_engine.extractor.publicizer import AssemblyPublicizer


def test_mcp_server_lists_tools():
    server = NuclearMCPServer()
    tools = server.get_tools()
    assert len(tools) >= 8
    tool_names = [t["name"] for t in tools]
    assert "get_class_api" in tool_names
    assert "get_method_code" in tool_names
    assert "generate_harmony_hook" in tool_names
    assert "find_callers" in tool_names
    assert "find_subclasses" in tool_names
    assert "find_enums" in tool_names


def test_mcp_server_executes_tools():
    server = NuclearMCPServer()

    # 1. Test get_method_code
    res = server.call_tool("get_method_code", {"class_name": "Aircraft", "method_name": "LockedByMissile"})
    assert isinstance(res, dict)
    assert "source" in res
    assert "LockedByMissile" in res["source"]

    # 2. Test find_subclasses
    subs = server.call_tool("find_subclasses", {"base_class": "Unit"})
    assert isinstance(subs, list)
    names = [s["subclass"] for s in subs]
    assert "Aircraft" in names

    # 3. Test generate_harmony_hook
    hook = server.call_tool("generate_harmony_hook", {"class_name": "Aircraft", "method_name": "LockedByMissile", "patch_type": "Prefix"})
    assert "patch" in hook
    assert "[HarmonyPatch(typeof(Aircraft)" in hook["patch"]


def test_assembly_publicizer_generates_dll():
    if not config.managed_dir.exists():
        pytest.skip("Game not installed")

    pub = AssemblyPublicizer()
    out_dll = pub.publicize()
    assert out_dll.exists()
    assert out_dll.stat().st_size > 1_000_000


def test_mod_builder_compiles_plugin():
    if not config.managed_dir.exists():
        pytest.skip("Game not installed")

    pipeline = ModPipeline()
    dll = pipeline.build("NuclearTelemetry")
    assert dll.exists()
    assert dll.stat().st_size > 1000
