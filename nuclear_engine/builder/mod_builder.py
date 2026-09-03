"""Mod build, deploy, and launch pipeline for Nuclear Option SDK."""

from pathlib import Path
import shutil
import subprocess
import os
import sys

from nuclear_engine.config import config


class ModPipeline:
    def __init__(self):
        self.plugins_dir = config.workspace_root / "plugins"
        self.game_plugins_dir = config.bepinex_dir / "plugins"

    def get_mod_dir(self, mod_name: str) -> Path:
        mod_dir = self.plugins_dir / mod_name
        if not mod_dir.exists():
            raise FileNotFoundError(f"Mod '{mod_name}' not found in {self.plugins_dir}")
        return mod_dir

    def build(self, mod_name: str, configuration: str = "Release") -> Path:
        """Compile mod C# project into DLL using Roslyn compiler with publicized game assembly."""
        mod_dir = self.get_mod_dir(mod_name)
        cs_files = list(mod_dir.glob("**/*.cs"))
        if not cs_files:
            raise FileNotFoundError(f"No .cs files found in {mod_dir}")

        out_bin_dir = mod_dir / "bin" / configuration
        out_bin_dir.mkdir(parents=True, exist_ok=True)
        target_dll = out_bin_dir / f"{mod_name}.dll"

        # Ensure publicized Assembly-CSharp exists
        publicized_dll = config.workspace_root / "lib" / "publicized" / "Assembly-CSharp.dll"
        if not publicized_dll.exists():
            from nuclear_engine.extractor.publicizer import AssemblyPublicizer
            AssemblyPublicizer().publicize()

        csc_path = Path(r"C:\Program Files\dotnet\sdk\9.0.313\Roslyn\bincore\csc.dll")
        if not csc_path.exists():
            sdk_base = Path(r"C:\Program Files\dotnet\sdk")
            found = list(sdk_base.rglob("csc.dll"))
            if found:
                csc_path = found[0]
            else:
                raise FileNotFoundError("Roslyn csc compiler not found in dotnet SDK.")

        # Reference assemblies from game and publicized cache
        mscorlib = config.managed_dir / "mscorlib.dll"
        netstandard = config.managed_dir / "netstandard.dll"
        system_dll = config.managed_dir / "System.dll"
        unity_engine = config.managed_dir / "UnityEngine.dll"
        unity_core = config.managed_dir / "UnityEngine.CoreModule.dll"
        bepinex_dll = config.bepinex_dir / "core" / "BepInEx.dll"
        harmony_dll = config.bepinex_dir / "core" / "0Harmony.dll"

        core_refs = [
            f"-r:{mscorlib}",
            f"-r:{netstandard}",
            f"-r:{system_dll}",
            f"-r:{unity_engine}",
            f"-r:{unity_core}",
            f"-r:{publicized_dll}",
            f"-r:{bepinex_dll}",
            f"-r:{harmony_dll}",
        ]

        # Also include all other managed DLLs so mods can reference anything
        for dll in config.managed_dir.glob("*.dll"):
            ref_str = f"-r:{dll}"
            if dll.name != "Assembly-CSharp.dll" and ref_str not in core_refs:
                core_refs.append(ref_str)

        csc_cmd = [
            "dotnet",
            "exec",
            str(csc_path),
            "-target:library",
            f"-out:{target_dll}",
            "-nostdlib+",
            "-optimize+",
            *core_refs,
            *[str(f) for f in cs_files],
        ]

        res = subprocess.run(csc_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"C# compilation failed:\n{res.stderr or res.stdout}")

        return target_dll


    def deploy(self, mod_name: str, configuration: str = "Release") -> Path:
        """Build and deploy mod DLL directly into Nuclear Option's BepInEx/plugins folder."""
        dll_path = self.build(mod_name, configuration=configuration)

        self.game_plugins_dir.mkdir(parents=True, exist_ok=True)
        dest_path = self.game_plugins_dir / dll_path.name
        shutil.copy2(dll_path, dest_path)
        return dest_path

    @staticmethod
    def launch_game() -> None:
        """Launch Nuclear Option via Steam or executable."""
        if sys.platform == "win32":
            os.system("start steam://rungameid/2158680")
        else:
            exe = config.game_dir / "NuclearOption.exe"
            if exe.exists():
                subprocess.Popen([str(exe)])
