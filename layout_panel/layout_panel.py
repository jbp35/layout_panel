# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LayoutPanel
                                 A QGIS plugin
 Add a panel to manage layouts without blocking the main interface
                              -------------------
        begin                : 2022-02-09
        copyright            : (C) 2022 by Atelier JBP
        email                : jbpeter@outlook.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon, QAction

from .layout_panel_dockwidget import LayoutPanelDockWidget

MENU_NAME = '&Layout Panel'


class LayoutPanel:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.pluginIsActive = False
        self.dockwidget = None

    def initGui(self):
        """Create the menu entry, toolbar icon and dock widget."""
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        self.action = QAction(QIcon(icon_path), 'Layout Panel', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(MENU_NAME, self.action)

        if self.dockwidget is None:
            self.dockwidget = LayoutPanelDockWidget(self.iface, self.iface.mainWindow())

        self.dockwidget.closingPlugin.connect(self.onClosePlugin)
        self.iface.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockwidget)

    def onClosePlugin(self):
        """Called when the dock widget is closed"""
        self.pluginIsActive = False

    def unload(self):
        """Remove the plugin menu item and icon from QGIS GUI."""
        self.iface.removePluginMenu(MENU_NAME, self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        """Show the dock widget"""
        if not self.pluginIsActive:
            self.pluginIsActive = True
            self.dockwidget.show()
