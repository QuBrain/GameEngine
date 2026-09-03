"""Handles automated decompilation of Nuclear Option's Assembly-CSharp.dll using ILSpy."""

import io
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import List, Optional, Tuple
import urllib.request
import zipfile

from nuclear_engine.config import config


class DecompilerEngine:
    def __init__(self):
        self.target_dll = config.target_dll
        self.tools_dir = config.tools_dir
        self.decompiled_dir = config.decompiled_dir
        self.ilspycmd_exe = config.ilspycmd_exe

    def check_prerequisites(self) -> Tuple[bool, str]:
        if not self.target_dll.exists():
            return (
                False,
                f"Assembly-CSharp.dll not found at: {self.target_dll}. Please verify Nuclear Option installation.",
            )
        return True, "Target DLL located."

    def is_decompiled(self) -> bool:
        """Check if source directory already contains decompiled C# files."""
        return (
            self.decompiled_dir.exists()
            and any(self.decompiled_dir.rglob("*.cs"))
        )

    def setup_ilspycmd(self) -> Tuple[bool, str]:
        """Ensures ilspycmd is available either via dotnet exec ilspycmd.dll or downloaded locally."""
        # 1. Check if local net8 ilspycmd.dll exists
        if config.ilspycmd_dll.exists():
            return True, f"Found local ILSpy DLL at {config.ilspycmd_dll}"

        # 2. Check if local exe exists
        if self.ilspycmd_exe.exists():
            return True, f"Found local ILSpy CLI at {self.ilspycmd_exe}"

        # 3. Check if installed as global command
        try:
            res = subprocess.run(
                ["ilspycmd", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if res.returncode == 0:
                return True, "Using system global ilspycmd"
        except FileNotFoundError:
            pass

        # 4. Download ilspycmd 9.0 NuGet package directly
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        try:
            nuget_url = "https://www.nuget.org/api/v2/package/ilspycmd/9.0.0.7889"
            req = urllib.request.Request(
                nuget_url, headers={"User-Agent": "NuclearEngine-Setup"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                pkg_bytes = resp.read()

            out_dir = self.tools_dir / "ilspycmd"
            out_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(pkg_bytes)) as z:
                for member in z.namelist():
                    if member.startswith("tools/net8.0/any/"):
                        z.extract(member, out_dir)

            if config.ilspycmd_dll.exists():
                return True, f"Extracted ILSpy DLL to {config.ilspycmd_dll}"
            return False, "Failed to locate ilspycmd.dll in downloaded NuGet package."

        except Exception as e:
            return False, f"Failed to download/setup ilspycmd: {e}"

    def run_decompilation(self, force: bool = False) -> Tuple[bool, str]:
        """Decompile the game DLL into C# source files."""
        if not force and self.is_decompiled():
            count = len(list(self.decompiled_dir.rglob("*.cs")))
            return True, f"Already decompiled ({count} C# source files present in {self.decompiled_dir})."

        ok, msg = self.check_prerequisites()
        if not ok:
            return False, msg

        ok, msg = self.setup_ilspycmd()
        if not ok:
            return False, msg

        self.decompiled_dir.mkdir(parents=True, exist_ok=True)

        if config.ilspycmd_dll.exists():
            cmd = [
                "dotnet",
                "exec",
                str(config.ilspycmd_dll),
                "-p",
                "-o",
                str(self.decompiled_dir),
                str(self.target_dll),
            ]
        elif self.ilspycmd_exe.exists():
            cmd = [
                str(self.ilspycmd_exe),
                "-p",
                "-o",
                str(self.decompiled_dir),
                str(self.target_dll),
            ]
        else:
            cmd = [
                "ilspycmd",
                "-p",
                "-o",
                str(self.decompiled_dir),
                str(self.target_dll),
            ]

        try:
            res = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if res.returncode != 0:
                return False, f"Decompiler exited with error:\n{res.stderr}"

            count = len(list(self.decompiled_dir.rglob("*.cs")))
            return True, f"Successfully decompiled {count} C# source files."
        except Exception as e:
            return False, f"Failed executing decompiler: {e}"


    def search_classes(self, query: str) -> List[Path]:
        """Find C# class files containing the query in their name."""
        if not self.decompiled_dir.exists():
            return []
        q = query.lower()
        return [
            p for p in self.decompiled_dir.rglob("*.cs") if q in p.stem.lower()
        ]

    def search_source_text(
        self, query: str, max_results: int = 25
    ) -> List[Tuple[Path, int, str]]:
        """Perform full-text search across all decompiled source files."""
        if not self.decompiled_dir.exists():
            return []
        results = []
        q = query.lower()
        for p in self.decompiled_dir.rglob("*.cs"):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, 1):
                        if q in line.lower():
                            results.append((p, line_no, line.strip()))
                            if len(results) >= max_results:
                                return results
            except Exception:
                continue
        return results
