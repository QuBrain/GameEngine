"""High-performance C# AST and signature extractor for Nuclear Option decompiled codebase.
Saves thousands of LLM tokens by extracting concise APIs, method bodies, and Harmony hooks.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

from nuclear_engine.config import config


@dataclass
class MethodInfo:
    access: str
    is_static: bool
    is_virtual: bool
    is_override: bool
    return_type: str
    name: str
    parameters: str
    line_number: int
    class_name: str


@dataclass
class FieldInfo:
    access: str
    type_name: str
    name: str
    line_number: int


@dataclass
class ClassInfo:
    name: str
    path: Path
    base_class: Optional[str] = None
    interfaces: List[str] = field(default_factory=list)
    fields: List[FieldInfo] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    enums: List[str] = field(default_factory=list)


class CodeIndexer:
    def __init__(self, source_dir: Optional[Path] = None):
        self.source_dir = source_dir or config.decompiled_dir
        self._class_cache: Dict[str, Path] = {}

    def _ensure_cache(self):
        if not self._class_cache and self.source_dir.exists():
            for p in self.source_dir.rglob("*.cs"):
                self._class_cache[p.stem.lower()] = p

    def find_class_file(self, class_name: str) -> Optional[Path]:
        self._ensure_cache()
        return self._class_cache.get(class_name.lower())

    def parse_class(self, class_name: str) -> Optional[ClassInfo]:
        path = self.find_class_file(class_name)
        if not path:
            return None

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            return None

        info = ClassInfo(name=path.stem, path=path)

        # 1. Class definition & inheritance
        class_pattern = re.compile(
            r"(?:public|internal|private)\s+(?:abstract\s+|sealed\s+|static\s+)?class\s+(\w+)(?:\s*:\s*([\w\s,<>]+))?"
        )
        for line in lines[:50]:
            m = class_pattern.search(line)
            if m and m.group(1).lower() == class_name.lower():
                inheritance = m.group(2)
                if inheritance:
                    parts = [p.strip() for p in inheritance.split(",") if p.strip()]
                    if parts:
                        info.base_class = parts[0]
                        info.interfaces = parts[1:]
                break

        # 2. Extract methods
        method_pattern = re.compile(
            r"^\s*(public|protected|private|internal)\s+(static\s+|virtual\s+|override\s+|async\s+)*([\w\<\>\[\],\s\?]+?)\s+([A-Z]\w*)\s*\((.*?)\)",
            re.MULTILINE,
        )

        content = "".join(lines)
        for m in method_pattern.finditer(content):
            access = m.group(1)
            modifiers = m.group(2) or ""
            return_type = m.group(3).strip()
            name = m.group(4)
            params = m.group(5).strip()

            # Skip common noise like constructors or state machines
            if name in ("Check", "MoveNext", "SetStateMachine", path.stem):
                continue

            # Determine line number
            line_no = content[: m.start()].count("\n") + 1

            info.methods.append(
                MethodInfo(
                    access=access,
                    is_static="static" in modifiers,
                    is_virtual="virtual" in modifiers,
                    is_override="override" in modifiers,
                    return_type=return_type,
                    name=name,
                    parameters=params,
                    line_number=line_no,
                    class_name=path.stem,
                )
            )

        # 3. Extract public/protected fields
        field_pattern = re.compile(
            r"^\s*(public|protected)\s+(?:readonly\s+|const\s+|static\s+)?([\w\<\>\[\]\?]+)\s+(\w+)\s*;",
            re.MULTILINE,
        )
        for m in field_pattern.finditer(content):
            line_no = content[: m.start()].count("\n") + 1
            info.fields.append(
                FieldInfo(
                    access=m.group(1),
                    type_name=m.group(2),
                    name=m.group(3),
                    line_number=line_no,
                )
            )

        return info

    def get_method_source(self, class_name: str, method_name: str) -> Optional[Tuple[str, int]]:
        """Extract only the exact method body and line number, saving thousands of tokens."""
        path = self.find_class_file(class_name)
        if not path:
            return None

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        start_idx = -1
        signature_line = ""
        pattern = re.compile(rf"\b{method_name}\s*\(")

        for i, line in enumerate(lines):
            if pattern.search(line) and not line.strip().startswith("//"):
                start_idx = i
                signature_line = line
                break

        if start_idx == -1:
            return None

        # Find opening and matching closing brace
        brace_count = 0
        found_first_brace = False
        body_lines = []

        for i in range(start_idx, len(lines)):
            l = lines[i]
            body_lines.append(l)
            for ch in l:
                if ch == "{":
                    brace_count += 1
                    found_first_brace = True
                elif ch == "}":
                    brace_count -= 1
                    if found_first_brace and brace_count == 0:
                        return "".join(body_lines), start_idx + 1

        return "".join(body_lines), start_idx + 1

    def generate_harmony_patch(
        self, class_name: str, method_name: str, patch_type: str = "Prefix"
    ) -> Optional[str]:
        """Generate a copy-paste ready C# Harmony patch for BepInEx modding."""
        cls_info = self.parse_class(class_name)
        if not cls_info:
            return None

        matching = [m for m in cls_info.methods if m.name.lower() == method_name.lower()]
        if not matching:
            return None

        m = matching[0]

        # Parse parameters for C# patch signature
        param_args = []
        if not m.is_static:
            param_args.append(f"{cls_info.name} __instance")

        if m.parameters:
            # clean parameters
            for p in m.parameters.split(","):
                p_clean = p.strip()
                if p_clean:
                    param_args.append(p_clean)

        args_str = ", ".join(param_args)

        snippet = f"""using HarmonyLib;
using UnityEngine;

[HarmonyPatch(typeof({cls_info.name}), nameof({cls_info.name}.{m.name}))]
public static class Patch_{cls_info.name}_{m.name}
{{
    [Harmony{patch_type}]
    public static bool {patch_type}({args_str})
    {{
        // TODO: Your custom mod logic here
        // Return false to skip original game method, true to execute it.
        return true;
    }}
}}"""
        return snippet

    def search_similar_apis(self, keyword: str, max_results: int = 30) -> List[MethodInfo]:
        """Find methods matching a keyword across all classes in the game."""
        self._ensure_cache()
        matches = []
        q = keyword.lower()

        for class_lower, path in self._class_cache.items():
            if len(matches) >= max_results:
                break
            # Quick check if file contains query
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                if q not in content.lower():
                    continue
            except Exception:
                continue

            info = self.parse_class(path.stem)
            if info:
                for m in info.methods:
                    if q in m.name.lower():
                        matches.append(m)
                        if len(matches) >= max_results:
                            break
        return matches
