"""Harmony IL and CIL OpCode Inspector for Nuclear Option reverse engineering and transpiler development."""

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Dict, List, Optional, Tuple

from rich.table import Table
from rich import box

from nuclear_engine.config import config


@dataclass
class ILInstruction:
    offset: str  # e.g. "IL_0000"
    opcode: str  # e.g. "ldarg.0", "callvirt", "stfld"
    operand: str  # e.g. "instance void Aircraft::LockedByMissile(Missile)"
    comment: str = ""


@dataclass
class ILMethod:
    class_name: str
    method_name: str
    signature: str
    code_size: int
    instructions: List[ILInstruction]


class ILInspector:
    """Disassembles and inspects raw CIL instructions for Harmony Transpiler development."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (config.workspace_root / "no_code_analysis" / "il_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.dll_path = config.workspace_root / "lib" / "publicized" / "Assembly-CSharp.dll"
        if not self.dll_path.exists():
            self.dll_path = config.target_dll


    def get_class_il(self, class_name: str) -> str:
        """Fetch or decompile IL for the specified class, caching locally."""
        cache_file = self.cache_dir / f"{class_name}.il"
        if cache_file.exists() and cache_file.stat().st_size > 0:
            return cache_file.read_text(encoding="utf-8")

        if not config.ilspycmd_dll.exists():
            raise FileNotFoundError(f"ilspycmd not found at {config.ilspycmd_dll}")

        cmd = [
            "dotnet",
            "exec",
            str(config.ilspycmd_dll),
            "-il",
            "-t",
            class_name,
            str(self.dll_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0 or not result.stdout.strip():
            raise RuntimeError(f"Failed to disassemble class '{class_name}': {result.stderr}")

        cache_file.write_text(result.stdout, encoding="utf-8")
        return result.stdout

    def get_method_il(self, class_name: str, method_name: str) -> Optional[ILMethod]:
        """Extract instructions and signature for a specific method inside a class."""
        il_text = self.get_class_il(class_name)

        end_tag = f"// end of method {class_name}::{method_name}"
        end_idx = il_text.find(end_tag)
        if end_idx == -1:
            # Fallback: search for any class prefix if nested
            alt_tag = f"::{method_name}"
            end_idx = il_text.find(f"// end of method {class_name}/{method_name}")
            if end_idx == -1:
                matches = [m.start() for m in re.finditer(rf"// end of method [^\n]*::{re.escape(method_name)}\b", il_text)]
                if matches:
                    end_idx = matches[0]
                else:
                    return None

        start_idx = il_text.rfind(".method", 0, end_idx)
        if start_idx == -1:
            return None

        method_block = il_text[start_idx:end_idx]

        # Extract signature
        sig_match = re.search(rf"\b{re.escape(method_name)}\s*\(([^\)]*)\)", method_block)
        signature = f"{method_name}({sig_match.group(1).strip() if sig_match else ''})"

        code_size = 0
        size_match = re.search(r"Code size:\s*(\d+)", method_block)
        if size_match:
            code_size = int(size_match.group(1))

        instructions: List[ILInstruction] = []
        inst_pattern = re.compile(r"^\s*(IL_[0-9a-fA-F]{4}):\s+([a-zA-Z0-9\._]+)(?:\s+(.+))?$", re.MULTILINE)
        for m in inst_pattern.finditer(method_block):
            offset = m.group(1)
            opcode = m.group(2)
            operand = (m.group(3) or "").strip()
            instructions.append(ILInstruction(offset=offset, opcode=opcode, operand=operand))

        return ILMethod(
            class_name=class_name,
            method_name=method_name,
            signature=signature,
            code_size=code_size,
            instructions=instructions,
        )


    def generate_matcher_template(self, method: ILMethod, match_opcode: str = "callvirt") -> str:
        """Generate ready-to-use Harmony CodeMatcher C# boilerplate."""
        return f"""// Harmony Transpiler for {method.class_name}.{method.method_name}
[HarmonyPatch(typeof({method.class_name}), nameof({method.class_name}.{method.method_name}))]
public static class Transpiler_{method.class_name}_{method.method_name}
{{
    [HarmonyTranspiler]
    public static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {{
        var matcher = new CodeMatcher(instructions);

        // Search for target instruction
        matcher.MatchForward(false,
            new ElementMatch<CodeInstruction>(x => x.opcode == OpCodes.{match_opcode.capitalize()})
        );

        if (matcher.IsInvalid)
        {{
            Plugin.ModLogger.LogError("Failed to match target instruction in {method.class_name}.{method.method_name}");
            return instructions;
        }}

        // Insert custom hook or replacement:
        // matcher.InsertAndAdvance(new CodeInstruction(OpCodes.Call, AccessTools.Method(typeof(MyHooks), nameof(MyHooks.CustomLogic))));

        return matcher.InstructionEnumeration();
    }}
}}
"""

    def render_table(self, method: ILMethod) -> Table:
        table = Table(
            title=f"CIL Bytecode: {method.class_name}::{method.signature} ({len(method.instructions)} inst, {method.code_size} bytes)",
            box=box.ROUNDED,
            header_style="bold cyan",
        )
        table.add_column("Offset", style="dim", width=10)
        table.add_column("OpCode", style="bold yellow", width=16)
        table.add_column("Operand / Target Symbol", justify="left")

        for inst in method.instructions:
            style = "bold green" if "call" in inst.opcode else ("bold magenta" if "br" in inst.opcode else "white")
            table.add_row(inst.offset, f"[{style}]{inst.opcode}[/{style}]", inst.operand)

        return table
