"""Assembly Publicizer wrapper for Nuclear Option SDK.
Converts private/internal types, fields, and methods in Assembly-CSharp.dll to public,
enabling 100% full IntelliSense and autocomplete in C# IDEs (Visual Studio, Rider, VS Code).
"""

from pathlib import Path
import subprocess
import urllib.request
import zipfile
import io

from nuclear_engine.config import config


PUBLICIZER_NUGET_URL = "https://api.nuget.org/v3-flatcontainer/bepinex.assemblypublicizer.cli/0.4.3/bepinex.assemblypublicizer.cli.0.4.3.nupkg"


class AssemblyPublicizer:
    def __init__(self):
        self.tools_dir = config.tools_dir / "publicizer"
        self.cli_dll = self.tools_dir / "tools" / "net6.0" / "any" / "BepInEx.AssemblyPublicizer.Cli.dll"
        self.output_dir = config.workspace_root / "lib" / "publicized"


    def ensure_tool(self) -> Path:
        """Download and extract BepInEx.AssemblyPublicizer.Cli if not already present."""
        if self.cli_dll.exists():
            return self.cli_dll

        self.tools_dir.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(
            PUBLICIZER_NUGET_URL,
            headers={"User-Agent": "NuclearEngine-SDK/1.0"}
        )
        with urllib.request.urlopen(req) as resp:
            content = resp.read()

        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            for member in zf.namelist():
                if member.startswith("tools/net6.0/any/"):
                    zf.extract(member, self.tools_dir)

        if not self.cli_dll.exists():
            raise FileNotFoundError(f"Failed to extract publicizer CLI to {self.cli_dll}")
        return self.cli_dll

    def publicize(self, input_dll: Path | None = None, output_dll: Path | None = None) -> Path:
        """Publicize target assembly and return the output path."""
        tool_path = self.ensure_tool()

        if input_dll is None:
            input_dll = config.managed_dir / "Assembly-CSharp.dll"
            if not input_dll.exists():
                raise FileNotFoundError(f"Source game assembly not found at {input_dll}")

        if output_dll is None:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_dll = self.output_dir / input_dll.name

        cmd = [
            "dotnet",
            "exec",
            str(tool_path),
            str(input_dll),
            "-o",
            str(output_dll),
            "-f",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output_dll
