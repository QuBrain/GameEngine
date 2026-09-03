"""Thunderstore and distribution packaging utility for Nuclear Option BepInEx mods."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct
from typing import List, Optional, Dict, Any
import zipfile
import zlib

from nuclear_engine.config import config
from nuclear_engine.builder.mod_builder import ModPipeline
from nuclear_engine.builder.patch_verifier import PatchVerifier


def create_minimal_png(width: int = 256, height: int = 256) -> bytes:
    """Generate a clean dark-grey 256x256 PNG image in pure Python (no PIL dependency required)."""
    header = b"\x89PNG\r\n\x1a\n"
    # IHDR chunk: width (4B), height (4B), bit_depth (1B=8), color_type (1B=6 RGBA), comp, filter, interlace
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data))
    ihdr_chunk = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + ihdr_crc

    # Raw RGBA scanlines (filter byte 0 per line)
    # Background color: Dark tactical slate (30, 35, 45, 255)
    row_bytes = b"\x00" + (bytes([30, 35, 45, 255]) * width)
    raw_data = row_bytes * height
    compressed_data = zlib.compress(raw_data)
    idat_crc = struct.pack(">I", zlib.crc32(b"IDAT" + compressed_data))
    idat_chunk = struct.pack(">I", len(compressed_data)) + b"IDAT" + compressed_data + idat_crc

    iend_chunk = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND"))

    return header + ihdr_chunk + idat_chunk + iend_chunk


@dataclass
class PackResult:
    mod_name: str
    version: str
    zip_path: Path
    file_count: int
    size_bytes: int
    manifest: Dict[str, Any]


class ModPacker:
    def __init__(self):
        self.builder = ModPipeline()
        self.verifier = PatchVerifier()
        self.dist_dir = config.workspace_root / "dist"

    def pack(
        self,
        mod_name: str,
        version: Optional[str] = None,
        author: str = "Community",
        description: Optional[str] = None,
        website_url: str = "",
        dependencies: Optional[List[str]] = None,
        skip_build: bool = False,
    ) -> PackResult:
        """Build, verify, and package a mod into a Thunderstore-compatible zip archive."""
        mod_dir = config.workspace_root / "plugins" / mod_name
        if not mod_dir.exists():
            raise FileNotFoundError(f"Mod directory not found: {mod_dir}")

        # 1. Build the mod in Release configuration
        if not skip_build:
            dll_path = self.builder.build(mod_name, configuration="Release")
        else:
            dll_path = mod_dir / "bin" / "Release" / f"{mod_name}.dll"
            if not dll_path.exists():
                dll_path = self.builder.build(mod_name, configuration="Release")

        # 2. Verify Harmony patches
        patch_results = self.verifier.verify_mod(mod_name)
        fatal_patches = [r for r in patch_results if not r.is_valid]
        if fatal_patches:
            err_msg = "\n".join(f"- {r.target_class}.{r.target_method}: {r.issues[0].message}" for r in fatal_patches)
            raise ValueError(f"Cannot package mod '{mod_name}' due to invalid Harmony patches:\n{err_msg}")

        # 3. Detect or extract version & description from .csproj or Plugin.cs
        detected_version = version or self._detect_version(mod_dir) or "1.0.0"
        detected_desc = description or self._detect_description(mod_dir) or f"{mod_name} mod for Nuclear Option"

        # 4. Prepare staging and manifest
        self.dist_dir.mkdir(parents=True, exist_ok=True)
        manifest_data = {
            "name": mod_name,
            "version_number": detected_version,
            "website_url": website_url,
            "description": detected_desc,
            "dependencies": dependencies or ["BepInEx-BepInExPack-5.4.2100"],
        }

        # 5. Icon handling
        icon_path = mod_dir / "icon.png"
        if icon_path.exists():
            icon_bytes = icon_path.read_bytes()
        else:
            icon_bytes = create_minimal_png(256, 256)

        # 6. Readme handling
        readme_path = mod_dir / "README.md"
        if readme_path.exists():
            readme_text = readme_path.read_text(encoding="utf-8")
        else:
            readme_text = f"# {mod_name}\n\n{detected_desc}\n\n## Installation\nInstall via Thunderstore Mod Manager or extract into `BepInEx/plugins/`.\n"

        # 7. Create ZIP archive
        zip_filename = f"{mod_name}_{detected_version}.zip"
        zip_path = self.dist_dir / zip_filename

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            # Thunderstore root requirements: manifest.json, icon.png, README.md, <ModName>.dll
            z.writestr("manifest.json", json.dumps(manifest_data, indent=2))
            z.writestr("icon.png", icon_bytes)
            z.writestr("README.md", readme_text)
            z.write(dll_path, arcname=f"{mod_name}.dll")

            # Include ModConfig.cs if present as documentation
            cfg_file = mod_dir / "ModConfig.cs"
            if cfg_file.exists():
                z.write(cfg_file, arcname="ModConfig.cs")

        return PackResult(
            mod_name=mod_name,
            version=detected_version,
            zip_path=zip_path,
            file_count=4 if not (mod_dir / "ModConfig.cs").exists() else 5,
            size_bytes=zip_path.stat().st_size,
            manifest=manifest_data,
        )

    def _detect_version(self, mod_dir: Path) -> Optional[str]:
        # Search in .csproj
        for csproj in mod_dir.glob("*.csproj"):
            txt = csproj.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"<Version>([\d\.]+)</Version>", txt)
            if m:
                return m.group(1)
        # Search in Plugin.cs
        for cs in mod_dir.glob("*.cs"):
            txt = cs.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r'\[BepInPlugin\([^,]+,[^,]+,\s*"([\d\.]+)"\)\]', txt)
            if m:
                return m.group(1)
        return None

    def _detect_description(self, mod_dir: Path) -> Optional[str]:
        for csproj in mod_dir.glob("*.csproj"):
            txt = csproj.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"<Description>(.+?)</Description>", txt)
            if m:
                return m.group(1)
        return None
