from pathlib import Path

import appdirs

user_data_dir = Path(appdirs.user_data_dir("this_is_editor", "small-hsn"))
user_config_dir = Path(appdirs.user_config_dir("this_is_editor", "small-hsn"))

if not Path(user_config_dir).exists():
    Path(user_config_dir).mkdir(parents=True, exist_ok=True)
