"""Mod Performance and Anti-Stutter Code Auditor for Nuclear Option BepInEx plugins."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List, Optional

from rich.table import Table
from rich import box

from nuclear_engine.config import config


@dataclass
class AuditIssue:
    severity: str  # "CRITICAL", "WARNING", "ADVICE"
    rule: str
    file_name: str
    line_number: int
    message: str
    fix_suggestion: str


@dataclass
class AuditResult:
    mod_name: str
    issues: List[AuditIssue]

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "CRITICAL")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "WARNING")

    @property
    def is_clean(self) -> bool:
        return self.critical_count == 0 and self.warning_count == 0


class CodeAuditor:
    """Audits mod source code for performance bottlenecks, GC allocation spikes, and framerate stutters."""

    HOT_METHODS = {"Update", "FixedUpdate", "LateUpdate", "OnGUI"}

    @classmethod
    def audit_mod(cls, mod_name: str, target_dir: Optional[Path] = None) -> AuditResult:
        root = target_dir or (config.workspace_root / "plugins" / mod_name)
        if not root.exists():
            raise FileNotFoundError(f"Mod directory not found: {root}")

        cs_files = list(root.rglob("*.cs"))
        issues: List[AuditIssue] = []

        for cs in cs_files:
            issues.extend(cls.audit_file(cs))

        return AuditResult(mod_name=mod_name, issues=issues)

    @classmethod
    def audit_file(cls, file_path: Path) -> List[AuditIssue]:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        issues: List[AuditIssue] = []

        current_method = None
        current_method_depth = None
        brace_depth = 0
        has_throttle_timer = False

        # Pre-check for timer throttling in Update
        for line in lines:
            if any(term in line for term in ("_lastSendTime", "_lastUpdateTime", "Time.time -", "timer +=", "interval")):
                has_throttle_timer = True

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Track method declaration
            method_match = re.search(
                r"(?:(?:public|private|protected|internal|static|override|virtual|async)\s+)*(void|IEnumerator|bool|int|float|[A-Za-z0-9_<>]+)\s+([A-Za-z0-9_]+)\s*\([^\)]*\)",
                stripped,
            )
            if method_match:
                candidate_name = method_match.group(2)
                current_method = candidate_name
                current_method_depth = brace_depth + 1

            opens = stripped.count("{")
            closes = stripped.count("}")
            brace_depth += opens - closes

            is_in_hot_loop = current_method in cls.HOT_METHODS

            if current_method is not None and current_method_depth is not None:
                if brace_depth < current_method_depth and closes > 0:
                    current_method = None
                    current_method_depth = None



            # Rule 1: FindObjectsOfType in Update (CRITICAL)
            if is_in_hot_loop and re.search(r"\b(FindObjectsOfType|GameObject\.Find|FindWithTag)\b", stripped):
                issues.append(AuditIssue(
                    severity="CRITICAL",
                    rule="SCENE_SEARCH_IN_HOT_LOOP",
                    file_name=file_path.name,
                    line_number=idx,
                    message="Calling FindObjectsOfType or GameObject.Find in a per-frame method causes severe frame drops.",
                    fix_suggestion="Cache object references during Awake() or Start(), or register via events."
                ))

            # Rule 2: Uncached GetComponent in Update (WARNING)
            if is_in_hot_loop and not has_throttle_timer and re.search(r"\bGetComponent<[A-Za-z0-9_]+>\(\)", stripped):
                issues.append(AuditIssue(
                    severity="WARNING",
                    rule="UNCACHED_GET_COMPONENT",
                    file_name=file_path.name,
                    line_number=idx,
                    message="GetComponent<T>() executed every frame without caching degrades performance.",
                    fix_suggestion="Store the component reference in a private field during Awake()."
                ))

            # Rule 3: Heavy LINQ allocations in Update (WARNING)
            if is_in_hot_loop and not has_throttle_timer and re.search(r"\.(Where|Select|ToList|ToArray|OrderBy)\(", stripped):
                issues.append(AuditIssue(
                    severity="WARNING",
                    rule="LINQ_HOT_LOOP_ALLOCATION",
                    file_name=file_path.name,
                    line_number=idx,
                    message="LINQ queries in per-frame methods allocate garbage on the heap, triggering frequent GC pauses.",
                    fix_suggestion="Replace with indexed for-loops or preallocated collections."
                ))

            # Rule 4: Blocking Synchronous I/O (CRITICAL)
            if is_in_hot_loop and re.search(r"(?:File\.Read|File\.Write|StreamReader|StreamWriter|TcpClient\.Connect)", stripped):
                issues.append(AuditIssue(

                    severity="CRITICAL",
                    rule="BLOCKING_IO_IN_UPDATE",
                    file_name=file_path.name,
                    line_number=idx,
                    message="Synchronous file or network I/O in main thread causes game freezes.",
                    fix_suggestion="Offload disk and network operations to background Threads or UniTask."
                ))

            # Rule 5: Empty Update/FixedUpdate (ADVICE)
            if is_in_hot_loop and (stripped == "{ }" or (stripped == "{" and idx < len(lines) and lines[idx].strip() == "}")):
                issues.append(AuditIssue(
                    severity="ADVICE",
                    rule="EMPTY_MONOBEHAVIOUR_METHOD",
                    file_name=file_path.name,
                    line_number=idx,
                    message="Empty Update() method incurs unnecessary Unity engine invocation overhead.",
                    fix_suggestion="Remove unused MonoBehaviour lifecycle callbacks."
                ))

        return issues

    @classmethod
    def render_report(cls, result: AuditResult) -> Table:
        table = Table(
            title=f"Performance & Anti-Stutter Audit: {result.mod_name} ({'CLEAN' if result.is_clean else 'OPTIMIZATIONS NEEDED'})",
            box=box.ROUNDED,
            header_style="bold cyan",
        )
        table.add_column("Severity", style="bold", width=10)
        table.add_column("Rule", style="dim", width=26)
        table.add_column("Location", width=20)
        table.add_column("Details and Remediation", justify="left")

        if not result.issues:
            table.add_row(
                "[green]CLEAN[/green]",
                "PERF_CHECKS_PASS",
                "-",
                "[green]No frame-drop hazards, hot-loop GC allocations, or blocking calls detected.[/green]"
            )
            return table

        for issue in result.issues:
            if issue.severity == "CRITICAL":
                sev_style = "[red]CRITICAL[/red]"
            elif issue.severity == "WARNING":
                sev_style = "[yellow]WARNING[/yellow]"
            else:
                sev_style = "[blue]ADVICE[/blue]"

            location = f"{issue.file_name}:{issue.line_number}"
            msg = f"{issue.message}\n[dim]Fix: {issue.fix_suggestion}[/dim]" if issue.fix_suggestion else issue.message
            table.add_row(
                sev_style,
                issue.rule,
                location,
                msg,
            )

        return table
