# -*- coding: utf-8 -*-
"""Translate the plugin in the language of the QGIS user interface.

Translations live in the i18n/ folder: layout_panel_<language>.ts are the
sources edited with Qt Linguist, layout_panel_<language>.qm the compiled
files loaded at runtime (see scripts/translations.py in the repository).
"""

import os

from qgis.PyQt.QtCore import QCoreApplication, QTranslator
from qgis.core import QgsApplication

CONTEXT = 'LayoutPanel'
I18N_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'i18n')


def tr(text, context=CONTEXT):
    """Return the translation of a text of the plugin.

    A different context lets the same English text get another translation,
    e.g. a short menu entry and the longer name of its keyboard shortcut.
    """
    return QCoreApplication.translate(context, text)


def trNoop(text, context=CONTEXT):
    """Mark a text for translation without translating it yet (translate it later with tr)"""
    return text


def installTranslator():
    """Install the translation matching the QGIS locale, if the plugin has one.

    :returns: the installed translator, to remove when the plugin is unloaded, or None
    :rtype: QTranslator
    """
    # QGIS locale, e.g. 'fr_FR' or 'de': the language set in Settings > Options > General
    language = QgsApplication.locale()[:2]
    path = os.path.join(I18N_DIR, f'layout_panel_{language}.qm')
    if not os.path.exists(path):
        return None
    translator = QTranslator()
    if not translator.load(path):
        return None
    QCoreApplication.installTranslator(translator)
    return translator


def removeTranslator(translator):
    if translator is not None:
        QCoreApplication.removeTranslator(translator)
