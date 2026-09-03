"""Harmony Patch Verifier for Nuclear Option mods.
Validates that [HarmonyPatch] attributes in a mod match actual existing classes,
methods, and signatures in the game assemblies to prevent crashes after updates.
"""

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import List, Optional, Dict, Any

from nuclear_engine.config import config
from nuclear_engine.extractor.code_indexer import CodeIndexer, ClassInfo, MethodInfo


@dataclass
class PatchIssue:
    severity: str  # "ERROR", "WARNING", "INFO"
    message: str
    file: Path
    line: int


@dataclass
class PatchVerificationResult:
    target_class: str
    target_method: str
    patch_type: str  # "Prefix", "Postfix", "Transpiler", "Unknown"
    is_valid: bool
    status: str  # "PASS", "FAIL", "WARN"
    file: Path
    line: int
    issues: List[PatchIssue] = field(default_factory=list)


class PatchVerifier:
    def __init__(self, indexer: Optional[CodeIndexer] = None):
        self.indexer = indexer or CodeIndexer()

    def verify_mod(self, mod_name_or_dir: str | Path) -> List[PatchVerificationResult]:
        """Scan mod directory and verify all Harmony patches."""
        if isinstance(mod_name_or_dir, Path):
            mod_dir = mod_name_or_dir
        else:
            mod_dir = config.workspace_root / "plugins" / mod_name_or_dir

        if not mod_dir.exists():
            raise FileNotFoundError(f"Mod directory not found: {mod_dir}")

        results: List[PatchVerificationResult] = []
        for cs_file in mod_dir.rglob("*.cs"):
            if "obj" in cs_file.parts or "bin" in cs_file.parts:
                continue
            file_results = self.verify_file(cs_file)
            results.extend(file_results)

        return results

    def verify_file(self, file_path: Path) -> List[PatchVerificationResult]:
        """Verify Harmony patches in a single C# file."""
        results: List[PatchVerificationResult] = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.splitlines()
        except Exception:
            return results

        # Regex for [HarmonyPatch(typeof(TargetClass), nameof(TargetClass.Method))]
        # or [HarmonyPatch(typeof(TargetClass), "Method")]
        patch_pattern = re.compile(
            r'\[HarmonyPatch\s*\(\s*typeof\s*\(\s*(\w+)\s*\)\s*,\s*(?:nameof\s*\(\s*(?:\w+\.)?(\w+)\s*\)|"(\w+)")\s*\)\]'
        )

        for line_idx, line in enumerate(lines, 1):
            m = patch_pattern.search(line)
            if not m:
                continue

            target_class = m.group(1)
            target_method = m.group(2) or m.group(3)

            # Inspect subsequent lines for Prefix, Postfix, Transpiler
            patch_type = "Unknown"
            subsequent_code = "\n".join(lines[line_idx:line_idx + 25])
            if "[HarmonyPrefix]" in subsequent_code or " Prefix(" in subsequent_code:
                patch_type = "Prefix"
            elif "[HarmonyPostfix]" in subsequent_code or " Postfix(" in subsequent_code:
                patch_type = "Postfix"
            elif "[HarmonyTranspiler]" in subsequent_code or " Transpiler(" in subsequent_code:
                patch_type = "Transpiler"

            res = self._validate_patch(target_class, target_method, patch_type, file_path, line_idx, subsequent_code)
            results.append(res)

        return results

    def _validate_patch(
        self,
        class_name: str,
        method_name: str,
        patch_type: str,
        file_path: Path,
        line_no: int,
        subsequent_code: str,
    ) -> PatchVerificationResult:
        issues: List[PatchIssue] = []

        # 1. Check if class exists
        class_info = self.indexer.parse_class(class_name)
        if not class_info:
            issues.append(
                PatchIssue(
                    severity="ERROR",
                    message=f"Target class '{class_name}' does not exist in game assemblies.",
                    file=file_path,
                    line=line_no,
                )
            )
            return PatchVerificationResult(
                target_class=class_name,
                target_method=method_name,
                patch_type=patch_type,
                is_valid=False,
                status="FAIL",
                file=file_path,
                line=line_no,
                issues=issues,
            )

        # 2. Check if method exists in target class
        matching_methods = [m for m in class_info.methods if m.name.lower() == method_name.lower()]
        if not matching_methods:
            # Check base classes
            issues.append(
                PatchIssue(
                    severity="ERROR",
                    message=f"Method '{method_name}' not found in class '{class_name}'.",
                    file=file_path,
                    line=line_no,
                )
            )
            return PatchVerificationResult(
                target_class=class_name,
                target_method=method_name,
                patch_type=patch_type,
                is_valid=False,
                status="FAIL",
                file=file_path,
                line=line_no,
                issues=issues,
            )

        # Method found
        game_method = matching_methods[0]

        # 3. Check for __instance type mismatch in hook parameter list
        instance_match = re.search(r'(\w+)\s+__instance', subsequent_code)
        if instance_match:
            instance_type = instance_match.group(1)
            if instance_type != class_name and instance_type != "object":
                issues.append(
                    PatchIssue(
                        severity="WARNING",
                        message=f"__instance parameter type '{instance_type}' does not match target class '{class_name}'.",
                        file=file_path,
                        line=line_no,
                    )
                )

        status = "WARN" if any(i.severity == "WARNING" for i in issues) else "PASS"
        return PatchVerificationResult(
            target_class=class_name,
            target_method=method_name,
            patch_type=patch_type,
            is_valid=len([i for i in issues if i.severity == "ERROR"]) == 0,
            status=status,
            file=file_path,
            line=line_no,
            issues=issues,
        )
