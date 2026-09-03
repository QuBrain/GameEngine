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



# ==========================================
# 🛠️ MODDING & API COMMANDS (Token-Savers)
# ==========================================


@app.command()
def api(class_name: str):
    """[MODDING] View the clean C# API (inheritance, fields, methods) of a class without code clutter."""
    indexer = CodeIndexer()
    info = indexer.parse_class(class_name)

    if not info:
        console.print(f"[red]Class '{class_name}' not found. Try 'no find {class_name}' or 'no decompile'.[/red]")
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
def method(class_name: str, method_name: str):
    """[MODDING] View ONLY the implementation of a specific method. Saves thousands of tokens!"""
    indexer = CodeIndexer()
    res = indexer.get_method_source(class_name, method_name)

    if not res:
        console.print(f"[red]Method '{method_name}' not found in class '{class_name}'.[/red]")
        return

    source, line_no = res
    syntax = Syntax(source, "csharp", theme="monokai", line_numbers=True, start_line=line_no)
    console.print(Panel(syntax, title=f"{class_name}.{method_name}() [Line {line_no}]", expand=False))


@app.command()
def hook(class_name: str, method_name: str, patch_type: str = "Prefix"):
    """[MODDING] Generate a ready-to-copy C# BepInEx Harmony patch for a method."""
    indexer = CodeIndexer()
    snippet = indexer.generate_harmony_patch(class_name, method_name, patch_type=patch_type)

    if not snippet:
        console.print(f"[red]Could not generate hook for '{class_name}.{method_name}'. Check names.[/red]")
        return

    syntax = Syntax(snippet, "csharp", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title=f"Harmony Patch: {class_name}.{method_name}", expand=False))


@app.command()
def sim(keyword: str, limit: int = 25):
    """[MODDING] Find similar APIs / methods across all game classes to group functionality."""
    indexer = CodeIndexer()
    console.print(f"[bold cyan]Searching all classes for methods matching '{keyword}'...[/bold cyan]")
    matches = indexer.search_similar_apis(keyword, max_results=limit)

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
def callers(target: str, limit: int = 25):

    """[MODDING] Find all places in the game code where a method, field, or event is called."""
    indexer = CodeIndexer()
    console.print(f"[bold cyan]Finding callers/references of '{target}'...[/bold cyan]")
    refs = indexer.find_callers(target, limit=limit)

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
def subclasses(base_class: str):
    """[MODDING] Show all classes that inherit from a base class or interface (e.g. Unit, Weapon)."""
    indexer = CodeIndexer()
    console.print(f"[bold cyan]Searching subclasses of '{base_class}'...[/bold cyan]")
    subs = indexer.find_subclasses(base_class)

    if not subs:
        console.print(f"[yellow]No classes inheriting from '{base_class}' found.[/yellow]")
        return

    tree = Tree(f"[bold green]{base_class}[/bold green] ({len(subs)} subclasses / implementations)")
    for name, path in subs:
        tree.add(f"[bold cyan]{name}[/bold cyan] [dim]({path.name})[/dim]")
    console.print(tree)


@app.command()
def structs(class_name: str):
    """[MODDING] Show all structs defined inside a class (e.g. OnMissileWarning in MissileWarning)."""
    indexer = CodeIndexer()
    info = indexer.parse_class(class_name)

    if not info or not info.structs:
        console.print(f"[yellow]No structs found in class '{class_name}'.[/yellow]")
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
def events(class_name: str):
    """[MODDING] Show all subscribable C# events in a class."""
    indexer = CodeIndexer()
    info = indexer.parse_class(class_name)

    if not info or not info.events:
        console.print(f"[yellow]No events found in class '{class_name}'.[/yellow]")
        return

    table = Table(title=f"Events in {info.name} ({len(info.events)})", box=box.ROUNDED)
    table.add_column("Event Name", style="bold cyan")
    table.add_column("Type / Action", style="magenta")
    table.add_column("Line", justify="right", style="dim")

    for e in info.events:
        table.add_row(e.name, e.event_type, str(e.line_number))

    console.print(table)


@app.command()
def enums(target: str):
    """[MODDING] Show enums inside a class or search for an enum by name across all game classes."""
    indexer = CodeIndexer()
    info = indexer.parse_class(target)

    # 1. Target is a class containing enums
    if info and info.enums:
        for enum in info.enums:
            console.print(f"[bold cyan]enum {enum.name}[/bold cyan] [dim](in {info.name}, Line {enum.line_number})[/dim]")
            for val in enum.values:
                console.print(f"  • [yellow]{val}[/yellow]")
        return

    # 2. Target might be an enum name itself across any class
    console.print(f"[bold cyan]Searching all classes for enum '{target}'...[/bold cyan]")
    indexer._ensure_cache()
    found = False
    for c_lower, path in indexer._class_cache.items():
        c_info = indexer.parse_class(path.stem)
        if c_info:
            for enum in c_info.enums:
                if target.lower() in enum.name.lower():
                    found = True
                    console.print(f"\n[bold cyan]enum {enum.name}[/bold cyan] [dim](in {c_info.name}.cs, Line {enum.line_number})[/dim]")
                    for val in enum.values:
                        console.print(f"  • [yellow]{val}[/yellow]")

    if not found:
        console.print(f"[yellow]No enum matching '{target}' found.[/yellow]")



@app.command(name="new-mod")
def new_mod(mod_name: str):
    """[MODDING] Scaffold a new, ready-to-compile BepInEx C# mod with Harmony patches."""
    mod_dir = config.workspace_root / "plugins" / mod_name
    if mod_dir.exists():
        console.print(f"[red]Directory already exists: {mod_dir}[/red]")
        return

    mod_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create .csproj
    csproj_content = f"""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>netstandard2.1</TargetFramework>
    <AssemblyName>{mod_name}</AssemblyName>
    <Description>{mod_name} Mod for Nuclear Option</Description>
    <Version>1.0.0</Version>
    <LangVersion>latest</LangVersion>
  </PropertyGroup>

  <PropertyGroup>
    <GameDir>{config.game_dir}</GameDir>
    <ManagedDir>$(GameDir)\\NuclearOption_Data\\Managed</ManagedDir>
    <BepInExDir>$(GameDir)\\BepInEx\\core</BepInExDir>
  </PropertyGroup>

  <ItemGroup Condition="Exists('$(BepInExDir)')">
    <Reference Include="0Harmony"><HintPath>$(BepInExDir)\\0Harmony.dll</HintPath><Private>false</Private></Reference>
    <Reference Include="BepInEx"><HintPath>$(BepInExDir)\\BepInEx.dll</HintPath><Private>false</Private></Reference>
  </ItemGroup>

  <ItemGroup Condition="Exists('$(ManagedDir)')">
    <Reference Include="UnityEngine"><HintPath>$(ManagedDir)\\UnityEngine.dll</HintPath><Private>false</Private></Reference>
    <Reference Include="UnityEngine.CoreModule"><HintPath>$(ManagedDir)\\UnityEngine.CoreModule.dll</HintPath><Private>false</Private></Reference>
    <Reference Include="Assembly-CSharp"><HintPath>$(ManagedDir)\\Assembly-CSharp.dll</HintPath><Private>false</Private></Reference>
  </ItemGroup>
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

    console.print(f"[bold green]✓ Successfully scaffolded mod '{mod_name}' at:[/bold green]")
    console.print(f"  [cyan]{mod_dir}[/cyan]")
    console.print(f"\n[dim]To compile with dotnet:[/dim]")
    console.print(f"  [bold]dotnet build plugins/{mod_name}[/bold]")



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


def main():
    app()


if __name__ == "__main__":
    main()
