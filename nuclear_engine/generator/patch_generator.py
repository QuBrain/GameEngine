"""Harmony Patch Generator for Nuclear Option BepInEx plugins.
Inspects real in-game C# method signatures and scaffolds 100% typed,
compilable Harmony prefix, postfix, and transpiler classes.
"""

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Dict, List, Optional, Tuple

from nuclear_engine.config import config
from nuclear_engine.extractor.code_indexer import CodeIndexer, ClassInfo, MethodInfo


@dataclass
class PatchTargetInfo:
    class_name: str
    method_name: str
    return_type: str
    parameters: str
    is_static: bool
    access: str
    source: str


class PatchGenerator:
    """Generates typed Harmony prefix, postfix, and transpiler patches from decompiled game code."""

    def __init__(self):
        self.indexer = CodeIndexer()

    def resolve_target(self, target: str) -> PatchTargetInfo:
        """Resolve a 'ClassName.MethodName' target string into metadata."""
        target = target.strip()
        if "." not in target:
            raise ValueError(f"Invalid patch target '{target}'. Expected format: 'ClassName.MethodName'")

        parts = target.split(".")
        class_name = parts[0]
        method_name = parts[1]

        # 1. Search in indexer cache
        cls_info = self.indexer.parse_class(class_name)
        if not cls_info and config.decompiled_dir.exists():
            # Try finding by rglob
            file_path = self.indexer.find_class_file(class_name)
            if file_path:
                cls_info = self.indexer.parse_class(class_name)

        if cls_info:
            for m in cls_info.methods:
                if m.name.lower() == method_name.lower():
                    return PatchTargetInfo(
                        class_name=cls_info.name,
                        method_name=m.name,
                        return_type=m.return_type,
                        parameters=m.parameters,
                        is_static=m.is_static,
                        access=m.access,
                        source="CodeIndexer",
                    )

        # 2. Try decompiling via ilspycmd if not found in cache
        ilspy_info = self._decompile_and_find_method(class_name, method_name)
        if ilspy_info:
            return ilspy_info

        # 3. Fallback: Generate intelligent default target
        return PatchTargetInfo(
            class_name=class_name,
            method_name=method_name,
            return_type="void",
            parameters="",
            is_static=False,
            access="public",
            source="Inferred",
        )

    def _decompile_and_find_method(self, class_name: str, method_name: str) -> Optional[PatchTargetInfo]:
        """Decompile class via ilspycmd to extract exact signature."""
        if not config.ilspycmd_dll.exists():
            return None

        target_dll = config.workspace_root / "lib" / "publicized" / "Assembly-CSharp.dll"
        if not target_dll.exists():
            target_dll = config.target_dll
        if not target_dll.exists():
            return None

        cmd = [
            "dotnet",
            "exec",
            str(config.ilspycmd_dll),
            "-t",
            class_name,
            str(target_dll),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode != 0:
                return None

            source = res.stdout
            method_pattern = re.compile(
                rf"^\s*(public|protected|private|internal)\s+(static\s+|virtual\s+|override\s+|async\s+)*([\w\<\>\[\],\s\?]+?)\s+({re.escape(method_name)})\s*\((.*?)\)",
                re.MULTILINE,
            )
            m = method_pattern.search(source)
            if m:
                access = m.group(1)
                modifiers = m.group(2) or ""
                return_type = m.group(3).strip()
                name = m.group(4)
                params = m.group(5).strip()
                return PatchTargetInfo(
                    class_name=class_name,
                    method_name=name,
                    return_type=return_type,
                    parameters=params,
                    is_static="static" in modifiers,
                    access=access,
                    source="ILSpyCmd",
                )
        except Exception:
            pass
        return None

    def generate_patch(
        self,
        target: str,
        patch_types: Optional[List[str]] = None,
        namespace: str = "NuclearOption.Mods.Patches",
    ) -> str:
        """Generate a complete C# Harmony patch file content.

        patch_types can contain: 'prefix', 'postfix', 'transpiler', or 'all'.
        """
        info = self.resolve_target(target)
        if not patch_types or "all" in patch_types:
            types_to_gen = ["prefix", "postfix", "transpiler"]
        else:
            types_to_gen = [t.lower() for t in patch_types]

        lines = [
            "using System;",
            "using System.Collections.Generic;",
            "using System.Reflection;",
            "using System.Reflection.Emit;",
            "using HarmonyLib;",
            "using UnityEngine;",
            "",
            f"namespace {namespace}",
            "{",
            "    /// <summary>",
            f"    /// Auto-generated Harmony patch for {info.class_name}.{info.method_name}",
            f"    /// Original signature: {info.access} {info.return_type} {info.method_name}({info.parameters})",
            f"    /// Source: {info.source}",
            "    /// </summary>",
            f'    [HarmonyPatch(typeof({info.class_name}), nameof({info.class_name}.{info.method_name}))]',
            f"    public static class {info.class_name}_{info.method_name}_Patch",
            "    {",
        ]

        # Parameter formatting for Prefix and Postfix
        prefix_params = []
        postfix_params = []

        if not info.is_static:
            prefix_params.append(f"{info.class_name} __instance")
            postfix_params.append(f"{info.class_name} __instance")

        # Parse original parameters
        if info.parameters:
            param_list = [p.strip() for p in info.parameters.split(",") if p.strip()]
            for p in param_list:
                # Remove default values if any, e.g. "float dt = 0f" -> "float dt"
                clean_p = p.split("=")[0].strip()
                prefix_params.append(clean_p)
                postfix_params.append(clean_p)

        is_non_void = info.return_type != "void" and info.return_type != ""

        if is_non_void:
            prefix_params.append(f"ref {info.return_type} __result")
            postfix_params.append(f"ref {info.return_type} __result")

        # 1. Prefix
        if "prefix" in types_to_gen:
            p_args = ", ".join(prefix_params)
            lines.extend([
                "        /// <summary>",
                f"        /// Executes BEFORE {info.class_name}.{info.method_name}.",
                "        /// Return true to allow original game code to execute.",
                "        /// Return false to suppress / skip original execution.",
                "        /// </summary>",
                "        [HarmonyPrefix]",
                f"        public static bool Prefix({p_args})",
                "        {",
                "            // TODO: Add your pre-execution logic here",
                "            return true; // continue to original method",
                "        }",
                "",
            ])

        # 2. Postfix
        if "postfix" in types_to_gen:
            post_args = ", ".join(postfix_params)
            lines.extend([
                "        /// <summary>",
                f"        /// Executes AFTER {info.class_name}.{info.method_name}.",
                "        /// Use this to inspect state, notify listeners, or modify return values.",
                "        /// </summary>",
                "        [HarmonyPostfix]",
                f"        public static void Postfix({post_args})",
                "        {",
                "            // TODO: Add your post-execution logic here",
                "        }",
                "",
            ])

        # 3. Transpiler
        if "transpiler" in types_to_gen:
            lines.extend([
                "        /// <summary>",
                f"        /// Modifies CIL byte-code instructions for {info.class_name}.{info.method_name} using Harmony CodeMatcher.",
                "        /// </summary>",
                "        [HarmonyTranspiler]",
                "        public static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)",
                "        {",
                "            var matcher = new CodeMatcher(instructions);",
                "            // Example CodeMatcher search & replace:",
                '            // matcher.MatchForward(false, new CodeMatch(OpCodes.Call, AccessTools.Method(typeof(Debug), "Log")));',
                "            return matcher.InstructionEnumeration();",
                "        }",
            ])

        lines.extend([
            "    }",
            "}",
            "",
        ])

        return "\n".join(lines)

    def save_patch(
        self,
        target: str,
        out_path: Optional[Path] = None,
        mod_name: Optional[str] = None,
        patch_types: Optional[List[str]] = None,
    ) -> Path:
        """Generate and write a patch file to disk."""
        info = self.resolve_target(target)
        code = self.generate_patch(target, patch_types=patch_types)

        if out_path is None:
            if mod_name:
                base_dir = config.workspace_root / "plugins" / mod_name / "Patches"
            else:
                base_dir = config.workspace_root / "plugins" / "Patches"
            base_dir.mkdir(parents=True, exist_ok=True)
            out_path = base_dir / f"{info.class_name}_{info.method_name}_Patch.cs"
        else:
            out_path.parent.mkdir(parents=True, exist_ok=True)

        out_path.write_text(code, encoding="utf-8")
        return out_path
