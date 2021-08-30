#      This file is part of the PEP GUI detection pipeline batch running tool
#      Copyright (C) 2021 Yuval Boss yuval@uw.edu
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
