"""NuclearEngine Command Line Interface (CLI).
High-efficiency, token-saving tools for Nuclear Option modding, API discovery, and mission intelligence.
"""

import sys
from pathlib import Path
from typing import Optional

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree
from rich import box

from nuclear_engine import __version__
from nuclear_engine.config import config
from nuclear_engine.domain.units import KNOWN_AIRCRAFT, KNOWN_GROUND_UNITS, KNOWN_NAVAL_UNITS, lookup_unit
from nuclear_engine.domain.weapons import KNOWN_WEAPONS, lookup_weapon
from nuclear_engine.extractor.mission_scanner import MissionScanner
from nuclear_engine.extractor.decompiler import DecompilerEngine
from nuclear_engine.extractor.code_indexer import CodeIndexer
from nuclear_engine.tactical_advisor.mission_analyzer import MissionAnalyzer
from nuclear_engine.tactical_advisor.combat_math import is_in_doppler_notch, calculate_radar_horizon_km

app = typer.Typer(
    name="no",
    help="⚡ Nuclear Option Modding & Tactical Intelligence System.",
    rich_markup_mode="rich",
)
console = Console(legacy_windows=False)


@app.command()
def tui():
    """[TUI] Launch the interactive Nuclear Option search engine (OpenCode style)."""
    from nuclear_engine.tui import start_tui
    start_tui()



import json


# ==========================================
# 🛠️ MODDING & API COMMANDS (Token-Savers)
# ==========================================


@app.command()
def api(
    class_name: str,
    as_json: bool = typer.Option(False, "--json", "-j", help="Output results in JSON format"),
):
    """[MODDING] View the clean C# API (inheritance, fields, methods) of a class without code clutter."""
    indexer = CodeIndexer()
    info = indexer.parse_class(class_name)

    if not info:
        if as_json:
            print(json.dumps({"error": f"Class '{class_name}' not found"}, indent=2))
        else:
            console.print(f"[red]Class '{class_name}' not found. Try 'no sim {class_name}' or 'no decompile'.[/red]")
        return

    if as_json:
        data = {
            "name": info.name,
            "base_class": info.base_class,
            "interfaces": info.interfaces,
            "fields": [{"access": f.access, "type": f.type_name, "name": f.name, "line": f.line_number} for f in info.fields],
            "methods": [{"access": m.access, "return": m.return_type, "name": m.name, "parameters": m.parameters, "line": m.line_number} for m in info.methods],
            "structs": [{"name": s.name, "fields": s.fields, "line": s.line_number} for s in info.structs],
            "events": [{"name": e.name, "type": e.event_type, "line": e.line_number} for e in info.events],
            "enums": [{"name": en.name, "values": en.values, "line": en.line_number} for en in info.enums],
        }
        print(json.dumps(data, indent=2))
        return

    # Title & Inheritance
    inheritance = f": {info.base_class}" if info.base_class else ""
    if info.interfaces:
        inheritance += f", {', '.join(info.interfaces)}"
    console.print(Panel(f"[bold cyan]class {info.name}[/bold cyan] [yellow]{inheritance}[/yellow]\n[dim]{info.path}[/dim]", expand=False))

    # Fields
    if info.fields:
        f_table = Table(title=f"Fields ({len(info.fields)})", box=box.SIMPLE)
        f_table.add_column("Access", style="cyan")
        f_table.add_column("Type", style="green")
        f_table.add_column("Name", style="bold white")
        f_table.add_column("Line", justify="right", style="dim")
        for f in info.fields[:20]:
            f_table.add_row(f.access, f.type_name, f.name, str(f.line_number))
        console.print(f_table)
        if len(info.fields) > 20:
            console.print(f"[dim]... and {len(info.fields) - 20} more fields.[/dim]")

    # Methods
    if info.methods:
        m_table = Table(title=f"Methods ({len(info.methods)})", box=box.ROUNDED)
        m_table.add_column("Access", style="cyan")
        m_table.add_column("Return", style="green")
        m_table.add_column("Method Name", style="bold white")
        m_table.add_column("Parameters", style="yellow")
        m_table.add_column("Line", justify="right", style="dim")

        for m in info.methods:
            mod_str = "static " if m.is_static else ("override " if m.is_override else "")
            m_table.add_row(
                f"{m.access} {mod_str}".strip(),
                m.return_type,
                m.name,
                m.parameters,
                str(m.line_number),
            )
        console.print(m_table)


@app.command()
def method(
    class_name: str,
    method_name: str,
    as_json: bool = typer.Option(False, "--json", "-j", help="Output results in JSON format"),
):
    """[MODDING] View ONLY the implementation of a specific method. Saves thousands of tokens!"""
    indexer = CodeIndexer()
    res = indexer.get_method_source(class_name, method_name)

    if not res:
        if as_json:
            print(json.dumps({"error": f"Method '{method_name}' not found in class '{class_name}'"}, indent=2))
        else:
            console.print(f"[red]Method '{method_name}' not found in class '{class_name}'.[/red]")
        return

    source, line_no = res
    if as_json:
        print(json.dumps({"class": class_name, "method": method_name, "start_line": line_no, "source": source}, indent=2))
        return

    syntax = Syntax(source, "csharp", theme="monokai", line_numbers=True, start_line=line_no)
    console.print(Panel(syntax, title=f"{class_name}.{method_name}() [Line {line_no}]", expand=False))


@app.command()
def hook(
    class_name: str,
    method_name: str,
    patch_type: str = "Prefix",
    as_json: bool = typer.Option(False, "--json", "-j", help="Output results in JSON format"),
):
    """[MODDING] Generate a ready-to-copy C# BepInEx Harmony patch for a method."""
    indexer = CodeIndexer()
    snippet = indexer.generate_harmony_patch(class_name, method_name, patch_type=patch_type)

    if not snippet:
        if as_json:
            print(json.dumps({"error": f"Could not generate hook for '{class_name}.{method_name}'"}, indent=2))
        else:
            console.print(f"[red]Could not generate hook for '{class_name}.{method_name}'. Check names.[/red]")
        return

    if as_json:
        print(json.dumps({"class": class_name, "method": method_name, "patch_type": patch_type, "patch": snippet}, indent=2))
        return

    syntax = Syntax(snippet, "csharp", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title=f"Harmony Patch: {class_name}.{method_name}", expand=False))


