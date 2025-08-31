"""Provides configuration utilities.

It includes functions to merge configuration metadata, handle user-specific
configuration files, and initialize the application configuration.
"""

import json

from .config_meta import config as cfg
from .user_data import user_config_dir


def merge_meta(cfg_meta: dict, config: dict) -> dict:
    """Recursively merges metadata from `cfg_meta` from `config`.

    This function traverses the `cfg_meta` dictionary and combines its structure with
    the values from the `config` dictionary. If a key in `cfg_meta` contains the string
    "display" in its value, the function creates a new dictionary for that key, where:
      - The "value" key is set to the corresponding value from `config`.
      - The rest of the metadata from `cfg_meta` is included.

    If "display" is not present in the value, the function recursively merges the
    nested dictionaries.

    Args:
        cfg_meta (dict): The metadata dictionary containing the structure and additional
                         information for each key.
        config (dict): The configuration dictionary containing the actual values to
                       merge with the metadata.

    Returns:
        dict: A new dictionary with the merged metadata and configuration values.

    """
    merged = {}
    for key, value in cfg_meta.items():
        if "display" in value:
            merged[key] = {"value": config.get(key)}
            merged[key].update(value)
        else:
            merged[key] = merge_meta(value, config.get(key, {}))
    return merged


def merge(a: dict, b: dict) -> dict:
    """Recursively merges two dictionaries.

    This function takes two dictionaries, `a` and `b`, and merges the contents
    of `b` into `a`. If a key in `b` corresponds to a dictionary and the same
    key exists in `a` as a dictionary, the function will recursively merge
    those dictionaries. Otherwise, the value from `b` will overwrite the value
    in `a`.

    Args:
        a (dict): The first dictionary to merge into. This dictionary will be
                  modified in place.
        b (dict): The second dictionary whose contents will be merged into `a`.

    Returns:
        dict: The merged dictionary, which is the same as `a` after the merge.

    Example:
        >>> a = {'x': 1, 'y': {'z': 2}}
        >>> b = {'y': {'z': 3, 'w': 4}, 'v': 5}
        >>> merge(a, b)
        {'x': 1, 'y': {'z': 3, 'w': 4}, 'v': 5}

    """
    for key, value in b.items():
        if isinstance(value, dict) and key in a and isinstance(a[key], dict):
            a[key] = merge(a[key], value)
        else:
            a[key] = value
    return a


config_p = user_config_dir / "config.json"
if not config_p.exists():
    config_p.write_text(json.dumps(cfg, indent=4), encoding="utf-8")
config = merge(cfg, json.loads(config_p.read_text(encoding="utf-8")))
