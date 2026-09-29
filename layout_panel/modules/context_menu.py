from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QDir, QFileInfo
from qgis.core import QgsPrintLayout
from .i18n import tr
from .icons import icon
from .layout_list import FOLDER_PATH_ROLE, folderParts, splitName

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
        newLayoutInFolderAction = None
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
            newLayoutAction = menu.addAction(icon('mActionNewLayout.svg'), tr("New Print Layout"))
            menu.addSeparator()
            exportMenu = menu.addMenu(tr("Export All Layouts as..."))
            exportPDFAction = exportMenu.addAction(icon('mActionSaveAsPDF.svg'), tr("Export as PDF"))
            exportImageAction = exportMenu.addAction(icon('mActionSaveMapAsImage.svg'), tr("Export as Image"))
            exportSvgAction = exportMenu.addAction(icon('mActionSaveAsSVG.svg'), tr("Export as SVG"))
                
        # Context menu if only one folder is selected
        elif len(selectedLayouts) == 1 and selectedLayouts[0].isFolder():
            newLayoutInFolderAction = menu.addAction(icon('mActionNewLayout.svg'), tr("New Print Layout"))
            renameAction = menu.addAction(icon('mActionRename.svg'), tr("Rename Folder"))
            removeAction = menu.addAction(icon('mActionDeleteSelected.svg'), tr("Remove Folder..."))
            menu.addSeparator()
            exportMenu = menu.addMenu(tr("Export Folder as..."))
            exportPDFAction = exportMenu.addAction(icon('mActionSaveAsPDF.svg'), tr("Export as PDF"))
            exportImageAction = exportMenu.addAction(icon('mActionSaveMapAsImage.svg'), tr("Export as Image"))
            exportSvgAction = exportMenu.addAction(icon('mActionSaveAsSVG.svg'), tr("Export as SVG"))

        # Context menu if only one layout is selected
        elif len(selectedLayouts) == 1:
            openAction = menu.addAction(icon('mIconLayout.svg'), tr("Open Layout"))
            duplicateAction = menu.addAction(icon('mActionNewLayout.svg'), tr("Duplicate Layout"))
            renameAction = menu.addAction(icon('mActionRename.svg'),tr("Rename Layout"))
            removeAction = menu.addAction(icon('mActionDeleteSelected.svg'),tr("Remove Layout..."))
            # Reports only support open, duplicate, rename and remove
            layout = self.parent.layout_item.currentLayout()
            if isinstance(layout, QgsPrintLayout):
                menu.addSeparator()
                saveAsTemplateAction = menu.addAction(icon('mActionSaveLayoutTemplate.svg'), tr("Save Layout as Template..."))
                menu.addSeparator()
                shareToMenu=menu.addMenu(tr("Share to..."))
                copyToClipboardAction = shareToMenu.addAction(tr("Copy to clipboard"))
                exportMenu=menu.addMenu(tr("Export Layout as..."))
                exportPDFAction = exportMenu.addAction(icon('mActionSaveAsPDF.svg'), tr("Export as PDF"))
                exportImageAction = exportMenu.addAction(icon('mActionSaveMapAsImage.svg'), tr("Export as Image"))
                exportSvgAction = exportMenu.addAction(icon('mActionSaveAsSVG.svg'), tr("Export as SVG"))

        # Context menu if multiple layouts are selected
        else:
            duplicateAction = menu.addAction(icon('mActionNewLayout.svg'),tr("Duplicate Layouts"))
            removeAction = menu.addAction(icon('mActionDeleteSelected.svg'), tr("Remove Layouts..."))
            menu.addSeparator()
            exportMenu = menu.addMenu(tr("Export Layouts as..."))
            exportPDFAction = exportMenu.addAction(icon('mActionSaveAsPDF.svg'), tr("Export as PDF"))
            exportImageAction = exportMenu.addAction(icon('mActionSaveMapAsImage.svg'), tr("Export as Image"))
            exportSvgAction = exportMenu.addAction(icon('mActionSaveAsSVG.svg'), tr("Export as SVG"))
        
        action = menu.exec(self.parent.listWidget.mapToGlobal(position))
        if action == None: return
            
        if action == newLayoutAction:
            self.parent.project.createNewLayout()
        elif action == newLayoutInFolderAction:
            self.parent.project.createNewLayout(selectedLayouts[0].data(0, FOLDER_PATH_ROLE))
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
        layout = self.parent.layout_item.currentLayout()
        if layout:
            self.parent.layout_item.copyToClipboard(layout)


    def exportSelectedLayouts(self, format):
        """Export selected layouts, or all layouts if nothing is selected"""

        if format == "PDF":
            default_extension = '.pdf'
            extension_filter = tr('PDF files') + ' (*.pdf *.PDF)'
            default_filter = extension_filter
        elif format == "IMG":
            default_extension = '.png'
            extension_filter = ';;'.join(tr('{format} format').format(format=fmt.upper()) + f' (*.{fmt} *.{fmt.upper()})'
                                         for fmt in IMAGE_FORMATS)
            default_filter = tr('{format} format').format(format='PNG') + ' (*.png *.PNG)'
        elif format == "SVG":
            default_extension = '.svg'
            extension_filter = tr('{format} format').format(format='SVG') + ' (*.svg *.SVG)'
            default_filter = extension_filter
        else:
            return

        last_used_folder = self.parent.project.getLastUsedFolder()
        selected_items = self.parent.listWidget.selectedItems()
        if selected_items:
            layout_names = self.parent.layout_list.selectedLayoutNames()
        else:
            layout_names = self.parent.layout_list.allLayoutNames()

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
            self.parent.iface.messageBar().pushWarning(tr('Export layout'), tr('Reports cannot be exported from the panel: {names}').format(names=', '.join(skipped)))
        if not layouts:
            return

        # A single layout: ask for a file name
        if len(selected_items) == 1 and not selected_items[0].isFolder():
            file_name = QtWidgets.QFileDialog.getSaveFileName(self.parent, tr('Choose a file name to export the layout'),
                                                              QDir(last_used_folder).filePath(splitName(layouts[0].name())[-1] + default_extension),
                                                              extension_filter, default_filter)[0]
            if file_name == '':
                return
            self.parent.project.setLastExportDir(file_name)
            jobs = [(layouts[0], file_name)]

        # Several layouts: ask for a destination folder, where their folders are
        # recreated below the folder they all share
        else:
            dir_name = QtWidgets.QFileDialog.getExistingDirectory(self.parent, tr('Choose folder to save multiple files'),
                                                                  last_used_folder, QtWidgets.QFileDialog.Option.ShowDirsOnly)
            if dir_name == '':
                return
            self.parent.project.setLastExportDir(dir_name)
            # A selected folder is exported into the destination folder itself
            selected_folders = [splitName(item.data(0, FOLDER_PATH_ROLE)) if item.isFolder()
                                else folderParts(self.parent.layout_list.layoutName(item)) for item in selected_items]
            common_folder = selected_folders[0] if selected_folders else []
            for folder in selected_folders:
                while folder[:len(common_folder)] != common_folder:
                    common_folder = common_folder[:-1]
            jobs = []
            for layout in layouts:
                parts = splitName(layout.name())[len(common_folder):]
                file_name = QDir(dir_name).filePath('/'.join(parts) + default_extension)
                QDir().mkpath(QFileInfo(file_name).absolutePath())
                jobs.append((layout, file_name))

        self.parent.layout_item.exportLayouts(jobs, format)
