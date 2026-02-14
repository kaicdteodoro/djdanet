from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.text import Text

from app.domain.entities import DownloadResult
from app.domain.protocols import ProgressCallback

console = Console(stderr=True)


class RichProgressCallback(ProgressCallback):
    """Progress callback implementation using Rich library."""

    def __init__(self) -> None:
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        self._task_id: int | None = None
        self._started = False

    def start(self) -> None:
        """Starts the progress display."""
        self._progress.start()
        self._task_id = self._progress.add_task("Downloading...", total=None)
        self._started = True

    def stop(self) -> None:
        """Stops the progress display."""
        if self._started:
            self._progress.stop()
            self._started = False

    def on_progress(self, downloaded_bytes: int, total_bytes: int | None) -> None:
        """Updates the progress bar with current download state.

        Args:
            downloaded_bytes: Number of bytes downloaded so far.
            total_bytes: Total file size in bytes, or None if unknown.
        """
        if self._task_id is not None:
            self._progress.update(
                self._task_id,
                completed=downloaded_bytes,
                total=total_bytes,
            )

    def on_status(self, message: str) -> None:
        """Updates the progress description with a status message.

        Args:
            message: The status message to display.
        """
        if self._task_id is not None:
            self._progress.update(self._task_id, description=message)


def print_header() -> None:
    """Prints the application header banner."""
    title = Text("djdanet", style="bold magenta")
    subtitle = Text("YouTube Downloader", style="dim")
    header = Text.assemble(title, " - ", subtitle)
    console.print(Panel(header, border_style="magenta", padding=(0, 2)))


def print_success(result: DownloadResult) -> None:
    """Prints a success message with download details.

    Args:
        result: The completed download result.
    """
    size_str = _format_file_size(result.file_size_bytes)
    console.print()
    console.print(
        Panel(
            f"[bold green]Download completed![/bold green]\n\n"
            f"[bold]Title:[/bold] {result.video.title}\n"
            f"[bold]Format:[/bold] {result.output_format.value.upper()}\n"
            f"[bold]Size:[/bold] {size_str}\n"
            f"[bold]Path:[/bold] {result.output_path}",
            title="[green]Success[/green]",
            border_style="green",
        )
    )


def print_error(message: str) -> None:
    """Prints an error message.

    Args:
        message: The error message to display.
    """
    console.print(f"\n[bold red]Error:[/bold red] {message}")


def print_info(message: str) -> None:
    """Prints an informational message.

    Args:
        message: The info message to display.
    """
    console.print(f"[dim]{message}[/dim]")


def _format_file_size(size_bytes: int | None) -> str:
    """Formats a file size in bytes to a human-readable string.

    Args:
        size_bytes: The file size in bytes, or None.

    Returns:
        A human-readable size string.
    """
    if size_bytes is None:
        return "Unknown"

    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024  # type: ignore[assignment]

    return f"{size_bytes:.1f} TB"
