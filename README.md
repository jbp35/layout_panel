# Layout Panel Plugin

This plugin adds a new panel to manage print layouts directly from QGIS main window. It allows to quickly open, create, rename, delete and filter print layouts without having to open the layout manager. It supports layout templates and also makes it possible to batch export one or multiple layouts to PDF, Image or SVG formats without having to open each print layout.

## Repository layout

- `layout_panel/`: the plugin itself. This is the only folder shipped to users.
- `scripts/`: development scripts, not shipped.
- `test/`: tests, not shipped.

## Development

Link the plugin folder into your QGIS profile so QGIS loads it straight from the repository (Windows, QGIS 4):

```
mklink /J "%APPDATA%\QGIS\QGIS4\profiles\default\python\plugins\layout_panel" "C:\path\to\repo\layout_panel"
```

On Linux/macOS use `ln -s` to the equivalent `python/plugins` folder.

## Translations

The plugin follows the language of the QGIS interface (Settings > Options > General) and is translated into French, Spanish and German. Sources are in `layout_panel/i18n/*.ts`, compiled to the `.qm` files QGIS loads. In the code, wrap user-facing texts with `tr()` from `modules/i18n.py`, then:

```
python scripts/translations.py update   # add new texts to the .ts files
python scripts/translations.py compile  # rebuild the .qm files
```

Translate the new entries (Qt Linguist or a text editor) before compiling, and commit both the `.ts` and `.qm` files: the packaged plugin ships the committed `.qm` files. To add a language, add it to `LANGUAGES` in the script.

## Publishing

Publishing a GitHub release runs `.github/workflows/release.yml`, which uses [qgis-plugin-ci](https://github.com/opengisch/qgis-plugin-ci) to package the `layout_panel/` folder (see `.qgis-plugin-ci`) and upload it to plugins.qgis.org. The release tag becomes the plugin version.

To build the zip locally: `qgis-plugin-ci package <version>`.
