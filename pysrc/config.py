import json

from pysrc.user_data import user_config_dir

from .config_meta import config as cfg


def merge_meta(cfg_meta: dict, config: dict) -> dict:
    merged = {}
    for key, value in cfg_meta.items():
        if "display" in value:
            merged[key] = {"value": config.get(key, None)}
            merged[key].update(value)
        else:
            merged[key] = merge_meta(value, config.get(key, {}))
    return merged


def merge(a: dict, b: dict) -> dict:
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
