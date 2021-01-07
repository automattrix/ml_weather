import yaml


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
