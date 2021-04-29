from functools import partial
from textwrap import wrap
from typing import Optional, Tuple, Dict

from prompt_toolkit.application import Application, get_app
from prompt_toolkit.filters import IsDone
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import ConditionalContainer, HSplit, Window, VSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.mouse_events import MouseEventType
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, Button, Box

from src.config.parser import ConfigOption, PipelineGlobalConfig

OptionValue = Optional[AnyFormattedText]
Option = Dict[
    AnyFormattedText,  # name value is same
    AnyFormattedText  # (name, value)
]
IndexedOption = Tuple[
    int,  # index
    AnyFormattedText,  # name
    OptionValue
]


class ConfigPromptSelectionControl(FormattedTextControl):
    def __init__(
            self,
            global_config: PipelineGlobalConfig,
            **kwargs
    ) -> None:
        self.global_config = global_config
        self.config_index = {i: k for i, (k,v) in enumerate(global_config.get_config().items())}
        self.selected_option_index = 0
        super().__init__(**kwargs)

    @property
    def selected_option(self) -> ConfigOption:
        return self.config_index[self.selected_option_index]

    @property
    def options_count(self) -> int:
        return len(self.global_config)



    def _select_option(self, index, text_area):

        def handler(mouse_event):
            if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
                get_app().layout.focus(text_area)
                # bind option with this index to mouse event
                self.selected_option_index = index

        return handler

    def format_option(
            self,
            idx,
            option: ConfigOption,
            text_area,
            *,
            selected_style_class: str = '',
            selected_prefix_char: str = '>',
            indent: int = 1
    ):
        option_prefix: AnyFormattedText = ' ' * indent
        name = option.name
        value = str(option.value())
        if self.selected_option_index == idx:
            option_prefix = selected_prefix_char + option_prefix
            return selected_style_class, f'{option_prefix}{name}\n', self._select_option(idx, text_area)

        option_prefix += ' '
        return '', f'{option_prefix}{name}\n', self._select_option(idx, text_area)


    def update_config(self, name, text):
        k = name
        v = text
        success = self.global_config.set_config_option(k, v)
        if not success:
            self.global_config.reset_config_option(k)

    def get_selection_description(self):
        if not self.selected_option_index in self.config_index:
            return []
        selection = self.global_config[self.config_index[self.selected_option_index]]
        if not selection.description:
            return []
        return [('class:description', 'Description\n'),  ('', "\n".join(wrap(selection.description, width=50)))]

class ConfigurationPrompt:
    def __init__(
            self,
            message: AnyFormattedText = "",
            *,
            options: Optional[PipelineGlobalConfig] = None
    ) -> None:
        self.message = message
        self.global_config = options
        self.control = None
        self.layout = None
        self.key_bindings = None
        self.app = None
        self.text_buffers = {}
        self.num_buttons = 0

    def btn_submit(self):
        get_app().exit()

    def btn_reset_defaults(self):
        self.control.global_config.reset_all_defaults()
        for name, buffer in self.text_buffers.items():
            buffer.text = str(self.global_config[name].value())
        self.update()

    def btn_cancel(self):
        self.btn_reset_defaults()
        get_app().exit()

    def _create_layout(self) -> Layout:
        """
        Create `Layout` for this prompt.
        """

        cancel_button = Button("Cancel", handler=partial(self.btn_cancel), width=len("Cancel") + 4)
        button_submit = Button("Submit", handler=partial(self.btn_submit), width=len("Submit") + 4)
        button_reset = Button("Reset Defaults", handler=partial(self.btn_reset_defaults), width=len("Reset Defaults") + 4)
        self.num_buttons = 3

        def callback_factory(idx, m, text_area):
            return lambda: [self.control.format_option(idx, m, text_area, selected_style_class='class:reverse')]

        form = []
        for idx, opt_name in self.control.config_index.items():
            opt = self.control.global_config[opt_name]
            ta = TextArea(text=str(opt.value()))
            ta.buffer.name = opt.name
            self.text_buffers[opt.name] = ta.buffer
            form.append(VSplit([
                Window(
                    height=Dimension.exact(1),
                    width=Dimension.exact(50),
                    content=FormattedTextControl(
                        callback_factory(idx, opt, ta))
                ),
                ta]))

        layout = HSplit([
            Window(
                height=Dimension.exact(2),
                content=FormattedTextControl(
                    lambda: '\n' + self.message + '\n',
                    show_cursor=False
                ),
            ),
            VSplit(
                [
                    HSplit(form),
                    Window(
                        content=FormattedTextControl(self.control.get_selection_description),
                        wrap_lines=True,
                        width=Dimension.exact(60),
                        height=Dimension.exact(len(self.control.config_index))

                    )
                ])
            ,
            Box(
                body=VSplit([cancel_button, button_submit, button_reset], padding=1),
                padding=1,
                style="class:left-pane",
            ),

            ConditionalContainer(
                Window(self.control),
                filter=~IsDone()
            )
        ])
        return Layout(layout)

    def update(self):
        for name, buffer in self.text_buffers.items():
            self.control.update_config(name, buffer.text)
            buffer.text = str(self.global_config[name].value())

    def _create_key_bindings(self) -> KeyBindings:
        """
        Create `KeyBindings` for this prompt
        """
        control = self.control
        kb = KeyBindings()

        @kb.add('c-q', eager=True)
        @kb.add('c-c', eager=True)
        def _(event):
            get_app().exit()

        @kb.add('down', eager=True)
        def move_cursor_down(event):
            self.update()

            control.selected_option_index = (control.selected_option_index + 1) % (control.options_count + self.num_buttons)
            event.app.layout.focus_next()

        @kb.add('up', eager=True)
        def move_cursor_up(event):
            self.update()
            control.selected_option_index = (control.selected_option_index - 1) % (control.options_count + self.num_buttons)
            event.app.layout.focus_previous()

        @kb.add('enter')
        def set_answer(event):
            return
            control.answered = True
            _, _, selected_option_value = self.control.selected_option
            event.app.exit(result=selected_option_value)

        return kb

    def _create_application(self) -> Application:
        """
        Create `Application` for this prompt.
        """
        style = Style.from_dict(
            {
                "status": "reverse",
                'description': 'reverse bold'
            }
        )
        app = Application(
            layout=self.layout,
            key_bindings=self.key_bindings,
            style=style,
            full_screen=False,
            mouse_support=True
        )
        return app

    def prompt(
            self,
            message: Optional[AnyFormattedText] = None
    ):
        # all arguments are overwritten the init arguments in SelectionPrompt.
        if message is not None:
            self.message = message

        if self.app is None:
            self.control = ConfigPromptSelectionControl(self.global_config)
            self.layout = self._create_layout()
            self.key_bindings = self._create_key_bindings()
            self.app = self._create_application()

        return self.app.run()


