from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QDir
from qgis.core import QgsPrintLayout
from .icons import icon

IMAGE_FORMATS = ['png', 'jpg', 'jpeg', 'bmp', 'tif', 'tiff', 'webp', 'ppm', 'xpm', 'xbm', 'pbm', 'pgm']


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
        copyToClipboardAction = None
        exportMenu = None
        exportPDFAction = None
        exportImageAction = None
        exportSvgAction = None
        
        # Context menu if no layout is selected
        if len(selectedLayouts) == 0: 
            newLayoutAction = menu.addAction(icon('mActionNewLayout.svg'), "New Print Layout")
            menu.addSeparator()
            exportMenu = menu.addMenu("Export All Layouts as...")
            exportPDFAction = exportMenu.addAction(icon('mActionSaveAsPDF.svg'), "Export as PDF")
            exportImageAction = exportMenu.addAction(icon('mActionSaveMapAsImage.svg'), "Export as Image")
            exportSvgAction = exportMenu.addAction(icon('mActionSaveAsSVG.svg'), "Export as SVG")
                
        # Context menu if only one layout is selected
        elif len(selectedLayouts) == 1:
            openAction = menu.addAction(icon('mIconLayout.svg'), "Open Layout")
            duplicateAction = menu.addAction(icon('mActionNewLayout.svg'), "Duplicate Layout")
            renameAction = menu.addAction(icon('mActionRename.svg'),"Rename Layout")
            removeAction = menu.addAction(icon('mActionDeleteSelected.svg'),"Remove Layout...")
            # Reports only support open, duplicate, rename and remove
            layout = self.parent.layout_item.layoutByName(selectedLayouts[0].text())
            if isinstance(layout, QgsPrintLayout):
                menu.addSeparator()
                saveAsTemplateAction = menu.addAction(icon('mActionSaveLayoutTemplate.svg'), "Save Layout as Template...")
                menu.addSeparator()
                shareToMenu=menu.addMenu("Share to...")
                copyToClipboardAction = shareToMenu.addAction( "Copy to clipboard")
                exportMenu=menu.addMenu("Export Layout as...")
                exportPDFAction = exportMenu.addAction(icon('mActionSaveAsPDF.svg'), "Export as PDF")
                exportImageAction = exportMenu.addAction(icon('mActionSaveMapAsImage.svg'), "Export as Image")
                exportSvgAction = exportMenu.addAction(icon('mActionSaveAsSVG.svg'), "Export as SVG")

        # Context menu if multiple layouts are selected
        else:
            duplicateAction = menu.addAction(icon('mActionNewLayout.svg'),"Duplicate Layouts")
            removeAction = menu.addAction(icon('mActionDeleteSelected.svg'), "Remove Layouts...")
            menu.addSeparator()
            exportMenu = menu.addMenu("Export Layouts as...")
            exportPDFAction = exportMenu.addAction(icon('mActionSaveAsPDF.svg'), "Export as PDF")
            exportImageAction = exportMenu.addAction(icon('mActionSaveMapAsImage.svg'), "Export as Image")
            exportSvgAction = exportMenu.addAction(icon('mActionSaveAsSVG.svg'),"Export as SVG")
        
        action = menu.exec(self.parent.listWidget.mapToGlobal(position))
        if action == None: return
            
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
        elif action == copyToClipboardAction :
            self.copyToClipboard()
        elif action == exportPDFAction:
            self.exportSelectedLayouts("PDF")
        elif action == exportImageAction:
            self.exportSelectedLayouts("IMG")
        elif action == exportSvgAction:
            self.exportSelectedLayouts("SVG")
        else:
            return


    def copyToClipboard(self):
        """Copy selected layout to clipboard"""
        layout = self.parent.layout_item.layoutByName(self.parent.listWidget.selectedItems()[0].text())
        self.parent.layout_item.copyToClipboard(layout)


    def exportSelectedLayouts(self, format):
        """Export selected layouts, or all layouts if nothing is selected"""

        if format == "PDF":
            default_extension = '.pdf'
            extension_filter = 'PDF files (*.pdf *.PDF)'
            default_filter = 'PDF files (*.pdf *.PDF)'
        elif format == "IMG":
            default_extension = '.png'
            extension_filter = ';;'.join(f'{fmt.upper()} format (*.{fmt} *.{fmt.upper()})' for fmt in IMAGE_FORMATS)
            default_filter = 'PNG format (*.png *.PNG)'
        elif format == "SVG":
            default_extension = '.svg'
            extension_filter = 'SVG format (*.svg *.SVG)'
            default_filter = 'SVG format (*.svg *.SVG)'
        else:
            return

        last_used_folder = self.parent.project.getLastUsedFolder()
        selected_items = self.parent.listWidget.selectedItems()
        if selected_items:
            layout_names = [item.text() for item in selected_items]
        else:
            layout_names = [self.parent.listWidget.item(row).text() for row in range(self.parent.listWidget.count())]

        # Reports cannot be exported with QgsLayoutExporter
        layouts = []
        skipped = []
        for layout_name in layout_names:
            layout = self.parent.layout_item.layoutByName(layout_name)
            if isinstance(layout, QgsPrintLayout):
                layouts.append(layout)
            else:
                skipped.append(layout_name)
        if skipped:
            self.parent.iface.messageBar().pushWarning('Export layout', 'Reports cannot be exported from the panel: ' + ', '.join(skipped))
        if not layouts:
            return

        # A single layout: ask for a file name
        if len(selected_items) == 1:
            file_name = QtWidgets.QFileDialog.getSaveFileName(self.parent, 'Choose a file name to export the layout',
                                                              QDir(last_used_folder).filePath(layouts[0].name() + default_extension),
                                                              extension_filter, default_filter)[0]
            if file_name == '':
                return
            self.parent.project.setLastExportDir(file_name)
            jobs = [(layouts[0], file_name)]

        # Several layouts: ask for a destination folder
        else:
            dir_name = QtWidgets.QFileDialog.getExistingDirectory(self.parent, 'Choose folder to save multiple files',
                                                                  last_used_folder, QtWidgets.QFileDialog.Option.ShowDirsOnly)
            if dir_name == '':
                return
            self.parent.project.setLastExportDir(dir_name)
            jobs = [(layout, QDir(dir_name).filePath(layout.name() + default_extension)) for layout in layouts]

        self.parent.layout_item.exportLayouts(jobs, format)
