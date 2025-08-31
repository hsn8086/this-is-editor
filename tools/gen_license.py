"""Generates license files for Python and Node.js dependencies.

It uses `pip-licenses` for Python packages and `license-checker` for Node.js packages
to extract license information and save it in a structured format.
"""

import json
import shlex
import subprocess
from pathlib import Path

licenses_p = Path("LICENSES")
if not licenses_p.exists():
    licenses_p.mkdir(exist_ok=True)
# pip
text = subprocess.check_output(
    shlex.join(["uv", "run", "pip-licenses", "--format=json", "--with-license-file"]),
    shell=True,
)
data = json.loads(text)
for pkg in data:
    name = pkg["Name"]

    (licenses_p / f"{name}").write_text(f"{pkg['LicenseFile']}")

# npm
text = subprocess.check_output(
    shlex.join(["npx", "license-checker", "--json"]), shell=True,
)
data = json.loads(text)
for key, pkg in data.items():
    name = key.rsplit("@", 1)[0].replace("/", "_")
    if "licenseFile" in pkg:
        license_p = Path(pkg["licenseFile"])

        (licenses_p / f"{name}").write_text(
            license_p.read_text(encoding="utf-8"), encoding="utf-8",
        )
    else:
        (licenses_p / f"{name}").write_text(
            f"License: {pkg.get('licenses', 'Unknown')}",
        )
