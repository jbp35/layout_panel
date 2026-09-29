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

from qgis.PyQt import sip
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon, QAction

from .layout_panel_dockwidget import LayoutPanelDockWidget
from .modules.i18n import installTranslator, removeTranslator
from .modules.shortcuts import registerShortcut, unregisterShortcut

MENU_NAME = '&Layout Panel'


class LayoutPanel:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dockwidget = None
        # before any widget is created, so they get the translated texts
        self.translator = installTranslator()

    def initGui(self):
        """Create the menu entry, toolbar icon and dock widget."""
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        self.action = QAction(QIcon(icon_path), 'Layout Panel', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        registerShortcut(self.action, 'mActionLayoutPanel', 'Ctrl+Alt+L')
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(MENU_NAME, self.action)

        if self.dockwidget is None:
            self.dockwidget = LayoutPanelDockWidget(self.iface, self.iface.mainWindow())

        self.iface.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockwidget)

    def unload(self):
        """Remove the plugin menu item, icon and dock widget from QGIS GUI."""
        unregisterShortcut(self.action)
        self.iface.removePluginMenu(MENU_NAME, self.action)
        self.iface.removeToolBarIcon(self.action)
        self.action.deleteLater()
        self.action = None

        if self.dockwidget is not None:
            self.dockwidget.cleanup()
            self.iface.removeDockWidget(self.dockwidget)
            # delete now rather than with deleteLater(): the old panel must be gone
            # before a reload creates the new one (Plugin Reloader flags it otherwise)
            sip.delete(self.dockwidget)
            self.dockwidget = None

        removeTranslator(self.translator)
        self.translator = None

    def run(self):
        """Show the dock widget"""
        self.dockwidget.show()
        self.dockwidget.raise_()
