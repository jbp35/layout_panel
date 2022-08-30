from qgis.PyQt import QtGui, QtWidgets
from qgis.PyQt.QtCore import  QDir


class ContextMenu():
    def __init__(self,parent=None):
        """Initialize the context menu list"""
        self.parent = parent
        
    
    def openContextMenu(self, position):
        """Create the contextual menu for the layout widgetlist"""
        selectedLayouts = self.parent.listWidget.selectedItems()
        menu = QtWidgets.QMenu()
        
        newLayoutAction = None
        openAction = None
        duplicateAction = None
        renameAction = None
        removeAction = None
        saveAsTemplateAction = None
        exportMenu = None
        exportPDFAction = None
        exportImageAction = None
        exportSvgAction = None
        
        # Context menu if no layout is selected
        if len(selectedLayouts) == 0: 
            newLayoutAction = menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionNewLayout.svg"), "New Print Layout")
            menu.addSeparator()
            exportMenu = menu.addMenu("Export All Layouts as...")
            exportPDFAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveAsPDF.svg"), "Export as PDF")
            exportImageAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveMapAsImage.svg"), "Export as Image")
            exportSvgAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveAsSVG.svg"), "Export as SVG")
                
        # Context menu if only one layout is selected
        elif len(selectedLayouts) == 1:
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

        # Context menu if multiple layouts are selected
        else:
            duplicateAction = menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionNewLayout.svg"),"Duplicate Layouts")
            removeAction = menu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionDeleteSelected.svg"), "Remove Layouts...")
            menu.addSeparator()
            exportMenu = menu.addMenu("Export Layouts as...")
            exportPDFAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveAsPDF.svg"), "Export as PDF")
            exportImageAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveMapAsImage.svg"), "Export as Image")
            exportSvgAction = exportMenu.addAction(QtGui.QIcon(":/plugins/layout_panel/icons/mActionSaveAsSVG.svg"),"Export as SVG")
        
        action = menu.exec_(self.parent.listWidget.mapToGlobal(position))
            
        if action == newLayoutAction:
            self.parent.project.createNewLayout()
        elif action == removeAction:
            self.parent.layout_list.removeSelectedLayouts()
        elif action == openAction:
            self.parent.layout_item.openCurrentLayout()
        elif action == duplicateAction:
            self.parent.layout_list.duplicateSelectedLayouts()
        elif action == renameAction:
            self.parent.layout_item.renameLayout()
        elif action == saveAsTemplateAction:
            self.parent.layout_item.saveAsTemplate()
        elif action == exportPDFAction:
            self.exportSelectedLayouts("PDF")
        elif action == exportImageAction:
            self.exportSelectedLayouts("IMG")
        elif action == exportSvgAction:
            self.exportSelectedLayouts("SVG")
        else:
            return

             
    def exportSelectedLayouts(self, format):
        """Export selected layouts"""
        
        if format == "PDF":
            default_extension = '.pdf'
            extension_filter = 'PDF files (*.pdf *.PDF)'
            default_filter = 'PDF files (*.pdf *.PDF)'
        elif format == "IMG":
            default_extension = '.png'
            extension_filter = 'PNG format (*.png *.PNG);;BMP format (*.bmp *.BMP);;CUR format (*.cur *.CUR);;ICNS format (*.icns *.ICNS);;ICO format (*.ico *.ICO)' \
                            'JPEG format (*.jpeg *.JPEG);;JPG format (*.jpg *.JPG);;PBM format (*.pbm *.PBM);;PGM format (*.pgm *.PGM);;PPM format (*.ppm *.PPM)' \
                            'TIF format (*.tif *.TIF);;TIFF format (*.tiff *.TIFF);;WBMP format (*.wbmp *.WBMP);;WEBP format (*.webp *.WEBP);;WBM format (*.wbm *.XBM);;XPM format (*.xpm *.XPM)'
            default_filter = 'PNG format (*.png *.PNG)'
        elif format == "SVG":
            default_extension = '.svg'
            extension_filter = 'SVG format (*.svg *.SVG)'
            default_filter = 'SVG format (*.svg *.SVG)'  
        else: return
        
        layout_manager= self.parent.project.getLayoutManager()
        last_used_folder=self.parent.project.getLastUsedFolder()
        layoutList = []
        selectedLayouts = self.parent.listWidget.selectedItems()
        
        # If nothing is selected, ask for destination folder and export all layouts
        if len(selectedLayouts) == 0:
            for layoutId in range(self.parent.listWidget.count()):
                layoutList.append(layout_manager.layoutByName(self.parent.listWidget.item(layoutId).text()))
            dir_name = QtWidgets.QFileDialog.getExistingDirectory(self.parent, 'Choose folder to save multiple files',
                                                               last_used_folder,QtWidgets.QFileDialog.ShowDirsOnly)
            if dir_name == '' : return
            self.parent.project.setLastExportDir(dir_name)
        
        # If only one layout is selected, ask file name and export layout
        elif len(selectedLayouts) == 1:  
            layout = (layout_manager.layoutByName(selectedLayouts[0].text()))
            layoutList.append(layout)
            file_name = QtWidgets.QFileDialog.getSaveFileName(self.parent, 'Choose a file name to save the layout as SVG',
                                                          QDir(last_used_folder).filePath(layout.name() + default_extension), extension_filter, default_filter)[0]
            if file_name == '' : return
            self.parent.project.setLastExportDir(file_name)
            
        # Multiple selection, ask for destination folder and export selected layouts
        else: 
            for layout in selectedLayouts:
                layoutList.append(layout_manager.layoutByName(layout.text()))
            dir_name = QtWidgets.QFileDialog.getExistingDirectory(self.parent, 'Choose folder to save multiple files',
                                                               last_used_folder,QtWidgets.QFileDialog.ShowDirsOnly)
            
            if dir_name == '' : return 
            self.parent.project.setLastExportDir(dir_name)
        
        # Export the layouts one by one       
        for layout in layoutList:
            if len(selectedLayouts) != 1: 
                file_name = QDir(dir_name).filePath(layout.name() + default_extension) 
            self.parent.layout_item.exportLayout(layout,file_name, format)
