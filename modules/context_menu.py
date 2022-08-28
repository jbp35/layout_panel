from qgis.PyQt import QtGui, QtWidgets


class ContextMenu():
    def __init__(self,parent=None):
        """Initialize the context menu list"""
        self.parent = parent
        
    
    def openContextMenu(self, position):
        """Create the contextual menu for the layout widgetlist"""
        selectedLayouts = self.parent.listWidget.selectedItems()
        if len(selectedLayouts) == 0: # Context menu if no layout is selected
            menu = QtWidgets.QMenu()
            newLayoutAction = menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionNewLayout.svg"), "New Print Layout")
            menu.addSeparator()
            exportMenu = menu.addMenu("Export All Layouts as...")
            exportPDFAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveAsPDF.svg"), "Export as PDF")
            exportImageAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveMapAsImage.svg"), "Export as Image")
            exportSvgAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveAsSVG.svg"), "Export as SVG")
            action = menu.exec_(self.parent.listWidget.mapToGlobal(position))
            if action == newLayoutAction:
                self.parent.layout_item.createNewLayout()
            elif action == exportPDFAction:
                self.parent.layout_item.exportLayoutPDF()
            elif action == exportImageAction:
                self.parent.layout_item.exportLayoutImage()
            elif action == exportSvgAction:
                self.parent.layout_item.exportLayoutSvg()

        elif len(selectedLayouts) == 1: # Context menu if only one layout is selected
            menu = QtWidgets.QMenu()
            openAction = menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mIconLayout.svg"), "Open Layout")
            duplicateAction = menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionNewLayout.svg"), "Duplicate Layout")
            renameAction = menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionRename.svg"),"Rename Layout")
            removeAction = menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionDeleteSelected.svg"),"Remove Layout...")
            menu.addSeparator()
            saveAsTemplateAction = menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveLayoutTemplate.svg"), "Save Layout as Template...")
            menu.addSeparator()
            exportMenu=menu.addMenu("Export Layout as...")
            exportPDFAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveAsPDF.svg"), "Export as PDF")
            exportImageAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveMapAsImage.svg"), "Export as Image")
            exportSvgAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveAsSVG.svg"), "Export as SVG")
            action = menu.exec_(self.parent.listWidget.mapToGlobal(position))
            if action == removeAction:
                self.parent.layout_item.removeSelectedLayouts()
            elif action == openAction:
                self.parent.layout_item.openCurrentLayout()
            elif action == duplicateAction:
                self.parent.layout_item.duplicateLayout()
            elif action == renameAction:
                self.parent.layout_item.renameLayout()
            elif action == saveAsTemplateAction:
                self.parent.layout_item.saveAsTemplate()
            elif action == exportPDFAction:
                self.parent.layout_item.exportLayoutPDF()
            elif action == exportImageAction:
                self.parent.layout_item.exportLayoutImage()
            elif action == exportSvgAction:
                self.parent.layout_item.exportLayoutSvg()
            else:
                print("Code not found")

        else: # Context menu if multiple layouts are selected
            menu = QtWidgets.QMenu()
            duplicateAction = menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionNewLayout.svg"),"Duplicate Layouts")
            removeAction = menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionDeleteSelected.svg"), "Remove Layouts...")
            menu.addSeparator()
            exportMenu = menu.addMenu("Export Layouts as...")
            exportPDFAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveAsPDF.svg"), "Export as PDF")
            exportImageAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveMapAsImage.svg"), "Export as Image")
            exportSvgAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveAsSVG.svg"),"Export as SVG")
            action = menu.exec_(self.parent.listWidget.mapToGlobal(position))
            if action == removeAction:
                self.parent.layout_item.removeSelectedLayouts()
            elif action == duplicateAction:
                self.parent.layout_item.duplicateLayout()
            elif action == exportPDFAction:
                self.parent.layout_item.exportLayoutPDF()
            elif action == exportImageAction:
                self.parent.layout_item.exportLayoutImage()
            elif action == exportSvgAction:
                self.parent.layout_item.exportLayoutSvg()
            else:
                return