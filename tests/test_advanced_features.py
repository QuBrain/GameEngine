"""Tests for advanced SDK features: Thunderstore Packer, Vehicle Inspector, Doc Generator, and Map Renderer."""

from pathlib import Path
import zipfile
import pytest

from nuclear_engine.config import config
from nuclear_engine.builder.packer import ModPacker, create_minimal_png
from nuclear_engine.domain.vehicle_inspector import VehicleInspector
from nuclear_engine.extractor.doc_generator import APIDocGenerator
from nuclear_engine.extractor.mission_scanner import MissionScanner
from nuclear_engine.tactical_advisor.map_renderer import TacticalMapRenderer
from nuclear_engine.mcp_server import NuclearMCPServer


def test_minimal_png_generator():
    png_bytes = create_minimal_png(256, 256)
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(png_bytes) > 100


def test_mod_packer_creates_valid_thunderstore_zip():
    packer = ModPacker()
    res = packer.pack("NuclearTelemetry")
    assert res.zip_path.exists()
    assert res.size_bytes > 0
    assert res.manifest["name"] == "NuclearTelemetry"
    assert "BepInEx-BepInExPack-5.4.2100" in res.manifest["dependencies"]

    # Verify zip entries
    with zipfile.ZipFile(res.zip_path, "r") as z:
        names = z.namelist()
        assert "manifest.json" in names
        assert "icon.png" in names
        assert "README.md" in names
        assert "NuclearTelemetry.dll" in names


def test_vehicle_inspector_queries():
    revoker = VehicleInspector.get_vehicle("revoker")
    assert revoker is not None
    assert revoker.designation == "FS-12"
    assert len(revoker.hardpoints) == 6
    assert revoker.top_speed_mach == 1.95

    darkreach = VehicleInspector.get_vehicle("SFB-81")
    assert darkreach is not None
    assert darkreach.rcs_m2 == 0.08
    assert len(darkreach.hardpoints) == 4

    all_v = VehicleInspector.list_all()
    assert len(all_v) >= 7


def test_api_doc_generator(tmp_path):
    gen = APIDocGenerator()
    gen.docs_dir = tmp_path / "docs" / "api"
    html_path = gen.generate()
    assert html_path.exists()
    assert html_path.stat().st_size > 10000

    json_path = tmp_path / "docs" / "api" / "api_reference.json"
    assert json_path.exists()



def test_tactical_map_renderer():
    scanner = MissionScanner()
    res = scanner.load_latest_mission_file("Boscali HQ")
    if res:
        path, mission = res
        renderer = TacticalMapRenderer(mission)
        ascii_map = renderer.render_ascii(width=40, height=15)
        assert "+---" in ascii_map
        assert "Legend:" in ascii_map

        svg = renderer.render_svg(width=400, height=300)
        assert "<svg" in svg
        assert "</svg>" in svg


def test_mcp_server_advanced_tools():
    server = NuclearMCPServer()
    tools = [t["name"] for t in server.get_tools()]
    assert "get_vehicle_specs" in tools
    assert "render_mission_map" in tools

    specs = server.call_tool("get_vehicle_specs", {"name": "revoker"})
    assert isinstance(specs, dict)
    assert specs["designation"] == "FS-12"
    assert len(specs["hardpoints"]) == 6
