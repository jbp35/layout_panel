import re

from qgis.PyQt import QtGui, QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject,QgsUnitTypes

class LayoutList():
    def __init__(self,parent=None):
        """Initialize the layout list"""
        self.parent = parent
        self.layout_list = None
        
        QgsProject.instance().layoutManager().layoutAdded.connect(self.updateLayoutList)
        QgsProject.instance().layoutManager().layoutRemoved.connect(self.updateLayoutList)
        QgsProject.instance().layoutManager().layoutRenamed.connect(self.updateLayoutList)
        
        self.updateLayoutList()
       
        
    def updateLayoutList(self):
        """Generate the list of layouts"""
        self.parent.listWidget.clear()
        layout_manager=self.parent.project.getLayoutManager()
        self.layout_list = layout_manager.layouts()
        search_value = self.parent.mLineEdit.value().replace("*", r"\*").replace("+", r"\+").replace("(", r"\(")\
            .replace(")",r"\)").replace("?", r"\?").replace("[", r"\[").replace("]", r"\]")
        
        for layout in self.layout_list:
            # necessary to ensure that tooltips are updated when layout format or page count changes
            layout.pageCollection().changed.connect(self.updateLayoutList)
            match = bool(re.search(search_value, layout.name(), re.IGNORECASE))
            if match:
                layout = layout_manager.layoutByName(layout.name())
                layout_page_collection = layout.pageCollection()
                page_count = layout_page_collection.pageCount()
                
                #page size
                if layout_page_collection.hasUniformPageSizes():
                    page_size = layout_page_collection.maximumPageSize()
                    units = QgsUnitTypes.encodeUnit(layout.units())
                    page_size_text = f'{page_size.width()}x{page_size.height()} {units}'
                else:
                    page_size_text = 'variable'
                
                # map scale
                reference_map=layout.referenceMap()
                if reference_map:
                    map_scale=f'1:{round(reference_map.scale())}'
                else:
                    map_scale="Unknown"

                item = QtWidgets.QListWidgetItem()
                item.setText(layout.name())
                item.setIcon(QtGui.QIcon(':/plugins/layout_panel/icons/mIconLayout.svg'))
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setToolTip(f'Page Count: {page_count} <br> Page Size: {page_size_text} <br> Map Scale: {map_scale}')
                self.parent.listWidget.addItem(item)
        
        #Disable delete button if there are no layouts in the list
        if len(self.layout_list) == 0:
            self.parent.pbDeleteLayout.setEnabled(False)
        else:
            self.parent.pbDeleteLayout.setEnabled(True)
      
            
    def duplicateSelectedLayouts(self):
        """Duplicate one or multiple selected layouts"""
        selected_items = self.parent.listWidget.selectedItems()
        
        # Copy the list of selected items to avoid race condition due to refresh
        list_layout_names = []  
        for layout_item in selected_items:
            list_layout_names.append(layout_item.text())
        for layout_name in list_layout_names:
            self.parent.layout_item.duplicateLayout(layout_name)


    def removeSelectedLayouts(self, askConfirmation=True):
        """Remove one or multiple selected layouts"""
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
            self.parent.layout_item.removeLayout(layout_name)
    
    