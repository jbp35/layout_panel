# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LayoutPanel
                                 A QGIS plugin
 Add a panel to manage layouts without blocking the main interface
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2022-02-09
        copyright            : (C) 2022 by Atelier JBP
        email                : jbpeter@outlook.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load LayoutPanel class from file LayoutPanel.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .layout_panel import LayoutPanel
    return LayoutPanel(iface)
