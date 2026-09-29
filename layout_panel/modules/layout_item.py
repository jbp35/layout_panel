from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt, QUrl, QDir, QFileInfo
from qgis.core import QgsLayoutExporter, QgsReadWriteContext
from .i18n import tr

class LayoutItem():
    def __init__(self,parent=None):
        """Initialize the layout item"""
        self.parent = parent
        
        # Used to store the initial name of the layout before entering editor mode
        self.name_before_rename = None


    def layoutByName(self, layout_name):
        """Return the layout (print layout or report) with this name"""
        return self.parent.project.getLayoutManager().layoutByName(layout_name)
        
    def currentLayout(self):
        """Return the first selected layout, or None if nothing is selected"""
        selected_items = self.parent.listWidget.selectedItems()
        if not selected_items:
            return None
        return self.layoutByName(selected_items[0].text())

    def openCurrentLayout(self):
        """Open currently selected layout in editor"""
        layout = self.currentLayout()
        if layout:
            self.parent.iface.openLayoutDesigner(layout)
    
    def duplicateLayout(self, layout_name):
        """Duplicate the layout"""
        layout_manager= self.parent.project.getLayoutManager()
        
        iterator = 1
        while True:
            duplicate_layout_name = tr('{name} copy {number}').format(name=layout_name, number=iterator)
            if layout_manager.layoutByName(duplicate_layout_name) is None:
                layout = layout_manager.layoutByName(layout_name)
                layout_manager.duplicateLayout(layout, duplicate_layout_name)
                return
            iterator = iterator + 1
          

    def renameLayout(self):
        """Open editor mode to rename currently selected layout"""
        selected_items = self.parent.listWidget.selectedItems()
        if not selected_items:
            return
        self.name_before_rename = selected_items[0].text()
        self.parent.listWidget.editItem(selected_items[0])


    def renameLayoutClosedEditor(self, editor):
        """Called when editor mode is closed to rename the layout"""
        old_name = self.name_before_rename
        self.name_before_rename = None
        new_name = editor.text().strip()
        if old_name is None or new_name == old_name:
            return

        layout = self.layoutByName(old_name)
        if layout and new_name and self.layoutByName(new_name) is None:
            layout.setName(new_name)
        else:
            self.parent.iface.messageBar().pushWarning(tr('Failed to rename layout'), ' ' + tr('Entered layout name already exists or is invalid.'))
        self.parent.layout_list.updateLayoutList()
       
        
    def removeLayout(self, layout_name):
        """Remove the layout"""
        layout = self.layoutByName(layout_name)
        if layout:
            self.parent.project.getLayoutManager().removeLayout(layout)
        
        
    def saveAsTemplate(self):
        """Save selected layout as template"""
        current_layout = self.currentLayout()
        if current_layout is None:
            return
        template_dir = QDir(self.parent.project.getDefaultTemplateFolderPath())
        file_path = QtWidgets.QFileDialog.getSaveFileName(self.parent, tr('Choose a file name to save the layout as template'),
                                                      template_dir.filePath(current_layout.name() + '.qpt'),
                                                      tr('Layout templates') + ' (*.qpt *.QPT)')[0]
        if file_path != '':
            template=current_layout.saveAsTemplate(file_path, QgsReadWriteContext())
            if template:
                href = f'<a href="{QUrl.fromLocalFile(file_path).toString()}">{QDir.toNativeSeparators(file_path)}</a>'
                self.parent.iface.messageBar().pushSuccess(tr('Save as Template'), ' ' + tr('Successfully saved layout template to {path}').format(path=href))

       
    def exportLayouts(self, jobs, format):
        """Export layouts to files.

        Export runs on the main thread: rendering a layout from a background
        task is not thread-safe and crashes QGIS (issues #3 and #4).

        :param jobs: list of (layout, file_name) tuples
        :param format: "PDF", "IMG" or "SVG"
        """
        progress = QtWidgets.QProgressDialog(tr('Exporting layouts...'), tr('Cancel'), 0, len(jobs), self.parent)
        progress.setWindowTitle(tr('Export layout'))
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(500)

        exported = []
        errors = []
        for index, (layout, file_name) in enumerate(jobs):
            if progress.wasCanceled():
                break
            progress.setLabelText(tr('Exporting "{name}"...').format(name=layout.name()))
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
                errors.append(f'"{layout.name()}": {exporter.errorMessage() or getattr(result, "name", result)}')
        progress.setValue(len(jobs))

        message_bar = self.parent.iface.messageBar()
        if errors:
            message_bar.pushCritical(tr('Export layout'), tr('Failed to export {errors}').format(errors='; '.join(errors)))
        if len(exported) == 1:
            href = f'<a href="{QUrl.fromLocalFile(exported[0]).toString()}">{QDir.toNativeSeparators(exported[0])}</a>'
            message_bar.pushSuccess(tr('Export layout'), ' ' + tr('Successfully exported layout to {path}').format(path=href))
        elif exported:
            folder = QFileInfo(exported[0]).absolutePath()
            href = f'<a href="{QUrl.fromLocalFile(folder).toString()}">{QDir.toNativeSeparators(folder)}</a>'
            message_bar.pushSuccess(tr('Export layout'), ' ' + tr('Successfully exported {count} layouts to {path}').format(
                count=len(exported), path=href))


    def copyToClipboard(self, layout):
        """Copy the first page of the layout to the clipboard as an image"""
        image = QgsLayoutExporter(layout).renderPageToImage(0)
        if image.isNull():
            self.parent.iface.messageBar().pushWarning(tr('Copy layout'), ' ' + tr('Failed to copy "{name}" to clipboard').format(name=layout.name()))
            return
        QtWidgets.QApplication.clipboard().setImage(image)
        self.parent.iface.messageBar().pushSuccess(tr('Copy layout'), ' ' + tr('Successfully copied "{name}" to clipboard').format(name=layout.name()))
