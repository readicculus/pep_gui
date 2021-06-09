import os


def shell_source(setup_viame_path):
    '''
    Runs setup_viame.sh and returns the below environment variables produced in the subprocess which can then
    be set for the current or other processes that use viame or kwiver apis.
    '''
    # TODO: windows compatibility
    import subprocess
    kwiver_env_variables = ['PYTHONPATH', 'PYTHON_LIBRARY', 'QT_PLUGIN_PATH', 'VG_PLUGIN_PATH', 'VIDTK_MODULE_PATH',
                            'SPROKIT_MODULE_PATH', 'KWIVER_PLUGIN_PATH', 'VIAME_INSTALL', 'SPROKIT_PYTHON_MODULES',
                            'KWIVER_DEFAULT_LOG_LEVEL', 'CUDA_INSTALL_DIR', 'LD_LIBRARY_PATH', 'PATH']
    pipe = subprocess.Popen("source %s; env" % setup_viame_path, stdout=subprocess.PIPE, shell=True,
                            executable="/bin/bash")
    output = pipe.communicate()[0].decode('utf-8').split('\n')
    env_kwiver = {}
    for o in output:
        kv = o.split('=')
        if len(o) > 0 and len(kv) == 2:
            if kv[0] in kwiver_env_variables:
                env_kwiver[kv[0]] = kv[1]
    return env_kwiver

def set_env(env_dict):
    import sys
    for path in env_dict['PYTHONPATH'].split(':'):
        if not path in sys.path:
            sys.path.insert(0, path)
    for k, v in env_dict.items():
        os.environ[k] = v

#
# @contextmanager
# def kwiver_environment(setup_viame_path):
#     """Temporarily set environment variables inside the context manager and
#     fully restore previous environment afterwards
#     """
#     original_env = os.environ
#     new_env = shell_source(setup_viame_path)
#     os.environ.update(new_env)
#     try:
#         yield
#     finally:
#         # set environment back to original
#         for key, value in original_env.items():
#             if value is None:
#                 del os.environ[key]
#             else:
#                 os.environ[key] = value