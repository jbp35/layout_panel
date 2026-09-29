# -*- coding: utf-8 -*-
"""Load the plugin's icons from the icons/ folder on disk."""

import os

from qgis.PyQt.QtGui import QIcon

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons')


def icon(file_name):
    """Return a QIcon for a file in the plugin's icons/ folder.

    :param file_name: file name relative to the icons/ folder,
        e.g. 'mActionNewLayout.svg'
    :type file_name: str
    :rtype: QIcon
    """
    return QIcon(os.path.join(ICONS_DIR, file_name))
