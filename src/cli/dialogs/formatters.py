from prompt_toolkit.shortcuts.progress_bar import formatters

rainbow_progress_bar = [
    formatters.Label(),
    formatters.Text(" "),
    formatters.Rainbow(formatters.Bar()),
    formatters.Text(" left: "),
    formatters.Rainbow(formatters.TimeLeft()),
]