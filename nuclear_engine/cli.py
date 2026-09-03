"""NuclearEngine Command Line Interface powered by Rich."""

import sys
from pathlib import Path
from typing import Optional

# Ensure UTF-8 output on Windows console to prevent charmap errors
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich import box

from nuclear_engine import __version__
from nuclear_engine.config import config
from nuclear_engine.domain.units import KNOWN_AIRCRAFT, KNOWN_GROUND_UNITS, KNOWN_NAVAL_UNITS, lookup_unit
from nuclear_engine.domain.weapons import KNOWN_WEAPONS, lookup_weapon
from nuclear_engine.extractor.mission_scanner import MissionScanner
from nuclear_engine.extractor.decompiler import DecompilerEngine
from nuclear_engine.tactical_advisor.mission_analyzer import MissionAnalyzer
from nuclear_engine.tactical_advisor.combat_math import is_in_doppler_notch, calculate_radar_horizon_km

app = typer.Typer(
    name="nuclear-engine",
    help="Nuclear Option Tactical Intelligence, Mission Engine, and Code Explorer.",
    rich_markup_mode="rich",
)
console = Console(legacy_windows=False)



@app.command()
def status():
    """Check the health and paths of the Nuclear Option installation and workspace."""
    table = Table(title="Nuclear Option System Status", box=box.ROUNDED)
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Path / Details", style="dim")

    # Game directory
    game_ok = config.is_game_installed()
    table.add_row(
        "Game DLL (Assembly-CSharp)",
        "[green]FOUND[/green]" if game_ok else "[red]NOT FOUND[/red]",
        str(config.target_dll),
    )

    # BepInEx
    bepinex_ok = config.bepinex_dir.exists()
    table.add_row(
        "BepInEx Mod Loader",
        "[green]INSTALLED[/green]" if bepinex_ok else "[yellow]NOT INSTALLED[/yellow]",
        str(config.bepinex_dir),
    )

    # Mission Editor Directory
    missions_ok = config.has_user_missions()
    scanner = MissionScanner()
    m_count = len(scanner.list_missions())
    table.add_row(
        "Mission Editor Saves",
        f"[green]{m_count} Missions Detected[/green]" if missions_ok else "[yellow]NONE[/yellow]",
        str(config.mission_editor_dir),
    )

    # Decompiler cache
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

    # Factions and Force Balance Table
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

    # Objectives
    if report.objective_summaries:
        obj_tree = Tree("[bold cyan]Mission Objectives[/bold cyan]")
        for o in report.objective_summaries:
            obj_tree.add(o)
        console.print(obj_tree)

    # Key Threats & Tactical Insights
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
def decompile(force: bool = False):
    """Decompile the game's Assembly-CSharp.dll into readable C# source code."""
    engine = DecompilerEngine()
    console.print("[bold cyan]Initializing ILSpy decompiler...[/bold cyan]")
    ok, msg = engine.run_decompilation(force=force)
    if ok:
        console.print(f"[bold green]✓ {msg}[/bold green]")
    else:
        console.print(f"[bold red]✗ {msg}[/bold red]")


@app.command()
def code(query: str, max_results: int = 20):
    """Search for classes or text in the decompiled Nuclear Option codebase."""
    engine = DecompilerEngine()
    if not engine.is_decompiled():
        console.print("[yellow]Code is not yet decompiled. Run 'nuclear-engine decompile' first.[/yellow]")
        return

    classes = engine.search_classes(query)
    if classes:
        console.print(f"[bold green]Found {len(classes)} matching class files:[/bold green]")
        for c in classes[:max_results]:
            console.print(f"  • [cyan]{c.stem}[/cyan] [dim]({c.name})[/dim]")

    matches = engine.search_source_text(query, max_results=max_results)
    if matches:
        console.print(f"\n[bold green]Text occurrences for '{query}':[/bold green]")
        for p, line_no, line in matches:
            console.print(f"  [dim]{p.name}:{line_no}[/dim] {line[:120]}")


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
