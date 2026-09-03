"""OpenCode-style Interactive Terminal Search Engine for Nuclear Option.
Starts with a centered green ASCII logo. When Enter is pressed, the input dock moves
to the bottom, and the rich information is displayed above it.
"""

from pathlib import Path
from typing import List, Tuple, Optional
import shlex

from textual.app import App, ComposeResult
from textual.containers import Vertical, Center, Middle, Container, Horizontal
from textual.widgets import Header, Footer, Input, Static, Label, ListView, ListItem
from textual.binding import Binding
from rich.console import RenderableType
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree
from rich import box

from nuclear_engine.config import config
from nuclear_engine.extractor.code_indexer import CodeIndexer
from nuclear_engine.domain.units import KNOWN_AIRCRAFT, KNOWN_GROUND_UNITS, KNOWN_NAVAL_UNITS
from nuclear_engine.domain.weapons import KNOWN_WEAPONS

ASCII_LOGO = r"""[bold green]
  _  _ _   _  ___ _    ___   _   ___    ___  ___ _____ ___ ___  _  _ 
 | \| | | | |/ __| |  | __| /_\ | _ \  / _ \| _ \_   _|_ _/ _ \| \| |
 | .` | |_| | (__| |__| _| / _ \|   / | (_) |  _/ | |  | | (_) | .` |
 |_|\_|\___/ \___|____|___/_/ \_\_|_\  \___/|_|   |_| |___\___/|_|\_|
[/bold green]
[dim green]━━━━━━━ TACTICAL INTELLIGENCE & REVERSE ENGINEERING SEARCH ENGINE ━━━━━━━[/dim green]
"""

HOME_HINTS = """[dim]
Type a class, method, or keyword (e.g. [cyan]Aircraft[/cyan], [cyan]Radar[/cyan], [cyan]LockedByMissile[/cyan], [cyan]SeekerMode[/cyan]) and press [bold green]ENTER[/bold green].
Type [yellow]clear[/yellow] or press [yellow]ESC[/yellow] to return home  •  Type [yellow]q[/yellow] to exit.
[/dim]"""


