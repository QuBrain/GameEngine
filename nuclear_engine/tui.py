"""OpenCode-style Interactive Terminal Search Engine for Nuclear Option.
Features centered green ASCII art home screen and seamless instant search results.
"""

from pathlib import Path
from typing import List, Tuple, Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Center, Middle, Container
from textual.widgets import Header, Footer, Input, ListView, ListItem, Static, Label, TabbedContent, TabPane
from textual.binding import Binding
from rich.syntax import Syntax
from rich.table import Table
from rich import box

from nuclear_engine.config import config
from nuclear_engine.extractor.code_indexer import CodeIndexer, ClassInfo, MethodInfo
from nuclear_engine.domain.units import KNOWN_AIRCRAFT, KNOWN_GROUND_UNITS, KNOWN_NAVAL_UNITS
from nuclear_engine.extractor.mission_scanner import MissionScanner

ASCII_LOGO = r"""[bold green]
  _  _ _   _  ___ _    ___   _   ___    ___  ___ _____ ___ ___  _  _ 
 | \| | | | |/ __| |  | __| /_\ | _ \  / _ \| _ \_   _|_ _/ _ \| \| |
 | .` | |_| | (__| |__| _| / _ \|   / | (_) |  _/ | |  | | (_) | .` |
 |_|\_|\___/ \___|____|___/_/ \_\_|_\  \___/|_|   |_| |___\___/|_|\_|
[/bold green]
[dim green]━━━━━━━ TACTICAL INTELLIGENCE & REVERSE ENGINEERING SEARCH ENGINE ━━━━━━━[/dim green]
"""


HINTS = """[dim]
Try searching: [cyan]Aircraft[/cyan] • [cyan]Radar[/cyan] • [cyan]Missile[/cyan] • [cyan]LockedByMissile[/cyan] • [cyan]SeekerMode[/cyan] • [cyan]TakeDamage[/cyan]
[yellow]ESC[/yellow] Clear / Home   •   [yellow]↑ / ↓[/yellow] Navigate   •   [yellow]Tab[/yellow] Switch Tabs   •   [yellow]Q[/yellow] Quit
[/dim]"""


class SearchResultItem(ListItem):
    def __init__(self, kind: str, title: str, subtitle: str, data: dict):
        super().__init__()
        self.kind = kind
        self.title_text = title
        self.subtitle_text = subtitle
        self.data = data

    def compose(self) -> ComposeResult:
        icon_map = {
            "class": "📦 [cyan]CLASS[/cyan]",
            "method": "⚡ [green]METHOD[/green]",
            "struct": "📋 [yellow]STRUCT[/yellow]",
            "event": "🔔 [magenta]EVENT[/magenta]",
            "enum": "🏷️ [blue]ENUM[/blue]",
            "unit": "✈️ [red]UNIT[/red]",
        }
        badge = icon_map.get(self.kind, "🔍")
        yield Label(f"{badge} [bold white]{self.title_text}[/bold white] [dim]({self.subtitle_text})[/dim]")