@app.command()
def sim(
    keyword: str,
    limit: int = 25,
    as_json: bool = typer.Option(False, "--json", "-j", help="Output results in JSON format"),
):
    """[MODDING] Find similar APIs / methods across all game classes to group functionality."""
    indexer = CodeIndexer()
    matches = indexer.search_similar_apis(keyword, max_results=limit)

    if as_json:
        print(json.dumps([{"class": m.class_name, "method": m.name, "parameters": m.parameters, "return_type": m.return_type} for m in matches], indent=2))
        return

    console.print(f"[bold cyan]Searching all classes for methods matching '{keyword}'...[/bold cyan]")
    if not matches:
        console.print(f"[yellow]No methods matching '{keyword}' found.[/yellow]")
        return

    table = Table(title=f"APIs matching '{keyword}' ({len(matches)})", box=box.ROUNDED)
    table.add_column("Class", style="bold cyan")
    table.add_column("Method", style="bold white")
    table.add_column("Parameters", style="yellow")
    table.add_column("Return", style="green")

    for m in matches:
        table.add_row(m.class_name, m.name, m.parameters, m.return_type)

    console.print(table)


@app.command()
def callers(
    target: str,
    limit: int = 25,
    as_json: bool = typer.Option(False, "--json", "-j", help="Output results in JSON format"),
):
    """[MODDING] Find all places in the game code where a method, field, or event is called."""
    indexer = CodeIndexer()
    refs = indexer.find_callers(target, limit=limit)

    if as_json:
        print(json.dumps([{"class": c, "line": ln, "snippet": sn} for c, ln, sn in refs], indent=2))
        return

    console.print(f"[bold cyan]Finding callers/references of '{target}'...[/bold cyan]")
    if not refs:
        console.print(f"[yellow]No callers of '{target}' found.[/yellow]")
        return

    table = Table(title=f"Callers & References of '{target}' ({len(refs)})", box=box.ROUNDED)
    table.add_column("Calling Class", style="bold cyan")
    table.add_column("Line", justify="right", style="dim")
    table.add_column("Code Snippet", style="white")

    for c_name, line_no, snippet in refs:
        table.add_row(c_name, str(line_no), snippet[:110])

    console.print(table)


@app.command()
def subclasses(
    base_class: str,
    as_json: bool = typer.Option(False, "--json", "-j", help="Output results in JSON format"),
):
    """[MODDING] Show all classes that inherit from a base class or interface (e.g. Unit, Weapon)."""
    indexer = CodeIndexer()
    subs = indexer.find_subclasses(base_class)

    if as_json:
        print(json.dumps([{"subclass": name, "file": path.name} for name, path in subs], indent=2))
        return

    console.print(f"[bold cyan]Searching subclasses of '{base_class}'...[/bold cyan]")
    if not subs:
        console.print(f"[yellow]No classes inheriting from '{base_class}' found.[/yellow]")
        return

    tree = Tree(f"[bold green]{base_class}[/bold green] ({len(subs)} subclasses / implementations)")
    for name, path in subs:
        tree.add(f"[bold cyan]{name}[/bold cyan] [dim]({path.name})[/dim]")
    console.print(tree)


@app.command()
def structs(
    class_name: str,
    as_json: bool = typer.Option(False, "--json", "-j", help="Output results in JSON format"),
):
    """[MODDING] Show all structs defined inside a class (e.g. OnMissileWarning in MissileWarning)."""
    indexer = CodeIndexer()
    info = indexer.parse_class(class_name)

    if not info or not info.structs:
        if as_json:
            print(json.dumps([], indent=2))
        else:
            console.print(f"[yellow]No structs found in class '{class_name}'.[/yellow]")
        return

    if as_json:
        print(json.dumps([{"name": s.name, "fields": s.fields, "line": s.line_number} for s in info.structs], indent=2))
        return

    table = Table(title=f"Structs in {info.name} ({len(info.structs)})", box=box.ROUNDED)
    table.add_column("Struct Name", style="bold cyan")
    table.add_column("Fields", style="green")
    table.add_column("Line", justify="right", style="dim")

    for s in info.structs:
        fields_str = ", ".join(f"{t} {n}" for t, n in s.fields) or "[dim]empty[/dim]"
        table.add_row(s.name, fields_str, str(s.line_number))

    console.print(table)


@app.command()
def events(
    class_name: str,
    as_json: bool = typer.Option(False, "--json", "-j", help="Output results in JSON format"),
):
    """[MODDING] Show all subscribable C# events in a class."""
    indexer = CodeIndexer()
    info = indexer.parse_class(class_name)

    if not info or not info.events:
        if as_json:
            print(json.dumps([], indent=2))
        else:
            console.print(f"[yellow]No events found in class '{class_name}'.[/yellow]")
        return

    if as_json:
        print(json.dumps([{"name": e.name, "type": e.event_type, "line": e.line_number} for e in info.events], indent=2))
        return

    table = Table(title=f"Events in {info.name} ({len(info.events)})", box=box.ROUNDED)
    table.add_column("Event Name", style="bold cyan")
    table.add_column("Type / Action", style="magenta")
    table.add_column("Line", justify="right", style="dim")

    for e in info.events:
        table.add_row(e.name, e.event_type, str(e.line_number))

    console.print(table)


