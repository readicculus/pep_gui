from prompt_toolkit.completion import Completer, Completion

class DatasetCompleter(Completer):
    def __init__(self, parser):
        self.parser = parser
        self.options = list(parser.get_dataset('*').keys())

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        res = self.parser.get_dataset(text + '*')
        for k in list(res.keys()):
            yield Completion(k, start_position=-len(text))
