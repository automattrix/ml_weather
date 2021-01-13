import yaml
from pathlib import Path
import sys
import os


def set_env(project_path):
    project_path = Path(project_path).expanduser().resolve()
    src_path = str(project_path)
    print(project_path)
    print(src_path)

    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    if "PYTHONPATH" not in os.environ:
        os.environ["PYTHONPATH"] = src_path

    if os.getcwd() != str(project_path):
        print(f"Changing the current working directory to {str(project_path)}")
        os.chdir(str(project_path))  # Move to project root


def load_params():
    """
    Create parameters dictionary from yaml.
    Read base config, override if values defined in ./conf/local/
    :return:
    """
    params_dict = {}

    with open('./conf/base/params.yaml') as p_base:
        params = yaml.load(p_base, Loader=yaml.FullLoader)
        for k, v in params['params']['environment'].items():
            params_dict[k] = v
    p_base.close()

    with open('./conf/local/params.yaml') as p_local:
        params = yaml.load(p_local, Loader=yaml.FullLoader)
        for k, v in params['params']['environment'].items():
            params_dict[k] = v
    p_local.close()

    return params_dict
