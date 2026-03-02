"""Rich terminal dashboard for the Ouroboros Cathedral."""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List

from .runner import CathedralRunner


class TerminalDashboard:
    """
    Runs a ``CathedralRunner`` in a background thread and displays a live
    Rich terminal dashboard that refreshes at ~2 Hz.
    """

    def __init__(self, num_entities: int = 17) -> None:
        self.num_entities = num_entities
        self._runner = CathedralRunner(num_entities=num_entities, mode="terminal")
        self._stop_event = threading.Event()

    def run(self) -> None:
        try:
            from rich.live import Live
            from rich.layout import Layout
            from rich.panel import Panel
            from rich.table import Table
            from rich.text import Text
        except ImportError:
            print("The 'rich' package is required for the dashboard.")
            print("Install it with:  pip install rich")
            return

        runner_thread = threading.Thread(target=self._runner.run, daemon=True)
        runner_thread.start()

        # Wait briefly for the runner to initialise
        time.sleep(0.5)

        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )
        layout["body"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="entities", ratio=2),
        )

        try:
            with Live(layout, refresh_per_second=2, screen=True):
                while not self._stop_event.is_set() and self._runner._running:
                    layout["header"].update(
                        Panel(
                            Text("✦ Ouroboros Cathedral ✦", justify="center", style="bold magenta"),
                            style="bold magenta",
                        )
                    )
                    layout["stats"].update(self._build_stats_panel())
                    layout["entities"].update(self._build_entity_table())
                    layout["footer"].update(
                        Panel(
                            Text("Inhale the 15. Exhale the 1.", justify="center", style="italic cyan"),
                            style="cyan",
                        )
                    )
                    time.sleep(0.5)
        except KeyboardInterrupt:
            self._runner._running = False

        runner_thread.join(timeout=3)

    def _build_stats_panel(self) -> Any:
        from rich.panel import Panel
        from rich.table import Table

        stats = self._runner.get_stats()
        table = Table.grid(padding=(0, 1))
        table.add_column(style="bold cyan")
        table.add_column(style="white")

        table.add_row("Active entities", str(stats.get("tiamat_count", 0)))
        table.add_row("Reached Monad", str(stats.get("monad_count", 0)))
        table.add_row("Vetoed", str(stats.get("vetoed_count", 0)))
        table.add_row("Total ticks", str(stats.get("ticks", 0)))
        table.add_row("Pulse frequency", f"{stats.get('frequency', 417.0):.1f} Hz")
        table.add_row("Elapsed", f"{stats.get('elapsed', 0.0):.1f}s")

        return Panel(table, title="[bold]Stats[/bold]", border_style="green")

    def _build_entity_table(self) -> Any:
        from rich.panel import Panel
        from rich.table import Table

        table = Table(show_header=True, header_style="bold blue", expand=True)
        table.add_column("ID", style="dim", width=12)
        table.add_column("Layer", width=6)
        table.add_column("Word", width=18)
        table.add_column("Vitality", width=10)
        table.add_column("Divergence", width=12)
        table.add_column("Status", width=14)

        states: List[Dict[str, Any]] = self._runner.get_entity_states()
        for state in states:
            pal = state.get("palindrome", {})
            layer = pal.get("layer", "?")
            word = pal.get("word", "")
            vitality = pal.get("vitality", 0.0)
            divergence = pal.get("vitality_divergence", 0.0)
            symmetry = pal.get("symmetry_verified", False)
            at_threshold = isinstance(layer, int) and layer == 6

            if symmetry or (isinstance(layer, int) and layer >= 7):
                status = "[green]MONAD[/green]"
            elif at_threshold:
                status = "[yellow]THRESHOLD[/yellow]"
            else:
                status = "[cyan]DESCENDING[/cyan]"

            table.add_row(
                str(state.get("entity_id", ""))[:10],
                str(layer),
                word[:16],
                f"{vitality:.3f}",
                f"{divergence:.4f}",
                status,
            )

        return Panel(table, title="[bold]Entities[/bold]", border_style="blue")
