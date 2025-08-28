from pathlib import Path

import appdirs

user_data_dir = Path(appdirs.user_data_dir("this_is_editor", "hsn8086"))
user_config_dir = Path(appdirs.user_config_dir("this_is_editor", "hsn8086"))
user_log_dir = Path(appdirs.user_log_dir("this_is_editor", "hsn8086"))

if not user_config_dir.exists():
    user_config_dir.mkdir(parents=True, exist_ok=True)
if not user_data_dir.exists():
    user_data_dir.mkdir(parents=True, exist_ok=True)
if not user_log_dir.exists():
    user_log_dir.mkdir(parents=True, exist_ok=True)