class NuclearSearchApp(App):
    CSS = """
    Screen {
        background: #0d1117;
        color: #e6edf3;
    }

    #home_view {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #home_box {
        width: 84;
        height: auto;
        align: center middle;
        padding: 1 2;
    }

    #ascii_logo {
        content-align: center middle;
        text-align: center;
        margin-bottom: 1;
    }

    #home_search_input {
        width: 100%;
        border: tall #22c55e;
        background: #161b22;
        color: #ffffff;
        margin: 1 0;
    }

    #home_search_input:focus {
        border: tall #4ade80;
    }

    #home_hints {
        content-align: center middle;
        text-align: center;
        margin-top: 1;
    }

    /* RESULTS VIEW (SPLIT SCREEN) */
    #results_view {
        width: 100%;
        height: 100%;
        display: none;
    }

    #top_search_bar {
        dock: top;
        height: 4;
        padding: 0 1;
        background: #161b22;
        border-bottom: solid #30363d;
    }

    #top_input {
        width: 100%;
        border: tall #22c55e;
        background: #0d1117;
        color: #ffffff;
    }

    #results_split {
        height: 1fr;
    }

    #results_sidebar {
        width: 38%;
        border-right: solid #30363d;
        background: #161b22;
    }

    #results_list {
        height: 100%;
        scrollbar-gutter: stable;
    }

    ListItem {
        padding: 1;
        border-bottom: solid #21262d;
    }

    ListItem:hover {
        background: #1f242c;
    }

    ListItem.-selected {
        background: #238636;
        color: white;
    }

    #preview_pane {
        width: 62%;
        padding: 1;
        background: #0d1117;
    }

    #code_preview {
        height: 100%;
        overflow-y: scroll;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "go_home", "Clear / Home"),
    ]

    def __init__(self):
        super().__init__()
        self.indexer = CodeIndexer()
        self.scanner = MissionScanner()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        # 1. CENTERED HOME VIEW (OpenCode Style)
        with Container(id="home_view"):
            with Center():
                with Middle():
                    with Vertical(id="home_box"):
                        yield Static(ASCII_LOGO, id="ascii_logo")
                        yield Input(placeholder="Search classes, methods, structs, events, units...", id="home_search_input")
                        yield Static(HINTS, id="home_hints")

        # 2. ACTIVE RESULTS VIEW (Split-Screen)
        with Container(id="results_view"):
            with Container(id="top_search_bar"):
                yield Input(placeholder="Search Nuclear Option...", id="top_input")

            with Horizontal(id="results_split"):
                with Vertical(id="results_sidebar"):
                    yield ListView(id="results_list")

                with Vertical(id="preview_pane"):
                    with TabbedContent():
                        with TabPane("Code / API", id="tab_code"):
                            yield Static("Select a result on the left to inspect its implementation.", id="code_preview")
                        with TabPane("Harmony Hook", id="tab_hook"):
                            yield Static("Ready-to-use BepInEx patch template will appear here.", id="hook_preview")
                        with TabPane("Callers", id="tab_callers"):
                            yield Static("Call hierarchy will appear here.", id="callers_preview")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#home_search_input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value.strip()

        # Switch to Results View if query has text
        if len(query) >= 1:
            self.show_results_view(query, sync_from=event.input.id)
        else:
            self.show_home_view()

    def show_results_view(self, query: str, sync_from: str) -> None:
        home_view = self.query_one("#home_view", Container)
        results_view = self.query_one("#results_view", Container)
        top_input = self.query_one("#top_input", Input)

        home_view.styles.display = "none"
        results_view.styles.display = "block"

        if sync_from == "home_search_input":
            top_input.value = query
            top_input.focus()
            top_input.cursor_position = len(query)

        self.run_search(query)

    def show_home_view(self) -> None:
        home_view = self.query_one("#home_view", Container)
        results_view = self.query_one("#results_view", Container)
        home_input = self.query_one("#home_search_input", Input)

        results_view.styles.display = "none"
        home_view.styles.display = "block"
        home_input.value = ""
        home_input.focus()

    def action_go_home(self) -> None:
        self.show_home_view()

    def run_search(self, query: str) -> None:
        results_list = self.query_one("#results_list", ListView)
        results_list.clear()

        q_lower = query.lower()
        count = 0
        max_items = 35

        # 1. Search Classes
        self.indexer._ensure_cache()
        for c_lower, path in self.indexer._class_cache.items():
            if q_lower in c_lower:
                results_list.append(SearchResultItem("class", path.stem, "Class", {"class_name": path.stem}))
                count += 1
                if count >= max_items:
                    return

        # 2. Search Methods
        methods = self.indexer.search_similar_apis(query, max_results=20)
        for m in methods:
            results_list.append(
                SearchResultItem(
                    "method",
                    f"{m.class_name}.{m.name}()",
                    f"{m.return_type}",
                    {"class_name": m.class_name, "method_name": m.name},
                )
            )
            count += 1
            if count >= max_items:
                return

        # 3. Search Units
        all_units = list(KNOWN_AIRCRAFT.values()) + list(KNOWN_GROUND_UNITS.values()) + list(KNOWN_NAVAL_UNITS.values())
        for u in all_units:
            if q_lower in u.key.lower() or q_lower in u.display_name.lower():
                results_list.append(
                    SearchResultItem(
                        "unit",
                        u.display_name,
                        u.category.value,
                        {"unit_key": u.key},
                    )
                )
                count += 1
                if count >= max_items:
                    return

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if not isinstance(item, SearchResultItem):
            return

        code_preview = self.query_one("#code_preview", Static)
        hook_preview = self.query_one("#hook_preview", Static)
        callers_preview = self.query_one("#callers_preview", Static)

        # METHOD ITEM
        if item.kind == "method":
            c_name = item.data["class_name"]
            m_name = item.data["method_name"]

            res = self.indexer.get_method_source(c_name, m_name)
            if res:
                src, line_no = res
                syntax = Syntax(src, "csharp", theme="monokai", line_numbers=True, start_line=line_no)
                code_preview.update(syntax)
            else:
                code_preview.update(f"Source for {c_name}.{m_name} could not be parsed.")

            patch = self.indexer.generate_harmony_patch(c_name, m_name)
            if patch:
                hook_preview.update(Syntax(patch, "csharp", theme="monokai"))
            else:
                hook_preview.update("No hook could be generated.")

            callers = self.indexer.find_callers(m_name, limit=15)
            if callers:
                t = Table(title=f"Callers of {m_name}", box=box.ROUNDED)
                t.add_column("Class", style="cyan")
                t.add_column("Line", style="dim")
                t.add_column("Snippet")
                for cl, ln, sn in callers:
                    t.add_row(cl, str(ln), sn[:80])
                callers_preview.update(t)
            else:
                callers_preview.update(f"No direct callers of {m_name} found.")

        # CLASS ITEM
        elif item.kind == "class":
            c_name = item.data["class_name"]
            info = self.indexer.parse_class(c_name)
            if info:
                t = Table(title=f"API: class {info.name}", box=box.ROUNDED)
                t.add_column("Type / Access", style="cyan")
                t.add_column("Member", style="bold white")
                t.add_column("Signature / Detail", style="yellow")
                t.add_column("Line", style="dim")

                for f in info.fields[:10]:
                    t.add_row(f.type_name, f.name, f.access, str(f.line_number))
                for m in info.methods[:20]:
                    t.add_row(m.return_type, m.name, m.parameters, str(m.line_number))

                code_preview.update(t)
                hook_preview.update(f"Select a specific method in {info.name} to view Harmony patch.")

                subs = self.indexer.find_subclasses(c_name)
                if subs:
                    callers_preview.update(f"Subclasses ({len(subs)}):\n" + "\n".join(f"• {n}" for n, _ in subs))
                else:
                    callers_preview.update(f"No subclasses of {c_name} found.")

        # UNIT ITEM
        elif item.kind == "unit":
            unit_key = item.data["unit_key"]
            all_units = {**KNOWN_AIRCRAFT, **KNOWN_GROUND_UNITS, **KNOWN_NAVAL_UNITS}
            u = all_units.get(unit_key)
            if u:
                info_text = f"[bold cyan]{u.display_name}[/bold cyan]\n"
                info_text += f"Category: [yellow]{u.category.value}[/yellow] | Role: [green]{u.role}[/green]\n"
                info_text += f"Radar Cross Section: [magenta]{u.radar_cross_section:.2f}x[/magenta]\n"
                info_text += f"Radar: {'Yes' if u.has_radar else 'No'} | RWR: {'Yes' if u.has_rwr else 'No'} | Jammer: {'Yes' if u.has_jammer else 'No'}\n\n"
                info_text += f"[white]{u.description}[/white]\n\n"
                if u.common_weapons:
                    info_text += f"[bold]Standard Loadout:[/bold]\n" + "\n".join(f"• {w}" for w in u.common_weapons)
                code_preview.update(info_text)
                hook_preview.update("N/A for static unit database")
                callers_preview.update("N/A")


def start_tui():
    app = NuclearSearchApp()
    app.run()


if __name__ == "__main__":
    start_tui()
