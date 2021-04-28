import os

from src.kwiver import shell_source, set_env

PLUGIN_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIAME_INSTALL = "/data/software/viame-build/build/install/"
SETUP_VIAME = os.path.join(VIAME_INSTALL, 'setup_viame.sh')


new_env = shell_source(os.path.join(VIAME_INSTALL, 'setup_viame.sh'))
set_env(new_env)