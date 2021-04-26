import os
from contextlib import contextmanager

PLUGIN_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIAME_INSTALL = "/data/software/viame-build/build/install/"
SETUP_VIAME = os.path.join(VIAME_INSTALL, 'setup_viame.sh')



#
# new_env = shell_source(os.path.join(VIAME_INSTALL, 'setup_viame.sh'))
# os.environ.update(new_env)

# def set_env(env_dict):
#     ''' Given a dictionary sets the environment variable k to the value v'''
#     for k, v in env_dict.items():
#         os.environ[k] = v

# set_env(new_env)