@app.command()
def enums(
    target: str,
    as_json: bool = typer.Option(False, "--json", "-j", help="Output results in JSON format"),
):
    """[MODDING] Show enums inside a class or search for an enum by name across all game classes."""
    indexer = CodeIndexer()
    info = indexer.parse_class(target)

    # 1. Target is a class containing enums
    if info and info.enums:
        if as_json:
            print(json.dumps([{"name": en.name, "values": en.values, "line": en.line_number} for en in info.enums], indent=2))
            return
        for enum in info.enums:
            console.print(f"[bold cyan]enum {enum.name}[/bold cyan] [dim](in {info.name}, Line {enum.line_number})[/dim]")
            for val in enum.values:
                console.print(f"  • [yellow]{val}[/yellow]")
        return

    # 2. Target might be an enum name itself across any class
    indexer._ensure_cache()
    matches = []
    for c_lower, path in indexer._class_cache.items():
        c_info = indexer.parse_class(path.stem)
        if c_info:
            for enum in c_info.enums:
                if target.lower() in enum.name.lower():
                    matches.append({"name": enum.name, "values": enum.values, "class": c_info.name, "line": enum.line_number})

    if as_json:
        print(json.dumps(matches, indent=2))
        return

    console.print(f"[bold cyan]Searching all classes for enum '{target}'...[/bold cyan]")
    if not matches:
        console.print(f"[yellow]No enum matching '{target}' found.[/yellow]")
        return

    for m in matches:
        console.print(f"\n[bold cyan]enum {m['name']}[/bold cyan] [dim](in {m['class']}.cs, Line {m['line']})[/dim]")
        for val in m["values"]:
            console.print(f"  • [yellow]{val}[/yellow]")


# ==========================================
# 🚀 SDK BUILD, DEPLOY & IDE INTEGRATION
# ==========================================


@app.command()
def build(mod_name: str, configuration: str = "Release"):
    """[SDK] Compile a C# BepInEx mod using SDK Roslyn compiler and publicized assemblies."""
    from nuclear_engine.builder.mod_builder import ModPipeline
    pipeline = ModPipeline()
    console.print(f"[bold cyan]Compiling mod '{mod_name}' ({configuration})...[/bold cyan]")
    dll = pipeline.build(mod_name, configuration=configuration)
    console.print(f"[bold green]Build succeeded:[/bold green] {dll} ({dll.stat().st_size} bytes)")


@app.command()
def deploy(mod_name: str, configuration: str = "Release"):
    """[SDK] Build and deploy mod directly into Nuclear Option's BepInEx/plugins folder."""
    from nuclear_engine.builder.mod_builder import ModPipeline
    pipeline = ModPipeline()
    console.print(f"[bold cyan]Building & deploying mod '{mod_name}'...[/bold cyan]")
    dest = pipeline.deploy(mod_name, configuration=configuration)
    console.print(f"[bold green]Deployed successfully to Steam plugins:[/bold green] {dest}")


@app.command(name="run-game")
def run_game():
    """[SDK] Launch Nuclear Option via Steam."""
    from nuclear_engine.builder.mod_builder import ModPipeline
    console.print("[bold green]Launching Nuclear Option via Steam...[/bold green]")
    ModPipeline.launch_game()


@app.command()
def publicize():
    """[SDK] Publicize Assembly-CSharp.dll for 100% private field autocomplete in IDEs."""
    from nuclear_engine.extractor.publicizer import AssemblyPublicizer
    pub = AssemblyPublicizer()
    console.print("[bold cyan]Publicizing Nuclear Option Assembly-CSharp.dll...[/bold cyan]")
    out_dll = pub.publicize()
    console.print(f"[bold green]Publicized successfully:[/bold green] {out_dll} ({out_dll.stat().st_size} bytes)")


@app.command()
def decompile(
    assembly: Optional[str] = typer.Argument(None, help="Target assembly name (e.g. 'Assembly-CSharp', 'Mirage', 'Rewired_Core')"),
    force: bool = typer.Option(False, "--force", "-f", help="Force decompilation even if already present"),
):
    """[SDK] Decompile game assemblies into searchable C# sources."""
    from nuclear_engine.extractor.decompiler import DecompilerEngine
    engine = DecompilerEngine()
    target_name = assembly or "Assembly-CSharp"
    console.print(f"[bold cyan]Decompiling {target_name}...[/bold cyan]")
    ok, msg = engine.run_decompilation(assembly_name=assembly, force=force)
    if ok:
        console.print(f"[bold green]{msg}[/bold green]")
    else:
        console.print(f"[bold red]Decompilation failed: {msg}[/bold red]")


@app.command(name="verify-patches")
def verify_patches(
    mod_name: str,
    as_json: bool = typer.Option(False, "--json", "-j", help="Output verification report as JSON"),
):
    """[SDK] Verify that [HarmonyPatch] attributes in a mod match valid game classes & methods."""
    from nuclear_engine.builder.patch_verifier import PatchVerifier
    verifier = PatchVerifier()
    try:
        results = verifier.verify_mod(mod_name)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        return

    if as_json:
        out = [
            {
                "target_class": r.target_class,
                "target_method": r.target_method,
                "patch_type": r.patch_type,
                "status": r.status,
                "valid": r.is_valid,
                "file": str(r.file),
                "line": r.line,
                "issues": [{"severity": i.severity, "message": i.message, "line": i.line} for i in r.issues],
            }
            for r in results
        ]
        print(json.dumps(out, indent=2))
        return

    console.print(f"[bold cyan]Verifying Harmony patches in '{mod_name}'...[/bold cyan]")
    if not results:
        console.print("[yellow]No [HarmonyPatch] attributes detected in mod source files.[/yellow]")
        return

    table = Table(title=f"Patch Verification Report: {mod_name}", box=box.ROUNDED)
    table.add_column("Status", justify="center")
    table.add_column("Target Class", style="bold cyan")
    table.add_column("Target Method", style="bold white")
    table.add_column("Hook Type", style="magenta")
    table.add_column("Details / Issues")
    table.add_column("Location", style="dim")

    for r in results:
        if r.status == "PASS":
            status_badge = "[bold green]PASS[/bold green]"
        elif r.status == "WARN":
            status_badge = "[bold yellow]WARN[/bold yellow]"
        else:
            status_badge = "[bold red]FAIL[/bold red]"

        issue_text = "\n".join(f"• [{i.severity.lower()}]{i.message}[/]" for i in r.issues) or "[green]Valid signature[/green]"
        table.add_row(status_badge, r.target_class, r.target_method, r.patch_type, issue_text, f"{r.file.name}:{r.line}")

    console.print(table)


