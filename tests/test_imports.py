from unittest import TestCase
from util import add_src_to_pythonpath

add_src_to_pythonpath()

# noinspection PyUnresolvedReferences
class TestImports(TestCase):
    def test_import_core(self):
        import pep_tk.core

        import pep_tk.core.parser
        import pep_tk.core.parser.pd_parser
        import pep_tk.core.parser.empty_parser
        import pep_tk.core.parser.ini_parser

        import pep_tk.core.configuration
        import pep_tk.core.configuration.configurations
        import pep_tk.core.configuration.pipelines
        import pep_tk.core.configuration.exceptions
        import pep_tk.core.configuration.types

        import pep_tk.core.utilities
        import pep_tk.core.utilities.jsonfile

        import pep_tk.core.kwiver
        import pep_tk.core.kwiver.pipeline_compiler
        import pep_tk.core.kwiver.subprocess_runner

        import pep_tk.core.job
        import pep_tk.core.scheduler

    def test_import_psg(self):
        import pep_tk.psg
        import pep_tk.psg.fonts
        import pep_tk.psg.utils
        import pep_tk.psg.settings

        import pep_tk.psg.layouts.layout
        import pep_tk.psg.layouts.task_progress
        import pep_tk.psg.layouts.pipeline_selection
        import pep_tk.psg.layouts.dataset_selection

        import pep_tk.psg.windows.popups
        import pep_tk.psg.windows.properties
        import pep_tk.psg.windows.create_job
        import pep_tk.psg.windows.job_runner
