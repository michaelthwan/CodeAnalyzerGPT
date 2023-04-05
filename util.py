import os
import yaml


def get_config():
    with open(os.path.join('config/config.yaml'), encoding='utf-8') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    with open(os.path.join('config/config_secret.yaml'), encoding='utf-8') as f:
        config_secret = yaml.load(f, Loader=yaml.FullLoader)
        config.update(config_secret)
    return config
