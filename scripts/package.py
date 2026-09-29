"""Build the zip to upload to plugins.qgis.org.

Only the ``layout_panel/`` folder is shipped. Usage::

    python scripts/package.py            # -> dist/layout_panel-<version>.zip
"""
import configparser
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "layout_panel"
EXCLUDED_DIRS = {"__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def main():
    metadata = configparser.ConfigParser(interpolation=None)
    metadata.read(PLUGIN_DIR / "metadata.txt", encoding="utf-8")
    version = metadata["general"]["version"]

    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    zip_path = dist / f"layout_panel-{version}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PLUGIN_DIR.rglob("*")):
            relative = path.relative_to(PLUGIN_DIR)
            if path.is_dir() or path.suffix in EXCLUDED_SUFFIXES:
                continue
            if EXCLUDED_DIRS.intersection(relative.parts):
                continue
            archive.write(path, pathlib.Path("layout_panel") / relative)

    print(f"Created {zip_path}")


if __name__ == "__main__":
    main()