@app.command()
def logs(
    source: str = typer.Option("bepinex", "--source", "-s", help="Log source: 'bepinex' (mods) or 'player' (Unity game)"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of trailing lines to view"),
    errors_only: bool = typer.Option(False, "--errors-only", "-e", help="Show only errors and warnings"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow / stream log output live"),
    as_json: bool = typer.Option(False, "--json", "-j", help="Output log entries in JSON format"),
):
    """[SDK] View and stream game and BepInEx mod logs with syntax highlighting."""
    from nuclear_engine.diagnostics.log_viewer import LogViewer
    viewer = LogViewer()

    if follow:
        console.print(f"[bold cyan]Streaming live logs from {source}... (Press Ctrl+C to stop)[/bold cyan]")
        try:
            for entry in viewer.follow(source=source, errors_only=errors_only):
                if entry.level == "ERROR":
                    console.print(f"[red]{entry.raw}[/red]")
                elif entry.level == "WARN":
                    console.print(f"[yellow]{entry.raw}[/yellow]")
                else:
                    console.print(entry.raw)
        except KeyboardInterrupt:
            console.print("\n[dim]Log stream stopped.[/dim]")
        return

    entries = viewer.read_entries(source=source, lines=lines, errors_only=errors_only)
    if as_json:
        print(json.dumps([{"source": e.source, "level": e.level, "message": e.message} for e in entries], indent=2))
        return

    if not entries:
        console.print(f"[yellow]No log entries found for source '{source}'.[/yellow]")
        return

    console.print(f"[bold cyan]Showing last {len(entries)} lines from {source} log:[/bold cyan]")
    for e in entries:
        if e.level == "ERROR":
            console.print(f"[red]{e.raw}[/red]")
        elif e.level == "WARN":
            console.print(f"[yellow]{e.raw}[/yellow]")
        elif e.level == "INFO":
            console.print(f"[green]{e.raw}[/green]")
        else:
            console.print(f"[dim]{e.raw}[/dim]")


@app.command(name="add-config")
def add_config(mod_name: str):
    """[SDK] Generate typed BepInEx ConfigFile boilerplate (ModConfig.cs) in a mod."""
    from nuclear_engine.builder.config_generator import generate_config_file
    try:
        cfg_file = generate_config_file(mod_name)
        console.print(f"[bold green]Created configuration template:[/bold green] {cfg_file}")
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")


@app.command(name="sync-ide")
def sync_ide():
    """[SDK] Synchronize Visual Studio / Rider solution (.sln), VS Code settings, and IntelliSense docstrings."""
    from nuclear_engine.builder.ide_sync import IDESync
    sync = IDESync()
    res = sync.sync_all()
    console.print(f"[bold green]Generated Master Solution:[/bold green] {res['sln']}")
    console.print(f"[bold green]Generated XML Docstrings:[/bold green] {res['xml_docs']}")
    console.print(f"[bold green]Updated VS Code Settings:[/bold green] {res['settings']}")
    console.print(f"[bold green]Updated Extension Recommendations:[/bold green] {res['extensions']}")


@app.command(name="new-mod")
def new_mod(mod_name: str):
    """[MODDING] Scaffold a new, ready-to-compile BepInEx C# mod with Harmony patches."""
    mod_dir = config.workspace_root / "plugins" / mod_name
    if mod_dir.exists():
        console.print(f"[red]Directory already exists: {mod_dir}[/red]")
        return

    mod_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create clean .csproj (inherits full references from Directory.Build.props)
    csproj_content = f"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>netstandard2.1</TargetFramework>
    <AssemblyName>{mod_name}</AssemblyName>
    <Description>{mod_name} Mod for Nuclear Option</Description>
    <Version>1.0.0</Version>
    <LangVersion>latest</LangVersion>
  </PropertyGroup>
</Project>
"""
    with open(mod_dir / f"{mod_name}.csproj", "w", encoding="utf-8") as f:
        f.write(csproj_content)

    # 2. Create Plugin.cs
    plugin_content = f"""using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using UnityEngine;

namespace {mod_name}
{{
    [BepInPlugin("com.nuclearoption.{mod_name.lower()}", "{mod_name}", "1.0.0")]
    public class {mod_name}Plugin : BaseUnityPlugin
    {{
        internal static ManualLogSource ModLogger;

        private void Awake()
        {{
            ModLogger = Logger;
            ModLogger.LogInfo("{mod_name} loaded successfully!");

            var harmony = new Harmony("com.nuclearoption.{mod_name.lower()}");
            harmony.PatchAll();
        }}
    }}

    // Example Harmony Patch: Hooks into aircraft missile lock
    [HarmonyPatch(typeof(Aircraft), nameof(Aircraft.LockedByMissile))]
    public static class Patch_Aircraft_LockedByMissile
    {{
        [HarmonyPrefix]
        public static void Prefix(Aircraft __instance, Missile missile)
        {{
            {mod_name}Plugin.ModLogger.LogInfo($"[Alert] Aircraft {{__instance.name}} locked by {{missile.name}}!");
        }}
    }}
}}
"""
    with open(mod_dir / "Plugin.cs", "w", encoding="utf-8") as f:
        f.write(plugin_content)

    # 3. Synchronize Solution and IDE settings
    from nuclear_engine.builder.ide_sync import IDESync
    IDESync().sync_all()

    console.print(f"[bold green]✓ Successfully scaffolded mod '{mod_name}' at:[/bold green]\n  {mod_dir}")
    console.print(f"\n[dim]To compile:[/dim]\n  uv run no build {mod_name}")
    console.print(f"[dim]To deploy to Steam:[/dim]\n  uv run no deploy {mod_name}")


@app.command()
def pack(
    mod_name: str,
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Explicit version number (e.g. 1.0.0)"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Short description of the mod"),
    as_json: bool = typer.Option(False, "--json", "-j", help="Output result as JSON"),
):
    """[SDK] Package mod into a Thunderstore-compatible zip distribution in dist/."""
    from nuclear_engine.builder.packer import ModPacker
    packer = ModPacker()
    try:
        res = packer.pack(mod_name, version=version, description=description)
        if as_json:
            print(json.dumps({
                "mod_name": res.mod_name,
                "version": res.version,
                "zip_path": str(res.zip_path),
                "size_bytes": res.size_bytes,
                "manifest": res.manifest,
            }, indent=2))
            return

        console.print(f"[bold green]Successfully packaged '{res.mod_name}' (v{res.version}):[/bold green]")
        console.print(f"  Archive: [cyan]{res.zip_path}[/cyan] ({res.size_bytes} bytes)")
        console.print("  Contents: manifest.json, icon.png, README.md, DLL, ModConfig.cs")
        console.print("[dim]Ready for 1-click upload to Thunderstore / r2modman.[/dim]")
    except Exception as e:
        console.print(f"[bold red]Packaging failed:[/bold red] {e}")


@app.command()
def vehicle(
    name: str,
    as_json: bool = typer.Option(False, "--json", "-j", help="Output specs as JSON"),
):
    """[INTEL] Inspect aircraft specs, radar cross section, and hardpoint weapon stations."""
    from nuclear_engine.domain.vehicle_inspector import VehicleInspector
    v = VehicleInspector.get_vehicle(name)
    if not v:
        console.print(f"[red]Vehicle '{name}' not found. Run 'no vehicles' to list all supported airframes.[/red]")
        return

    if as_json:
        data = {
            "name": v.name,
            "designation": v.designation,
            "role": v.role,
            "faction": v.faction,
            "empty_weight_kg": v.empty_weight_kg,
            "max_takeoff_weight_kg": v.max_takeoff_weight_kg,
            "top_speed_mach": v.top_speed_mach,
            "service_ceiling_m": v.service_ceiling_m,
            "rcs_m2": v.rcs_m2,
            "radar_type": v.radar_type,
            "countermeasures": v.countermeasures,
            "hardpoints": [
                {
                    "station": h.station_index,
                    "name": h.name,
                    "location": h.location,
                    "max_weight_kg": h.max_weight_kg,
                    "weapons": h.compatible_weapons,
                }
                for h in v.hardpoints
            ],
        }
        print(json.dumps(data, indent=2))
        return

    table = Table(title=f"{v.designation} '{v.name}' Specifications", box=box.ROUNDED)
    table.add_column("Attribute", style="cyan")
    table.add_column("Value", style="bold white")

    table.add_row("Role", v.role)
    table.add_row("Faction", v.faction)
    table.add_row("Crew", str(v.crew))
    table.add_row("Empty Weight", f"{v.empty_weight_kg:,} kg")
    table.add_row("Max Takeoff Weight", f"{v.max_takeoff_weight_kg:,} kg")
    table.add_row("Top Speed", f"Mach {v.top_speed_mach}")
    table.add_row("Service Ceiling", f"{v.service_ceiling_m:,} m")
    table.add_row("Radar Cross Section (RCS)", f"{v.rcs_m2} m²")
    table.add_row("Radar Suite", v.radar_type)
    table.add_row("Countermeasures", ", ".join(f"{k}: {val}" for k, val in v.countermeasures.items()))

    console.print(table)

    if v.hardpoints:
        hp_table = Table(title=f"{v.name} Hardpoint Stations ({len(v.hardpoints)})", box=box.SIMPLE_HEAVY)
        hp_table.add_column("#", justify="center")
        hp_table.add_column("Station Name", style="bold yellow")
        hp_table.add_column("Location")
        hp_table.add_column("Max Load", justify="right")
        hp_table.add_column("Compatible Ordnance", style="dim")

        for h in v.hardpoints:
            hp_table.add_row(str(h.station_index), h.name, h.location, f"{h.max_weight_kg} kg", ", ".join(h.compatible_weapons))

        console.print(hp_table)


@app.command()
def vehicles(as_json: bool = typer.Option(False, "--json", "-j", help="Output all vehicles as JSON")):
    """[INTEL] List all indexed Nuclear Option vehicles and designations."""
    from nuclear_engine.domain.vehicle_inspector import VehicleInspector
    all_v = VehicleInspector.list_all()

    if as_json:
        print(json.dumps([{"name": v.name, "designation": v.designation, "role": v.role, "hardpoints": len(v.hardpoints)} for v in all_v], indent=2))
        return

    table = Table(title="Nuclear Option Airframes & Vehicles", box=box.ROUNDED)
    table.add_column("Designation", style="bold cyan")
    table.add_column("Name", style="bold white")
    table.add_column("Role")
    table.add_column("Top Speed", justify="center")
    table.add_column("RCS", justify="center")
    table.add_column("Hardpoints", justify="center")

    for v in all_v:
        table.add_row(v.designation, v.name, v.role, f"M{v.top_speed_mach}", f"{v.rcs_m2} m²", str(len(v.hardpoints)))

    console.print(table)


@app.command()
def docs():
    """[SDK] Generate complete offline HTML API documentation for all 1,200+ game classes."""
    from nuclear_engine.extractor.doc_generator import APIDocGenerator
    console.print("[bold cyan]Generating offline API documentation in docs/api/...[/bold cyan]")
    gen = APIDocGenerator()
    html_path = gen.generate()
    console.print(f"[bold green]API Documentation generated successfully:[/bold green]\n  {html_path}")
    console.print(f"[dim]File size: {html_path.stat().st_size:,} bytes. Open in any browser.[/dim]")


@app.command(name="mission-map")
def mission_map(
    mission_name: str,
    web: bool = typer.Option(False, "--web", "--html", help="Generate interactive HTML tactical map with unit details"),
    svg: bool = typer.Option(False, "--svg", help="Export vector SVG map to file"),
    width: int = typer.Option(60, "--width", "-w", help="ASCII grid width"),
    height: int = typer.Option(24, "--height", "-h", help="ASCII grid height"),
):
    """[INTEL] Render a 2D tactical radar map of a mission scenario."""
    from nuclear_engine.extractor.mission_scanner import MissionScanner
    from nuclear_engine.tactical_advisor.map_renderer import TacticalMapRenderer

    scanner = MissionScanner()
    res = scanner.load_latest_mission_file(mission_name)
    if not res:
        console.print(f"[red]Mission '{mission_name}' not found.[/red]")
        return

    path, mission = res
    renderer = TacticalMapRenderer(mission)

    if web:
        html_content = renderer.render_interactive_html(mission_name)
        out_html = config.workspace_root / f"{mission_name.replace(' ', '_')}_map.html"
        out_html.write_text(html_content, encoding="utf-8")
        console.print(f"[bold green]Interactive Tactical War Room Map generated:[/bold green]\n  {out_html}")
        console.print(f"[dim]Total contacts plotted: {len(renderer.points)} (Airbases, SAM sites, Armor, Warships, Structures)[/dim]")
        return

    if svg:
        svg_content = renderer.render_svg()
        out_svg = config.workspace_root / f"{mission_name.replace(' ', '_')}_map.svg"
        out_svg.write_text(svg_content, encoding="utf-8")
        console.print(f"[bold green]Tactical SVG map exported:[/bold green] {out_svg}")
        return

    console.print(f"[bold cyan]Tactical Map: {mission_name}[/bold cyan]")
    console.print(renderer.render_ascii(width=width, height=height))


@app.command()
def watch(mod_name: str, interval: float = typer.Option(0.5, "--interval", "-i", help="Poll interval in seconds")):
    """[DEV] Watch mod source files and auto-rebuild + deploy to BepInEx on change."""
    from nuclear_engine.builder.watcher import ModWatcher
    watcher = ModWatcher(mod_name, poll_interval=interval)
    watcher.watch()


@app.command()
def rpc(
    target_class: Optional[str] = typer.Argument(None, help="Filter by class name (e.g. Aircraft, Player)"),
    rpc_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by RPC type: ServerRpc, ClientRpc, TargetRpc, SyncVar"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search in method names and parameters"),
    as_json: bool = typer.Option(False, "--json", "-j", help="Output results as JSON"),
):
    """[NETWORK] Inspect Mirage multiplayer RPCs and SyncVars in decompiled code."""
    from nuclear_engine.extractor.rpc_inspector import RPCInspector
    inspector = RPCInspector()
    results = inspector.query(class_filter=target_class, rpc_type=rpc_type, search_query=query)

    if as_json:
        print(json.dumps([
            {
                "type": r.endpoint_type,
                "class": r.declaring_class,
                "name": r.name,
                "parameters": r.parameters,
                "attributes": r.attributes,
                "file": r.file_name,
                "line": r.line_number,
            }
            for r in results
        ], indent=2))
        return

    if not results:
        console.print("[yellow]No network RPCs or SyncVars matching criteria.[/yellow]")
        return

    table = Table(title=f"Mirage Multiplayer Endpoints ({len(results)})", box=box.ROUNDED)
    table.add_column("Type", style="bold yellow")
    table.add_column("Class", style="bold cyan")
    table.add_column("Name / Method", style="bold white")
    table.add_column("Parameters / Type", style="dim")
    table.add_column("Line", justify="right")

    for r in results[:40]:
        table.add_row(r.endpoint_type, r.declaring_class, r.name, r.parameters, str(r.line_number))

    console.print(table)
    if len(results) > 40:
        console.print(f"[dim]Showing 40 of {len(results)} endpoints. Use --json or filter with arguments.[/dim]")


@app.command(name="new-mission")
def new_mission(
    name: str,
    preset: str = typer.Option("dogfight", "--preset", "-p", help="Scenario preset: dogfight, strike, naval_patrol"),
    player_faction: str = typer.Option("Boscali", "--player", help="Player faction name"),
    enemy_faction: str = typer.Option("Primeva", "--enemy", help="Enemy faction name"),
):
    """[SCENARIO] Programmatically generate a ready-to-play mission scenario in MissionEditor."""
    from nuclear_engine.domain.mission_generator import MissionFactory
    path = MissionFactory.save_to_mission_editor(
        mission_name=name,
        preset=preset.lower(),
        player_faction=player_faction,
        enemy_faction=enemy_faction,
    )
    console.print(f"[bold green]Mission '{name}' successfully created:[/bold green]")
    console.print(f"  File: [cyan]{path}[/cyan]")
    console.print(f"  Preset: [yellow]{preset}[/yellow] | Factions: {player_faction} vs {enemy_faction}")
    console.print("[dim]Open in Nuclear Option's Mission Editor or launch with 'no run-game'.[/dim]")


@app.command()
def audio(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category: VoiceWarning, Interface, Effects, Alert"),
    class_filter: Optional[str] = typer.Option(None, "--class", help="Filter by declaring class"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query"),
    as_json: bool = typer.Option(False, "--json", "-j", help="Output results as JSON"),
):
    """[AUDIO] Inspect game sound effects, SoundManager hooks, and cockpit voice warnings."""
    from nuclear_engine.extractor.audio_inspector import AudioInspector
    inspector = AudioInspector()
    results = inspector.query(category=category, class_filter=class_filter, search_query=query)

    if as_json:
        print(json.dumps([
            {
                "category": a.category,
                "class": a.class_name,
                "event": a.event_name,
                "mixer": a.mixer_group,
                "method": a.trigger_method,
                "line": a.line_number,
            }
            for a in results
        ], indent=2))
        return

    if not results:
        console.print("[yellow]No audio events matching criteria.[/yellow]")
        return

    table = Table(title=f"Game Audio Events ({len(results)})", box=box.ROUNDED)
    table.add_column("Category", style="bold yellow")
    table.add_column("Class", style="bold cyan")
    table.add_column("Event / Clip", style="bold white")
    table.add_column("Mixer Group", style="green")
    table.add_column("Trigger Method", style="dim")

    for a in results[:35]:
        table.add_row(a.category, a.class_name, a.event_name, a.mixer_group, a.trigger_method)

    console.print(table)
    if len(results) > 35:
        console.print(f"[dim]Showing 35 of {len(results)} audio hooks. Use --json or filter with arguments.[/dim]")


@app.command()
def telemetry(
    port: int = typer.Option(8766, "--port", "-p", help="UDP listening port"),
    packets: int = typer.Option(10, "--packets", "-n", help="Number of telemetry packets to sample"),
):
    """[INTEL] Sample real-time UDP flight telemetry from NuclearTelemetry mod."""
    from nuclear_engine.telemetry.server import TelemetryServer
    server = TelemetryServer(udp_port=port)
    console.print(f"[bold cyan]Listening for UDP telemetry on 127.0.0.1:{port} (waiting for game)...[/bold cyan]")
    try:
        server.listen_udp_sync(max_packets=packets, timeout=2.0)
        console.print(server.render_hud())
    except Exception as e:
        console.print(f"[yellow]No telemetry stream detected: {e}[/yellow]")
        console.print("[dim]Launch Nuclear Option with the NuclearTelemetry mod to stream live flight data.[/dim]")






# ==========================================
# 🔍 SEARCH & DECOMPILATION COMMANDS
# ==========================================


@app.command()
def find(query: str, limit: int = 15):
    """Quick search for classes or source code text across the decompiled game."""
    engine = DecompilerEngine()
    if not engine.is_decompiled():
        console.print("[yellow]Code is not decompiled yet. Run 'no decompile' first.[/yellow]")
        return

    classes = engine.search_classes(query)
    if classes:
        console.print(f"[bold green]Matching Classes ({len(classes)}):[/bold green]")
        for c in classes[:limit]:
            console.print(f"  • [cyan]{c.stem}[/cyan] [dim]({c.name})[/dim]")

    matches = engine.search_source_text(query, max_results=limit)
    if matches:
        console.print(f"\n[bold green]Text Occurrences ({len(matches)}):[/bold green]")
        for p, line_no, line in matches:
            console.print(f"  [dim]{p.name}:{line_no}[/dim] {line[:110]}")


@app.command()
def decompile(force: bool = False):
    """Decompile Assembly-CSharp.dll into C# source code (cached)."""
    engine = DecompilerEngine()
    console.print("[bold cyan]Initializing decompiler...[/bold cyan]")
    ok, msg = engine.run_decompilation(force=force)
    if ok:
        console.print(f"[bold green]✓ {msg}[/bold green]")
    else:
        console.print(f"[bold red]✗ {msg}[/bold red]")


# ==========================================
# 📊 MISSION & TACTICAL INTELLIGENCE
# ==========================================


@app.command()
def status():
    """Check health and paths of the game installation, BepInEx, and workspace."""
    table = Table(title="Nuclear Option System Status", box=box.ROUNDED)
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Path / Details", style="dim")

    game_ok = config.is_game_installed()
    table.add_row(
        "Game DLL (Assembly-CSharp)",
        "[green]FOUND[/green]" if game_ok else "[red]NOT FOUND[/red]",
        str(config.target_dll),
    )

    bepinex_ok = config.bepinex_dir.exists()
    table.add_row(
        "BepInEx Mod Loader",
        "[green]INSTALLED[/green]" if bepinex_ok else "[yellow]NOT INSTALLED[/yellow]",
        str(config.bepinex_dir),
    )

    missions_ok = config.has_user_missions()
    scanner = MissionScanner()
    m_count = len(scanner.list_missions())
    table.add_row(
        "Mission Editor Saves",
        f"[green]{m_count} Missions Detected[/green]" if missions_ok else "[yellow]NONE[/yellow]",
        str(config.mission_editor_dir),
    )

    decompiler = DecompilerEngine()
    decompiled_ok = decompiler.is_decompiled()
    table.add_row(
        "Decompiled C# Source Cache",
        "[green]READY[/green]" if decompiled_ok else "[yellow]NOT DECOMPILED[/yellow]",
        str(config.decompiled_dir),
    )

    console.print(table)


@app.command()
def missions():
    """List all custom & auto-saved missions found in the game's editor directory."""
    scanner = MissionScanner()
    summaries = scanner.scan_all_summaries()

    if not summaries:
        console.print("[yellow]No missions found in the Nuclear Option MissionEditor folder.[/yellow]")
        return

    table = Table(title=f"Discovered Nuclear Option Missions ({len(summaries)})", box=box.ROUNDED)
    table.add_column("Mission Name", style="bold cyan")
    table.add_column("Aircraft", justify="right", style="green")
    table.add_column("Vehicles", justify="right", style="yellow")
    table.add_column("Warships", justify="right", style="blue")
    table.add_column("Factions", style="magenta")
    table.add_column("Objectives", style="white")

    for s in summaries:
        table.add_row(
            s.name,
            str(s.aircraft_count),
            str(s.ground_count),
            str(s.ship_count),
            ", ".join(s.faction_names) or "None",
            f"{len(s.objective_names)} defined",
        )

    console.print(table)


@app.command()
def analyze(mission_name: str):
    """Run an in-depth tactical analysis on a specified mission."""
    scanner = MissionScanner()
    res = scanner.load_latest_mission_file(mission_name)

    if not res:
        console.print(f"[red]Could not find mission matching '{mission_name}'.[/red]")
        return

    path, mission = res
    analyzer = MissionAnalyzer()
    report = analyzer.analyze(mission, mission_name=mission_name)

    console.print(Panel(f"[bold green]Tactical Intelligence Report: {mission_name}[/bold green]\nSource: [dim]{path}[/dim]", expand=False))

    f_table = Table(title="Force Structure by Faction", box=box.SIMPLE_HEAVY)
    f_table.add_column("Faction", style="bold")
    f_table.add_column("Fighters", justify="right", style="cyan")
    f_table.add_column("Bombers", justify="right", style="red")
    f_table.add_column("Helos", justify="right", style="green")
    f_table.add_column("Air Defense", justify="right", style="yellow")
    f_table.add_column("Warships", justify="right", style="blue")
    f_table.add_column("Air Score", justify="right", style="bold magenta")

    for name, f_str in report.factions.items():
        f_table.add_row(
            name,
            str(f_str.fighter_count),
            str(f_str.bomber_count),
            str(f_str.attack_helo_count),
            str(f_str.air_defense_count),
            str(f_str.warship_count),
            f"{f_str.air_superiority_score:.1f}",
        )
    console.print(f_table)

    if report.objective_summaries:
        obj_tree = Tree("[bold cyan]Mission Objectives[/bold cyan]")
        for o in report.objective_summaries:
            obj_tree.add(o)
        console.print(obj_tree)

    if report.key_threats or report.tactical_recommendations:
        t_panel = Tree("[bold yellow]Tactical Insights & Threats[/bold yellow]")
        for t in report.key_threats:
            t_panel.add(f"[red]{t}[/red]")
        for r in report.tactical_recommendations:
            t_panel.add(f"[green]{r}[/green]")
        console.print(t_panel)


@app.command()
def units(category: Optional[str] = None):
    """Browse the domain database of Nuclear Option aircraft, air defenses, and warships."""
    table = Table(title="Nuclear Option Unit Encyclopedia", box=box.ROUNDED)
    table.add_column("Key", style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Category", style="magenta")
    table.add_column("Role", style="yellow")
    table.add_column("RCS Multiplier", justify="right")
    table.add_column("Radar / Jammer", justify="center")

    all_units = list(KNOWN_AIRCRAFT.values()) + list(KNOWN_GROUND_UNITS.values()) + list(KNOWN_NAVAL_UNITS.values())
    for u in all_units:
        if category and category.lower() not in u.category.value.lower():
            continue
        radar_str = ("📡 " if u.has_radar else "") + ("⚡ " if u.has_jammer else "") or "—"
        table.add_row(
            u.key,
            u.display_name,
            u.category.value,
            u.role or "N/A",
            f"{u.radar_cross_section:.2f}x",
            radar_str,
        )

    console.print(table)


@app.command()
def weapons():
    """Display missile and ordnance profiles with countermeasure tactics."""
    table = Table(title="Nuclear Option Weapons & Counters", box=box.ROUNDED)
    table.add_column("Weapon", style="bold cyan")
    table.add_column("Guidance", style="magenta")
    table.add_column("Range", justify="right", style="green")
    table.add_column("Mach", justify="right", style="yellow")
    table.add_column("Countermeasures & Tactics", style="white")

    for w in KNOWN_WEAPONS.values():
        table.add_row(
            w.display_name,
            w.guidance.value,
            f"{w.typical_range_km:.0f} km",
            f"M {w.max_speed_mach:.1f}",
            f"[bold]{', '.join(w.countermeasures)}[/bold]\n[dim]{w.tactical_advice}[/dim]",
        )

    console.print(table)


@app.command()
def doppler(speed_mps: float, aspect_deg: float):
    """Calculate Doppler notch probability against pulse-doppler radars."""
    in_notch, explanation = is_in_doppler_notch(speed_mps, aspect_deg)
    color = "green" if in_notch else "red"
    console.print(f"[{color}]{explanation}[/{color}]")


@app.command(name="validate-mission")
def validate_mission(
    target: str = typer.Argument(..., help="Path to mission.json or mission name in MissionEditor"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
):
    """Validate and lint a scenario for missing factions, ground collisions, and broken targets."""
    from nuclear_engine.domain.mission_validator import MissionValidator
    import json

    try:
        result = MissionValidator.validate_file(target)
        if json_output:
            out = {
                "mission_name": result.mission_name,
                "is_valid": result.is_valid,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "issues": [i.__dict__ for i in result.issues],
            }
            console.print(json.dumps(out, indent=2))
        else:
            table = MissionValidator.render_report(result)
            console.print(table)
            if not result.is_valid:
                raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Validation Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command(name="il")
def il_inspect(
    target: str = typer.Argument(..., help="Target in Class.Method format (e.g. RadarWarning.Start)"),
    matcher: bool = typer.Option(False, "--matcher", "-m", help="Generate Harmony CodeMatcher C# boilerplate"),
):
    """Disassemble and inspect raw CIL bytecode instructions for Harmony Transpilers."""
    from nuclear_engine.extractor.il_inspector import ILInspector

    if "." not in target:
        console.print("[bold red]Error:[/bold red] Target must be in 'ClassName.MethodName' format (e.g. RadarWarning.Start).")
        raise typer.Exit(code=1)

    class_name, method_name = target.split(".", 1)
    inspector = ILInspector()

    try:
        method = inspector.get_method_il(class_name, method_name)
        if not method:
            console.print(f"[bold yellow]Method not found:[/bold yellow] Could not locate {class_name}::{method_name} in game assembly.")
            raise typer.Exit(code=1)

        if matcher:
            code = inspector.generate_matcher_template(method)
            console.print(code)
        else:
            table = inspector.render_table(method)
            console.print(table)
    except Exception as e:
        console.print(f"[bold red]Disassembly Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command(name="new-livery")
def new_livery(
    vehicle: str = typer.Argument(..., help="Aircraft name (e.g. Revoker, Cricket, Darkreach)"),
    skin_name: str = typer.Argument(..., help="Skin name (e.g. GhostSquadron, DesertCamo)"),
    author: str = typer.Option("Modder", "--author", "-a", help="Author name"),
):
    """Scaffold a custom aircraft livery package with texture loader plugin."""
    from nuclear_engine.builder.livery_scaffolder import LiveryScaffolder

    out_dir = LiveryScaffolder.scaffold(vehicle, skin_name, author=author)
    console.print(f"[bold green]Livery scaffolded successfully![/bold green] -> {out_dir}")
    console.print("Place your 2048x2048 textures in this folder: [cyan]albedo.png[/cyan], [cyan]normal.png[/cyan], [cyan]metallic.png[/cyan].")


@app.command(name="audit")
def audit_mod(
    mod_name: str = typer.Argument(..., help="Mod directory name in plugins/ (e.g. NuclearTelemetry)"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
):
    """Audit mod source code for performance bottlenecks, GC spikes, and micro-stutters."""
    from nuclear_engine.diagnostics.code_auditor import CodeAuditor
    import json

    try:
        result = CodeAuditor.audit_mod(mod_name)
        if json_output:
            out = {
                "mod_name": result.mod_name,
                "is_clean": result.is_clean,
                "critical_count": result.critical_count,
                "warning_count": result.warning_count,
                "issues": [i.__dict__ for i in result.issues],
            }
            console.print(json.dumps(out, indent=2))
        else:
            table = CodeAuditor.render_report(result)
            console.print(table)
    except Exception as e:
        console.print(f"[bold red]Audit Error:[/bold red] {e}")
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == "__main__":
    main()

