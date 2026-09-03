"""Hot-Reload File Watcher and Auto-Deploy pipeline for Nuclear Option mods."""

from pathlib import Path
import time
from typing import Dict, Optional
from rich.console import Console

from nuclear_engine.config import config
from nuclear_engine.builder.mod_builder import ModPipeline
from nuclear_engine.builder.patch_verifier import PatchVerifier
from nuclear_engine.extractor.code_indexer import CodeIndexer


console = Console()


class ModWatcher:
    def __init__(self, mod_name: str, poll_interval: float = 0.5):
        self.mod_name = mod_name
        self.mod_dir = config.workspace_root / "plugins" / mod_name
        self.poll_interval = poll_interval

        self.pipeline = ModPipeline()
        self.indexer = CodeIndexer()
        self.verifier = PatchVerifier(self.indexer)

    def _get_mtimes(self) -> Dict[Path, float]:
        mtimes: Dict[Path, float] = {}
        if not self.mod_dir.exists():
            return mtimes
        for f in self.mod_dir.rglob("*.cs"):
            try:
                mtimes[f] = f.stat().st_mtime
            except OSError:
                pass
        return mtimes

    def run_once(self) -> bool:
        """Trigger a single build-verify-deploy cycle."""
        start = time.perf_counter()
        console.print(f"[cyan][{time.strftime('%H:%M:%S')}] Detected change in '{self.mod_name}'. Rebuilding...[/cyan]")

        try:
            deployed_path = self.pipeline.deploy(self.mod_name)
        except Exception as e:
            console.print(f"[bold red][FAIL] Compilation/Deployment failed:[/bold red]\n{e}")
            return False


        # Verify patches
        patches = self.verifier.verify_mod(self.mod_name)
        invalid = [p for p in patches if not p.is_valid]
        if invalid:
            console.print(f"[yellow]Warning: {len(invalid)} invalid Harmony patch(es) detected![/yellow]")

        elapsed = (time.perf_counter() - start) * 1000.0
        console.print(f"[bold green][OK] Rebuilt & Deployed in {elapsed:.0f} ms[/bold green] -> {deployed_path.name}")
        return True


    def watch(self, max_iterations: Optional[int] = None):
        """Watch loop. If max_iterations is set, stops after that many iterations."""
        if not self.mod_dir.exists():
            raise FileNotFoundError(f"Mod directory '{self.mod_dir}' does not exist.")

        console.print(f"[bold cyan]Watching '{self.mod_name}' for changes...[/bold cyan]")
        console.print(f"[dim]Directory: {self.mod_dir}[/dim]")
        console.print("[dim]Press Ctrl+C to stop watching.[/dim]\n")

        last_mtimes = self._get_mtimes()
        iteration = 0

        try:
            while max_iterations is None or iteration < max_iterations:
                time.sleep(self.poll_interval)
                current_mtimes = self._get_mtimes()

                # Check if any file was modified or added
                changed = False
                for p, mtime in current_mtimes.items():
                    if p not in last_mtimes or mtime > last_mtimes[p]:
                        changed = True
                        break

                if changed:
                    self.run_once()
                    last_mtimes = current_mtimes

                iteration += 1
        except KeyboardInterrupt:
            console.print("\n[dim]Watcher stopped.[/dim]")
