import os
__version__ = "N/A"
PLUGIN_PATH = os.path.normpath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

version_txt_fp = os.path.join(os.path.dirname(__file__), 'VERSION.txt')
with open(version_txt_fp, 'r') as file:
    v_data = file.read().replace('\n', '')
if len(v_data.split('.')) == 3:
    __version__ = v_data
else:
    print(f'Invalid VERSION.cfg - could not parse {v_data}')