class NuclearSearchApp(App):
    CSS = """
    Screen {
        background: #0d1117;
        color: #e6edf3;
    }

    /* 1. CENTERED HOME VIEW */
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

    #home_input {
        width: 100%;
        border: tall #22c55e;
        background: #161b22;
        color: #ffffff;
        margin: 1 0;
    }

    #home_input:focus {
        border: tall #4ade80;
    }

    #home_hints {
        content-align: center middle;
        text-align: center;
        margin-top: 1;
    }

    /* 2. CHAT / BOTTOM INPUT VIEW (OpenCode Style) */
    #chat_view {
        width: 100%;
        height: 100%;
        display: none;
    }

    #info_viewport {
        height: 1fr;
        padding: 1 2;
        background: #0d1117;
        overflow-y: scroll;
    }

    #bottom_bar {
        dock: bottom;
        height: 4;
        padding: 0 1;
        background: #161b22;
        border-top: heavy #22c55e;
    }

    #bottom_input {
        width: 100%;
        border: tall #22c55e;
        background: #0d1117;
        color: #ffffff;
    }

    #bottom_input:focus {
        border: tall #4ade80;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "go_home", "Home / Clear"),
    ]

    def __init__(self):
        super().__init__()
        self.indexer = CodeIndexer()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        # 1. Centered Home View
        with Container(id="home_view"):
            with Center():
                with Middle():
                    with Vertical(id="home_box"):
                        yield Static(ASCII_LOGO, id="ascii_logo")
                        yield Input(placeholder="Search Nuclear Option (press Enter to explore)...", id="home_input")
                        yield Static(HOME_HINTS, id="home_hints")

        # 2. Bottom Input / Content Above View (OpenCode Style)
        with Container(id="chat_view"):
            with Vertical(id="info_viewport"):
                yield Static("", id="content_display")

            with Container(id="bottom_bar"):
                yield Input(placeholder="Search another class, method, or command (ESC to home, 'clear')...", id="bottom_input")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#home_input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return

        if query.lower() in ("clear", "home", "reset"):
            self.action_go_home()
            return

        if query.lower() in ("q", "quit", "exit"):
            self.exit()
            return

        # Switch to chat view (input at the bottom, info above)
        self.show_chat_view()
        self.render_query_info(query)

    def show_chat_view(self) -> None:
        home_view = self.query_one("#home_view", Container)
        chat_view = self.query_one("#chat_view", Container)
        bottom_input = self.query_one("#bottom_input", Input)

        home_view.styles.display = "none"
        chat_view.styles.display = "block"
        bottom_input.value = ""
        bottom_input.focus()

    def action_go_home(self) -> None:
        home_view = self.query_one("#home_view", Container)
        chat_view = self.query_one("#chat_view", Container)
        home_input = self.query_one("#home_input", Input)

        chat_view.styles.display = "none"
        home_view.styles.display = "block"
        home_input.value = ""
        home_input.focus()

    def render_query_info(self, query: str) -> None:
        content_display = self.query_one("#content_display", Static)
        self.indexer._ensure_cache()

        parts = query.split()
        cmd = parts[0].lower() if parts else ""
        arg = parts[1] if len(parts) > 1 else ""

        # 1. Direct Command: api <Class>
        if cmd == "api" and arg:
            self._render_class_api(arg)
            return

        # 2. Direct Command: method <Class> <Method>
        if cmd == "method" and len(parts) >= 3:
            self._render_method(parts[1], parts[2])
            return

        # 3. Direct Command: hook <Class> <Method>
        if cmd == "hook" and len(parts) >= 3:
            self._render_hook(parts[1], parts[2])
            return

        # 4. Direct Command: callers <Target>
        if cmd == "callers" and arg:
            self._render_callers(arg)
            return

        # 5. Direct Command: subclasses <BaseClass>
        if cmd == "subclasses" and arg:
            self._render_subclasses(arg)
            return

        # 6. Direct Command: enums <Target>
        if cmd == "enums" and arg:
            self._render_enums(arg)
            return

        # 7. Check if query is Class.Method (e.g. Aircraft.LockedByMissile)
        if "." in query:
            c_name, m_name = query.split(".", 1)
            c_name = c_name.strip()
            m_name = m_name.replace("()", "").strip()
            if self.indexer.find_class_file(c_name):
                self._render_method(c_name, m_name)
                return

        # 8. Check if query is an exact class name
        if self.indexer.find_class_file(query):
            self._render_class_api(query)
            return

        # 9. Check if query is an exact method across classes
        similar_methods = self.indexer.search_similar_apis(query, max_results=1)
        if similar_methods and similar_methods[0].name.lower() == query.lower():
            m = similar_methods[0]
            self._render_method(m.class_name, m.name)
            return

        # 10. Check if query is an enum
        enum_found = self._check_and_render_enum(query)
        if enum_found:
            return

        # 11. General Search Results
        self._render_general_search(query)

    def _render_class_api(self, class_name: str) -> None:
        content_display = self.query_one("#content_display", Static)
        info = self.indexer.parse_class(class_name)
        if not info:
            content_display.update(Panel(f"[red]Class '{class_name}' not found.[/red]", title="Error"))
            return

        inheritance = f": {info.base_class}" if info.base_class else ""
        if info.interfaces:
            inheritance += f", {', '.join(info.interfaces)}"

        t = Table(title=f"API: class {info.name} {inheritance}", box=box.ROUNDED, expand=True)
        t.add_column("Type / Access", style="cyan", no_wrap=True)
        t.add_column("Member", style="bold white")
        t.add_column("Signature / Detail", style="yellow")
        t.add_column("Line", justify="right", style="dim", no_wrap=True)

        for f in info.fields:
            t.add_row(f.type_name, f.name, f.access, str(f.line_number))
        for m in info.methods:
            mod_str = "static " if m.is_static else ("override " if m.is_override else "")
            t.add_row(f"{m.access} {mod_str}".strip(), m.name, f"({m.parameters}) -> {m.return_type}", str(m.line_number))

        hint_panel = Panel(
            f"[bold cyan]class {info.name}[/bold cyan] [yellow]{inheritance}[/yellow]\n"
            f"[dim]Defined in {info.path}[/dim]\n"
            f"[green]Tip:[/green] To view a method's implementation, type: [bold white]{info.name}.<MethodName>[/bold white] (e.g. [bold white]{info.name}.{info.methods[0].name if info.methods else 'Method'}[/bold white])",
            box=box.SIMPLE,
        )

        content_display.update(Vertical(hint_panel, t))

    def _render_method(self, class_name: str, method_name: str) -> None:
        content_display = self.query_one("#content_display", Static)
        res = self.indexer.get_method_source(class_name, method_name)
        if not res:
            content_display.update(Panel(f"[red]Method '{method_name}' not found in class '{class_name}'.[/red]", title="Error"))
            return

        source, line_no = res
        syntax = Syntax(source, "csharp", theme="monokai", line_numbers=True, start_line=line_no)
        method_panel = Panel(syntax, title=f"⚡ {class_name}.{method_name}() [Line {line_no}]", box=box.ROUNDED)

        # Harmony Patch
        patch = self.indexer.generate_harmony_patch(class_name, method_name)
        patch_panel = None
        if patch:
            patch_syntax = Syntax(patch, "csharp", theme="monokai")
            patch_panel = Panel(patch_syntax, title="🛠️ Ready-to-copy BepInEx Harmony Patch", box=box.ROUNDED)

        # Callers
        callers = self.indexer.find_callers(method_name, limit=10)
        callers_panel = None
        if callers:
            c_table = Table(box=box.SIMPLE)
            c_table.add_column("Calling Class", style="bold cyan")
            c_table.add_column("Line", style="dim")
            c_table.add_column("Code Snippet")
            for cl, ln, sn in callers:
                c_table.add_row(cl, str(ln), sn[:80])
            callers_panel = Panel(c_table, title=f"🔍 References / Callers of '{method_name}'", box=box.ROUNDED)

        elements = [method_panel]
        if patch_panel:
            elements.append(patch_panel)
        if callers_panel:
            elements.append(callers_panel)

        content_display.update(Vertical(*elements))

    def _render_hook(self, class_name: str, method_name: str) -> None:
        content_display = self.query_one("#content_display", Static)
        patch = self.indexer.generate_harmony_patch(class_name, method_name)
        if patch:
            syntax = Syntax(patch, "csharp", theme="monokai")
            content_display.update(Panel(syntax, title=f"Harmony Patch: {class_name}.{method_name}", box=box.ROUNDED))
        else:
            content_display.update(Panel(f"[red]Could not generate hook for {class_name}.{method_name}[/red]", title="Error"))

    def _render_callers(self, target: str) -> None:
        content_display = self.query_one("#content_display", Static)
        callers = self.indexer.find_callers(target, limit=25)
        if not callers:
            content_display.update(Panel(f"[yellow]No callers of '{target}' found in game codebase.[/yellow]", title="Callers"))
            return

        t = Table(title=f"Callers of '{target}' ({len(callers)})", box=box.ROUNDED, expand=True)
        t.add_column("Class", style="bold cyan")
        t.add_column("Line", justify="right", style="dim")
        t.add_column("Code Snippet", style="white")
        for cl, ln, sn in callers:
            t.add_row(cl, str(ln), sn[:90])
        content_display.update(t)

    def _render_subclasses(self, base_class: str) -> None:
        content_display = self.query_one("#content_display", Static)
        subs = self.indexer.find_subclasses(base_class)
        if not subs:
            content_display.update(Panel(f"[yellow]No subclasses of '{base_class}' found.[/yellow]", title="Subclasses"))
            return

        tree = Tree(f"[bold green]{base_class}[/bold green] ({len(subs)} subclasses)")
        for name, path in subs:
            tree.add(f"[bold cyan]{name}[/bold cyan] [dim]({path.name})[/dim]")
        content_display.update(Panel(tree, title=f"Subclass Hierarchy: {base_class}", box=box.ROUNDED))

    def _render_enums(self, target: str) -> None:
        content_display = self.query_one("#content_display", Static)
        info = self.indexer.parse_class(target)
        if info and info.enums:
            tables = []
            for enum in info.enums:
                t = Table(title=f"enum {enum.name} (Line {enum.line_number})", box=box.ROUNDED)
                t.add_column("Value", style="yellow")
                for v in enum.values:
                    t.add_row(v)
                tables.append(t)
            content_display.update(Vertical(*tables))
            return

        self._check_and_render_enum(target)

    def _check_and_render_enum(self, target: str) -> bool:
        content_display = self.query_one("#content_display", Static)
        for c_lower, path in self.indexer._class_cache.items():
            c_info = self.indexer.parse_class(path.stem)
            if c_info:
                for enum in c_info.enums:
                    if target.lower() in enum.name.lower():
                        t = Table(title=f"enum {enum.name} (in {c_info.name}.cs, Line {enum.line_number})", box=box.ROUNDED)
                        t.add_column("Value", style="yellow")
                        for v in enum.values:
                            t.add_row(v)
                        content_display.update(t)
                        return True
        return False

    def _render_general_search(self, query: str) -> None:
        content_display = self.query_one("#content_display", Static)
        q_lower = query.lower()

        t = Table(title=f"Search Results for '{query}'", box=box.ROUNDED, expand=True)
        t.add_column("Category", style="cyan", no_wrap=True)
        t.add_column("Name", style="bold white")
        t.add_column("Details", style="yellow")

        # Classes
        for c_lower, path in self.indexer._class_cache.items():
            if q_lower in c_lower:
                t.add_row("📦 Class", path.stem, f"Source in {path.name}")

        # Methods
        methods = self.indexer.search_similar_apis(query, max_results=15)
        for m in methods:
            t.add_row("⚡ Method", f"{m.class_name}.{m.name}()", f"({m.parameters}) -> {m.return_type}")

        # Units
        all_units = list(KNOWN_AIRCRAFT.values()) + list(KNOWN_GROUND_UNITS.values()) + list(KNOWN_NAVAL_UNITS.values())
        for u in all_units:
            if q_lower in u.key.lower() or q_lower in u.display_name.lower():
                t.add_row("✈️ Unit", u.display_name, f"{u.category.value} - {u.role}")

        if t.row_count == 0:
            content_display.update(Panel(f"[yellow]No results found for '{query}'. Try searching for 'Radar', 'Aircraft', 'Missile', or 'subclasses Unit'.[/yellow]", title="Search"))
        else:
            hint = Label("[dim green]Tip: Type any Class.Method (e.g. Aircraft.LockedByMissile) to view full source and Harmony hook.[/dim green]")
            content_display.update(Vertical(hint, t))


def start_tui():
    app = NuclearSearchApp()
    app.run()


if __name__ == "__main__":
    start_tui()
