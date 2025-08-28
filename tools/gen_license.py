import json
import subprocess
from pathlib import Path

licenses_p = Path("LICENSES")
if not licenses_p.exists():
    licenses_p.mkdir(exist_ok=True)
# pip
text = subprocess.check_output(
    ["uv", "run", "pip-licenses", "--format=json", "--with-license-file"]
)
data = json.loads(text)
for pkg in data:
    name = pkg["Name"]
    license = pkg["License"]

    (licenses_p / f"{name}").write_text(f"{pkg['LicenseFile']}")

# npm
text = subprocess.check_output(["npx", "license-checker", "--json"])
data = json.loads(text)
for key, pkg in data.items():
    name = key.rsplit("@", 1)[0].replace("/", "_")
    # print(name, pkg)
    if "licenseFile" in pkg:
        license_p = Path(pkg["licenseFile"])

        (licenses_p / f"{name}").write_text(license_p.read_text())
    else:
        (licenses_p / f"{name}").write_text(
            f"License: {pkg.get('licenses', 'Unknown')}"
        )
