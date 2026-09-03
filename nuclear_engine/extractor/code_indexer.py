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
class StructInfo:
    name: str
    class_name: str
    fields: List[Tuple[str, str]]
    line_number: int


@dataclass
class EventInfo:
    name: str
    event_type: str
    class_name: str
    line_number: int


@dataclass
class EnumInfo:
    name: str
    values: List[str]
    class_name: str
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
    structs: List[StructInfo] = field(default_factory=list)
    events: List[EventInfo] = field(default_factory=list)
    enums: List[EnumInfo] = field(default_factory=list)



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

        # 4. Extract Events (e.g. public event Action<OnMissileWarning> onMissileWarning;)
        event_pattern = re.compile(
            r"^\s*(?:public|protected)\s+event\s+([\w\<\>,\s]+?)\s+(\w+)\s*;",
            re.MULTILINE,
        )
        for m in event_pattern.finditer(content):
            line_no = content[: m.start()].count("\n") + 1
            info.events.append(
                EventInfo(
                    name=m.group(2),
                    event_type=m.group(1).strip(),
                    class_name=path.stem,
                    line_number=line_no,
                )
            )

        # 5. Extract Structs (e.g. public struct OnMissileWarning { public Missile missile; })
        struct_pattern = re.compile(
            r"(?:public|protected|internal)\s+struct\s+(\w+)\s*\{([^}]*)\}",
            re.MULTILINE,
        )
        for m in struct_pattern.finditer(content):
            s_name = m.group(1)
            s_body = m.group(2)
            line_no = content[: m.start()].count("\n") + 1
            # Extract struct fields
            s_fields = []
            for f_match in re.finditer(r"public\s+([\w\<\>\[\]]+)\s+(\w+)\s*;", s_body):
                s_fields.append((f_match.group(1), f_match.group(2)))
            info.structs.append(
                StructInfo(
                    name=s_name,
                    class_name=path.stem,
                    fields=s_fields,
                    line_number=line_no,
                )
            )

        # 6. Extract Enums (e.g. public enum FlightMode : byte { Cruise, Combat })
        enum_pattern = re.compile(
            r"(?:(?:public|protected|internal|private)\s+)?enum\s+(\w+)(?:\s*:\s*\w+)?\s*\{([^}]*)\}",
            re.MULTILINE,
        )
        for m in enum_pattern.finditer(content):
            e_name = m.group(1)
            e_body = m.group(2)
            line_no = content[: m.start()].count("\n") + 1
            # Extract enum values
            vals = [
                v.split("=")[0].strip()
                for v in e_body.split(",")
                if v.strip() and not v.strip().startswith("//")
            ]
            info.enums.append(
                EnumInfo(
                    name=e_name,
                    values=vals,
                    class_name=path.stem,
                    line_number=line_no,
                )
            )


        return info

    def find_callers(self, target: str, limit: int = 30) -> List[Tuple[str, int, str]]:
        """Find references/callers of a method or field across the codebase."""
        self._ensure_cache()
        results = []
        target_pattern = re.compile(rf"\b{re.escape(target)}\b")

        for class_lower, path in self._class_cache.items():
            if len(results) >= limit:
                break
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, 1):
                        line_stripped = line.strip()
                        if target_pattern.search(line_stripped):
                            if not line_stripped.startswith("//"):
                                results.append((path.stem, line_no, line_stripped))
                                if len(results) >= limit:
                                    break
            except Exception:
                continue
        return results

    def find_subclasses(self, base_class_name: str) -> List[Tuple[str, Path]]:
        """Find all classes that inherit from a specific base class or interface."""
        self._ensure_cache()
        subclasses = []
        base_lower = base_class_name.lower()

        for class_lower, path in self._class_cache.items():
            info = self.parse_class(path.stem)
            if info:
                is_sub = False
                if info.base_class and info.base_class.lower() == base_lower:
                    is_sub = True
                elif any(i.lower() == base_lower for i in info.interfaces):
                    is_sub = True

                if is_sub:
                    subclasses.append((info.name, path))

        return sorted(subclasses, key=lambda x: x[0])


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
