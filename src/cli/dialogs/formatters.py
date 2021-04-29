from prompt_toolkit.shortcuts.progress_bar import formatters

rainbow_progress_bar = [
    formatters.Label(),
    formatters.Text(" "),
    formatters.Rainbow(formatters.Bar()),
    formatters.Progress(),
    formatters.Text(" it/s: "),
    formatters.IterationsPerSecond(),
    formatters.Text(" eta: "),
    formatters.Rainbow(formatters.TimeLeft()),
]