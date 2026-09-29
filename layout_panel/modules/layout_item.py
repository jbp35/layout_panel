from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt, QUrl, QDir, QFileInfo
from qgis.core import QgsLayoutExporter, QgsReadWriteContext, QgsApplication

class LayoutItem():
    def __init__(self,parent=None):
        """Initialize the layout item"""
        self.parent = parent
        
        # Used to store the initial name of the layout before entering editor mode
        self.name_before_rename = None


    def layoutByName(self, layout_name):
        """Return the layout (print layout or report) with this name"""
        return self.parent.project.getLayoutManager().layoutByName(layout_name)
        
    def openCurrentLayout(self):
        """Open currently selected layout in editor"""
        layout_manager= self.parent.project.getLayoutManager()
        layout = layout_manager.layoutByName(self.parent.listWidget.selectedItems()[0].text())
        self.parent.iface.openLayoutDesigner(layout)
    
    def duplicateLayout(self, layout_name):
        """Duplicate the layout"""
        layout_manager= self.parent.project.getLayoutManager()
        
        iterator = 1
        while True:
            duplicate_layout_name = layout_name + ' copy ' + str(iterator)
            if layout_manager.layoutByName(duplicate_layout_name) is None:
                layout = layout_manager.layoutByName(layout_name)
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
        self.parent.layout_list.updateLayoutList()
       
        
    def removeLayout(self, layout_name):
        """Remove the layout"""
        layout_manager= self.parent.project.getLayoutManager()
        layout_manager.removeLayout(layout_manager.layoutByName(layout_name))
        
        
    def saveAsTemplate(self):
        """Save selected layout as template"""
        layout_manager= self.parent.project.getLayoutManager()
        selected_items = self.parent.listWidget.selectedItems()
        template_dir = QDir(QgsApplication.qgisSettingsDirPath() + '/composer_templates')

        current_layout = layout_manager.layoutByName(selected_items[0].text())
        file_path = QtWidgets.QFileDialog.getSaveFileName(self.parent, 'Choose a file name to save the layout as template',
                                                      template_dir.filePath(current_layout.name() + '.qpt'),
                                                      'Layout templates (*.qpt *.QPT)')[0]
        if file_path != '':
            template=current_layout.saveAsTemplate(file_path, QgsReadWriteContext())
            if template:
                href = f'<a href="{QUrl.fromLocalFile(file_path).toString()}">{QDir.toNativeSeparators(file_path)}</a>'
                self.iface.messageBar().pushSuccess('Save as Template', ' Successfully saved layout template to ' + href)

       
    def exportLayouts(self, jobs, format):
        """Export layouts to files.

        Export runs on the main thread: rendering a layout from a background
        task is not thread-safe and crashes QGIS (issues #3 and #4).

        :param jobs: list of (layout, file_name) tuples
        :param format: "PDF", "IMG" or "SVG"
        """
        progress = QtWidgets.QProgressDialog('Exporting layouts...', 'Cancel', 0, len(jobs), self.parent)
        progress.setWindowTitle('Export layout')
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(500)

        exported = []
        errors = []
        for index, (layout, file_name) in enumerate(jobs):
            if progress.wasCanceled():
                break
            progress.setLabelText(f'Exporting "{layout.name()}"...')
            progress.setValue(index)

            exporter = QgsLayoutExporter(layout)
            if format == "PDF":
                result = exporter.exportToPdf(file_name, QgsLayoutExporter.PdfExportSettings())
            elif format == "IMG":
                result = exporter.exportToImage(file_name, QgsLayoutExporter.ImageExportSettings())
            else:
                result = exporter.exportToSvg(file_name, QgsLayoutExporter.SvgExportSettings())

            if result == QgsLayoutExporter.ExportResult.Success:
                exported.append(file_name)
            else:
                errors.append(f'"{layout.name()}": {exporter.errorMessage() or result.name}')
        progress.setValue(len(jobs))

        message_bar = self.parent.iface.messageBar()
        if errors:
            message_bar.pushCritical('Export layout', 'Failed to export ' + '; '.join(errors))
        if len(exported) == 1:
            href = f'<a href="{QUrl.fromLocalFile(exported[0]).toString()}">{QDir.toNativeSeparators(exported[0])}</a>'
            message_bar.pushSuccess('Export layout', ' Successfully exported layout to ' + href)
        elif exported:
            folder = QFileInfo(exported[0]).absolutePath()
            href = f'<a href="{QUrl.fromLocalFile(folder).toString()}">{QDir.toNativeSeparators(folder)}</a>'
            message_bar.pushSuccess('Export layout', f' Successfully exported {len(exported)} layouts to ' + href)


    def copyToClipboard(self, layout):
        """Copy the first page of the layout to the clipboard as an image"""
        image = QgsLayoutExporter(layout).renderPageToImage(0)
        if image.isNull():
            self.parent.iface.messageBar().pushWarning('Copy layout', f' Failed to copy "{layout.name()}" to clipboard')
            return
        QtWidgets.QApplication.clipboard().setImage(image)
        self.parent.iface.messageBar().pushSuccess('Copy layout', f' Successfully copied "{layout.name()}" to clipboard')
