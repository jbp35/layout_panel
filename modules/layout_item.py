from qgis.PyQt import QtWidgets, QtXml
from qgis.PyQt.QtCore import  QUrl, QDir, QFileInfo
from qgis.core import QgsPrintLayout, QgsLayoutExporter,  QgsReadWriteContext, QgsApplication

class LayoutItem():
    def __init__(self,parent=None):
        """Initialize the layout item"""
        self.parent = parent
        
        # Used to store the initial name of the layout before entering editor mode
        self.name_before_rename = None
        
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

       
    def exportLayout(self,task,layout, file_name, format):
        """Export the layout"""
        export = QgsLayoutExporter(layout)
        if format == "PDF":
            export.exportToPdf(file_name, QgsLayoutExporter.PdfExportSettings())
        elif format == "IMG":
            export.exportToImage(file_name, QgsLayoutExporter.ImageExportSettings())
        elif format == "SVG":
            export.exportToSvg(file_name, QgsLayoutExporter.SvgExportSettings())
        return file_name
    
     
    def exportLayoutCompleted(self,exception,result=None):
        """Called when export background task is complete"""
        if not exception:
            href = f'<a href="{QUrl.fromLocalFile(result).toString()}">{QDir.toNativeSeparators(result)}</a>'
            self.parent.iface.messageBar().pushSuccess('Export layout',' Successfully exported layout to ' + href)
          
            
    def copyToClipboard(self,task,layout):
        """Export selected layout to image"""
        export = QgsLayoutExporter(layout)
        image = export.renderPageToImage(0)
        return layout.name(), image
        
    def copyToClipboardCompleted(self,exception,result=None):
        """Copy the image to the clipboard"""
        if not exception:
            self.parent.iface.messageBar().pushSuccess('Copy layout',f' Successfully copied layout "{result[0]}" to clipboard')
            app = QtWidgets.QApplication.instance()
            clipboard = app.clipboard()
            clipboard.setImage(result[1])
