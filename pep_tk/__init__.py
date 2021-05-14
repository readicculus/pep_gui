import os

from pep_tk.kwiver import shell_source, set_env

PLUGIN_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
# VIAME_INSTALL = "/data/software/viame-build/build/install/"
VIAME_INSTALL = "/data/software/seal_tk/"


def setup_env(viame_install: str, plugin_path: str):
    ''' Set correct kwiver environment/PYTHONPATH '''
    # get the viame environemnt
    new_env = shell_source(os.path.join(viame_install, 'setup_viame.sh'))

    # append this tool's dependencies to the PYTHONPATH
    local_site_packages = os.path.join(plugin_path, 'lib', 'python3.6', 'site-packages')
    if 'PYTHONPATH' in new_env:
        new_env['PYTHONPATH'] = ('%s:%s' % (new_env['PYTHONPATH'], local_site_packages))
    else:
        new_env['PYTHONPATH'] = local_site_packages

    # set the environment
    set_env(new_env)

setup_env(VIAME_INSTALL, PLUGIN_PATH)

