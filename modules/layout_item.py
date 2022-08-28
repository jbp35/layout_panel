import os

from qgis.PyQt import QtGui, QtWidgets, uic, QtXml
from qgis.PyQt.QtCore import pyqtSignal, Qt, QUrl, QDir, QFileInfo, QFileSystemWatcher, QEvent, QSettings
from PyQt5.QtWidgets import QAbstractItemView 
from qgis.core import QgsProject, QgsPrintLayout, QgsLayoutExporter, QgsSettings, QgsReadWriteContext, QgsApplication, QgsUnitTypes, QgsMessageLog
from PyQt5.QtGui import QFontDatabase, QRawFont


class LayoutItem():
    def __init__(self,parent=None):
        """Initialize the layout item"""
        self.parent = parent
        
        # Used to store the initial name of the layout before entering editor mode
        self.name_before_rename = None
        
    def createNewLayout(self):
        """Create a new blank layout"""
        layout_manager= self.parent.project.getLayoutManager()
        
        iterator = 1
        while True:
            if layout_manager.layoutByName('Layout ' + str(iterator)) is None:
                layout_name = "Layout " + str(iterator)
                layout = QgsPrintLayout(self.parent.project.getProjectInstance())
                layout.initializeDefaults()
                layout.setName(layout_name)
                layout_manager.addLayout(layout)
                return
            iterator = iterator + 1

    def createLayoutFromTemplate(self, layout_template_path):
        """Create a new layout based on a template file"""
        project_instance=self.parent.project.getProjectInstance()
        layout_manager= self.parent.project.getLayoutManager()
        document = QtXml.QDomDocument()
        with open(layout_template_path) as file:
            content = file.read()
        document.setContent(content)
        template_name = QFileInfo(layout_template_path).baseName()
        iterator = 1
        while True:
            if layout_manager.layoutByName(template_name + ' ' + str(iterator)) is None :
                layout = QgsPrintLayout(project_instance)
                layout_name = template_name + ' ' + str(iterator)
                layout.loadFromTemplate(document, QgsReadWriteContext())
                layout.setName(layout_name)
                layout_manager.addLayout(layout)
                self.parent.iface.openLayoutDesigner(layout)
                return
            iterator = iterator + 1

        
    def openCurrentLayout(self):
        """Open currently selected layout in editor"""
        layout_manager= self.parent.project.getLayoutManager()
        layout = layout_manager.layoutByName(self.parent.listWidget.selectedItems()[0].text())
        self.parent.iface.openLayoutDesigner(layout)
        

    def duplicateLayout(self):
        """Duplicate one or multiple selected layouts"""
        layout_manager= self.parent.project.getLayoutManager()
        selected_items = self.parent.listWidget.selectedItems()
        list_layout_names = []
        for layoutItem in selected_items:
            list_layout_names.append(layoutItem.text())
        for layoutName in list_layout_names:
            iterator = 1
            while True:
                duplicate_layout_name = layoutName + ' copy ' + str(iterator)
                if layout_manager.layoutByName(duplicate_layout_name) is None:
                    layout = layout_manager.layoutByName(layoutName)
                    layout_manager.duplicateLayout(layout, duplicate_layout_name)
                    return
                iterator = iterator + 1

    def renameLayout(self):
        """Open editor mode to rename currently selected layout"""
        self.name_before_rename = self.parent.listWidget.selectedItems()[0].text()
        self.parent.listWidget.editItem(self.parent.listWidget.selectedItems()[0])

    def renameLayoutClosedEditor(self, QListWidgetItem):
        """Called when editor mode is closed to rename the layout"""
        layout_manager= self.parent.project.getLayoutManager()
        if layout_manager.layoutByName(QListWidgetItem.text()) is None and QListWidgetItem.text() != "":
            if self.name_before_rename != QListWidgetItem.text():
                layout = layout_manager.layoutByName(self.name_before_rename)
                layout.setName(QListWidgetItem.text())
        else:
            if self.name_before_rename != QListWidgetItem.text():
                self.parent.iface.messageBar().pushWarning('Failed to rename layout', ' Entered layout name already exists or is invalid.')
        self.parent.layout_list.updateLayoutWidgetList()
        
        
    def removeSelectedLayouts(self, askConfirmation=True):
        """Remove one or multiple selected layouts"""
        layout_manager= self.parent.project.getLayoutManager()
        selected_items = self.parent.listWidget.selectedItems()
        if askConfirmation:
            qm = QtWidgets.QMessageBox
            if len(selected_items) == 0:
                return
            elif len(selected_items) == 1:
                ret = qm.question(self.parent, 'Remove Selected Layout',
                                f'Are you sure you want to remove permanently "{selected_items[0].text()}" ?', qm.Yes | qm.No)
            else:
                ret = qm.question(self.parent, 'Remove Selected Layouts',
                                f'Are you sure you want to remove permanently {len(selected_items)} layouts?', qm.Yes | qm.No)
        
            if ret == qm.No:
                return
            
        layout_names = []
        for item in selected_items:
            layout_names.append(item.text())
        for layout_name in layout_names:
            layout_manager.removeLayout(layout_manager.layoutByName(layout_name))

    def saveAsTemplate(self):
        """Save selected layout as template"""
        layout_manager= self.parent.project.getLayoutManager()
        selected_items = self.parent.listWidget.selectedItems()
        current_layout = layout_manager.layoutByName(selected_items[0].text())
        file_path = QtWidgets.QFileDialog.getSaveFileName(self.parent, 'Choose a file name to save the layout as template',
                                                      self.template_dir.filePath(current_layout.name() + '.qpt'),
                                                      'Layout templates (*.qpt *.QPT)')[0]
        if file_path != '':
            template=current_layout.saveAsTemplate(file_path, QgsReadWriteContext())
            if template:
                href = f'<a href="{QUrl.fromLocalFile(file_path).toString()}">{QDir.toNativeSeparators(file_path)}</a>'
                self.iface.messageBar().pushSuccess('Save as Template', ' Successfully saved layout template to ' + href)

     
    def exportLayoutPDF(self):
        """Export one or multiple layouts to PDF"""
        default_extension = '.pdf'
        extension_filter = 'PDF files (*.pdf *.PDF)'
        default_filter = 'PDF files (*.pdf *.PDF)'
        
        layout_manager= self.parent.project.getLayoutManager()
        project_instance=self.parent.project.getProjectInstance()
        lastLayoutExportDir = QgsSettings().value('APP/lastLayoutExportDir')
        if lastLayoutExportDir == "":
            lastUsedFolder = QDir(project_instance.homePath())
        else:
            lastUsedFolder = QFileInfo(lastLayoutExportDir).dir()

        layoutList = []
        selectedLayouts = self.parent.listWidget.selectedItems()
        if len(selectedLayouts) == 0: # If nothing is selected, ask for destination folder and export all layouts
            for x in range(self.parent.listWidget.count()):
                layoutList.append(layout_manager.layoutByName(self.parent.listWidget.item(x).text()))
            fname = QtWidgets.QFileDialog.getExistingDirectory(self.parent, 'Choose folder to save multiple files',
                                                               lastUsedFolder.path(),QtWidgets.QFileDialog.ShowDirsOnly)
        elif len(selectedLayouts) == 1:  # If nonly one layout is selected, ask file name and export layout
            layout = (layout_manager.layoutByName(selectedLayouts[0].text()))
            layoutList.append(layout)
            fname = QtWidgets.QFileDialog.getSaveFileName(self.parent, 'Choose a file name to save the layout as PDF',
                                                          lastUsedFolder.filePath(layout.name() + default_extension), extension_filter,default_filter)
            if fname[0] == '': fname = None
        else: # Multiple selection, ask for destination folder and export selected layouts
            for layout in selectedLayouts:
                layoutList.append(layout_manager.layoutByName(layout.text()))
            fname = QtWidgets.QFileDialog.getExistingDirectory(self.parent, 'Choose folder to save multiple files',
                                                               lastUsedFolder.path(),QtWidgets.QFileDialog.ShowDirsOnly)

        if fname:
            QgsSettings().setValue('APP/lastLayoutExportDir', fname[0])
            for layout in layoutList:
                export = QgsLayoutExporter(layout)
                if len(selectedLayouts) == 1: fileName = fname[0]
                else: fileName = QDir(fname).filePath(layout.name() + default_extension)
                export.exportToPdf(fileName, QgsLayoutExporter.PdfExportSettings())
                href = f'<a href="{QUrl.fromLocalFile(fileName).toString()}">{QDir.toNativeSeparators(fileName)}</a>'
                self.parent.iface.messageBar().pushSuccess('Export layout',' Successfully exported layout to ' + href)

    def exportLayoutImage(self):
        """Export one or multiple layouts to image"""
        default_extension = '.png'
        extension_filter = 'PNG format (*.png *.PNG);;BMP format (*.bmp *.BMP);;CUR format (*.cur *.CUR);;ICNS format (*.icns *.ICNS);;ICO format (*.ico *.ICO)' \
                           'JPEG format (*.jpeg *.JPEG);;JPG format (*.jpg *.JPG);;PBM format (*.pbm *.PBM);;PGM format (*.pgm *.PGM);;PPM format (*.ppm *.PPM)' \
                           'TIF format (*.tif *.TIF);;TIFF format (*.tiff *.TIFF);;WBMP format (*.wbmp *.WBMP);;WEBP format (*.webp *.WEBP);;WBM format (*.wbm *.XBM);;XPM format (*.xpm *.XPM)'
        default_filter = 'PNG format (*.png *.PNG)'
        
        layout_manager= self.parent.project.getLayoutManager()
        project_instance=self.parent.project.getProjectInstance()
        lastLayoutExportDir = QgsSettings().value('APP/lastLayoutExportDir')
        if lastLayoutExportDir == "":
            lastUsedFolder = QDir(project_instance.homePath())
        else:
            lastUsedFolder = QFileInfo(lastLayoutExportDir).dir()

        layoutList = []
        selectedLayouts = self.parent.listWidget.selectedItems()
        if len(selectedLayouts) == 0: # If nothing is selected, ask for destination folder and export all layouts
            for x in range(self.parent.listWidget.count()):
                layoutList.append(layout_manager.layoutByName(self.listWidget.item(x).text()))
            fname = QtWidgets.QFileDialog.getExistingDirectory(self.parent, 'Choose folder to save multiple files',
                                                               lastUsedFolder.path(),QtWidgets.QFileDialog.ShowDirsOnly)
        elif len(selectedLayouts) == 1:  # If nonly one layout is selected, ask file name and export layout
            layout = (layout_manager.layoutByName(selectedLayouts[0].text()))
            layoutList.append(layout)
            fname = QtWidgets.QFileDialog.getSaveFileName(self.parent, 'Choose a file name to save the layout as image',
                                                          lastUsedFolder.filePath(layout.name() + default_extension), extension_filter,default_filter)
            if fname[0] == '': fname = None
        else: # Multiple selection, ask for destination folder and export selected layouts
            for layout in selectedLayouts:
                layoutList.append(layout_manager.layoutByName(layout.text()))
            fname = QtWidgets.QFileDialog.getExistingDirectory(self.parent, 'Choose folder to save multiple files',
                                                               lastUsedFolder.path(),QtWidgets.QFileDialog.ShowDirsOnly)

        if fname:
            QgsSettings().setValue('APP/lastLayoutExportDir', fname[0])
            for layout in layoutList:
                export = QgsLayoutExporter(layout)
                if len(selectedLayouts) == 1: fileName = fname[0]
                else: fileName = QDir(fname).filePath(layout.name() + default_extension)
                export.exportToImage(fileName, QgsLayoutExporter.ImageExportSettings())
                href = f'<a href="{QUrl.fromLocalFile(fileName).toString()}">{QDir.toNativeSeparators(fileName)}</a>'
                self.parent.iface.messageBar().pushSuccess('Export layout', ' Successfully exported layout to ' + href)

    def exportLayoutSvg(self):
        """Export one or multiple layouts to SVG"""
        default_extension = '.svg'
        extension_filter = 'SVG format (*.svg *.SVG)'
        default_filter = 'SVG format (*.svg *.SVG)'

        layout_manager= self.parent.project.getLayoutManager()
        project_instance=self.parent.project.getProjectInstance()
        lastLayoutExportDir=QgsSettings().value('APP/lastLayoutExportDir')
        if lastLayoutExportDir=="":
            lastUsedFolder = QDir(project_instance.homePath())
        else:
            lastUsedFolder = QFileInfo(lastLayoutExportDir).dir()

        layoutList = []
        selectedLayouts = self.parent.listWidget.selectedItems()
        if len(selectedLayouts) == 0: # If nothing is selected, ask for destination folder and export all layouts
            for x in range(self.listWidget.count()):
                layoutList.append(layout_manager.layoutByName(self.listWidget.item(x).text()))
            fname = QtWidgets.QFileDialog.getExistingDirectory(self.parent, 'Choose folder to save multiple files',
                                                               lastUsedFolder.path(),QtWidgets.QFileDialog.ShowDirsOnly)
        elif len(selectedLayouts) == 1:  # If only one layout is selected, ask file name and export layout
            layout = (layout_manager.layoutByName(selectedLayouts[0].text()))
            layoutList.append(layout)
            fname = QtWidgets.QFileDialog.getSaveFileName(self.parent, 'Choose a file name to save the layout as SVG',
                                                          lastUsedFolder.filePath(layout.name() + default_extension), extension_filter, default_filter)
            if fname[0] == '': fname = None
        else: # Multiple selection, ask for destination folder and export selected layouts
            for layout in selectedLayouts:
                layoutList.append(layout_manager.layoutByName(layout.text()))
            fname = QtWidgets.QFileDialog.getExistingDirectory(self.parent, 'Choose folder to save multiple files',
                                                               lastUsedFolder.path(),QtWidgets.QFileDialog.ShowDirsOnly)

        if fname:
            QgsSettings().setValue('APP/lastLayoutExportDir', fname[0])
            for layout in layoutList:
                export = QgsLayoutExporter(layout)
                if len(selectedLayouts) == 1: fileName = fname[0]
                else: fileName = QDir(fname).filePath(layout.name() + default_extension)
                export.exportToSvg(fileName, QgsLayoutExporter.SvgExportSettings())
                href = f'<a href="{QUrl.fromLocalFile(fileName).toString()}">{QDir.toNativeSeparators(fileName)}</a>'
                self.parent.iface.messageBar().pushSuccess('Export layout',' Successfully exported layout to ' + href)